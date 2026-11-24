from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import delete, select

from config import POPULAR_ROUTES_LIMIT
from dependencies import AdminUser, CurrentUser, DatabaseSession
from models import BlockedPathReport, Building, CampusPath, RouteFeedback, RouteObservation, RouteVisit
from schemas.paths import PathKind
from schemas.routes import (
    AlgorithmResult,
    BlockedPathRequest,
    BlockedPathStatus,
    FeedbackReason,
    LearnedPath,
    MultiStopRequest,
    MultiStopResponse,
    PathAlgorithm,
    PopularRouteResponse,
    RouteAlternative,
    RouteComparisonResponse,
    RouteFeedbackRequest,
    RouteLeg,
    RouteLearningResponse,
    RouteMode,
    RouteOutcomeRequest,
    RoutePreferencesResponse,
    RouteRequest,
    RouteResponse,
)
from services import route_learning
from services.buildings import get_building_or_404
from services.campus_graph import campus_graph_service
from services.popular_routes import rank_popular_routes
from services.routing import compute_path, resolve_endpoints

router = APIRouter(prefix="/routes", tags=["routes"])

ALTERNATIVES: tuple[tuple[str, str, RouteMode, tuple[PathKind, ...]], ...] = (
    ("comfortable", "Más cómoda", RouteMode.COMFORTABLE, ()),
    ("shortest", "Más corta", RouteMode.SHORTEST, ()),
    ("no_stairs", "Sin escaleras", RouteMode.COMFORTABLE, (PathKind.STAIRS,)),
)


def build_route_response(path: list[str], distance: float, origin: Building, destination: Building,
                         mode: RouteMode, observation_id: int | None = None) -> RouteResponse:
    return RouteResponse(
        path=campus_graph_service.names(path),
        waypoints=campus_graph_service.waypoints(path),
        steps=campus_graph_service.describe_steps(path),
        distance=distance,
        origin_name=origin.name,
        destination_name=destination.name,
        mode=mode,
        estimated_seconds=campus_graph_service.estimate_seconds(path),
        observation_id=observation_id,
    )


@router.post("/calculate", response_model=RouteResponse)
def calculate_route(
    route_request: RouteRequest,
    database_session: DatabaseSession,
    current_user: CurrentUser,
) -> RouteResponse:
    origin, destination = resolve_endpoints(
        database_session, route_request.origin_id, route_request.destination_id
    )
    path, distance = compute_path(
        origin, destination, route_request.algorithm, route_request.avoid, route_request.mode
    )

    visit = RouteVisit(
        user_id=current_user.id,
        origin_id=origin.id,
        destination_id=destination.id,
        distance=distance,
    )
    database_session.add(visit)
    database_session.flush()
    # The exact connections are kept with the history entry (and deleted with it) so routing can learn.
    observation = RouteObservation(
        user_id=current_user.id,
        route_visit_id=visit.id,
        origin_id=origin.id,
        destination_id=destination.id,
        mode=route_request.mode.value,
        avoid=",".join(sorted(kind.value for kind in route_request.avoid)),
        path_ids=json.dumps(campus_graph_service.path_ids(path)),
        distance=distance,
    )
    database_session.add(observation)
    database_session.commit()

    return build_route_response(path, distance, origin, destination, route_request.mode, observation.id)


@router.post("/alternatives", response_model=list[RouteAlternative])
def route_alternatives(route_request: RouteRequest, database_session: DatabaseSession) -> list[RouteAlternative]:
    """Up to three different routes (comfortable, shortest, without stairs), summarised; nothing is recorded."""
    origin, destination = resolve_endpoints(
        database_session, route_request.origin_id, route_request.destination_id
    )
    results: list[RouteAlternative] = []
    seen: set[tuple[str, ...]] = set()
    for key, label, mode, avoid in ALTERNATIVES:
        try:
            path, distance = compute_path(origin, destination, route_request.algorithm, list(avoid), mode)
        except HTTPException as error:
            if error.status_code == status.HTTP_404_NOT_FOUND:
                continue
            raise
        if tuple(path) in seen:
            continue
        seen.add(tuple(path))
        kinds = campus_graph_service.path_kinds(path)
        results.append(RouteAlternative(
            key=key, label=label, mode=mode, avoid=list(avoid), distance=distance,
            estimated_seconds=campus_graph_service.estimate_seconds(path), steps=len(path) - 1,
            uses_stairs=PathKind.STAIRS.value in kinds, uses_elevator=PathKind.ELEVATOR.value in kinds,
        ))
    return results


@router.post("/compare", response_model=RouteComparisonResponse)
def compare_algorithms(
    route_request: RouteRequest, database_session: DatabaseSession
) -> RouteComparisonResponse:
    origin, destination = resolve_endpoints(
        database_session, route_request.origin_id, route_request.destination_id
    )
    results: list[AlgorithmResult] = []
    for algorithm in PathAlgorithm:
        path, distance = compute_path(origin, destination, algorithm, route_request.avoid, route_request.mode)
        results.append(AlgorithmResult(algorithm=algorithm, path=campus_graph_service.names(path),
            waypoints=campus_graph_service.waypoints(path), distance=distance))

    return RouteComparisonResponse(
        origin_name=origin.name, destination_name=destination.name, results=results
    )


@router.post("/multi-stop", response_model=MultiStopResponse)
def calculate_multi_stop_route(
    request: MultiStopRequest, database_session: DatabaseSession
) -> MultiStopResponse:
    buildings = [get_building_or_404(database_session, id_) for id_ in request.building_ids]

    legs: list[RouteLeg] = []
    for origin, destination in zip(buildings, buildings[1:]):
        path, distance = compute_path(origin, destination, request.algorithm, request.avoid, request.mode)
        legs.append(
            RouteLeg(
                origin_name=origin.name,
                destination_name=destination.name,
                path=campus_graph_service.names(path),
                waypoints=campus_graph_service.waypoints(path),
                steps=campus_graph_service.describe_steps(path),
                distance=distance,
            )
        )
    return MultiStopResponse(legs=legs, total_distance=sum(leg.distance for leg in legs))


@router.get("/popular", response_model=list[PopularRouteResponse])
def list_popular_routes(database_session: DatabaseSession) -> list[PopularRouteResponse]:
    return rank_popular_routes(database_session, POPULAR_ROUTES_LIMIT)


def own_observation(database_session: DatabaseSession, user_id: int, observation_id: int) -> RouteObservation:
    observation = database_session.get(RouteObservation, observation_id)
    if observation is None or observation.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Route {observation_id} not found.")
    return observation


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def send_route_feedback(
    request: RouteFeedbackRequest, database_session: DatabaseSession, current_user: CurrentUser
) -> dict[str, bool]:
    if request.rating not in (1, -1):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rating must be 1 or -1.")
    observation = own_observation(database_session, current_user.id, request.observation_id)
    path_ids: list[int] = json.loads(observation.path_ids)
    path_id = path_ids[request.step_index] if request.step_index is not None and request.step_index < len(path_ids) else None
    database_session.add(RouteFeedback(
        observation_id=observation.id, user_id=current_user.id, rating=request.rating,
        reason=request.reason.value if request.reason else None, path_id=path_id,
    ))
    blocked = request.reason is FeedbackReason.CLOSED and path_id is not None
    if blocked:
        database_session.add(BlockedPathReport(path_id=path_id, user_id=current_user.id, reason="closed"))
    database_session.commit()
    route_learning.refresh(database_session)
    return {"recorded": True, "blocked_reported": blocked}


@router.post("/observations/{observation_id}/outcome", status_code=status.HTTP_204_NO_CONTENT)
def record_route_outcome(
    observation_id: int, request: RouteOutcomeRequest, database_session: DatabaseSession, current_user: CurrentUser
) -> Response:
    observation = own_observation(database_session, current_user.id, observation_id)
    observation.outcome = request.outcome.value
    database_session.commit()
    route_learning.refresh(database_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/blocked", status_code=status.HTTP_201_CREATED)
def report_blocked_path(
    request: BlockedPathRequest, database_session: DatabaseSession, current_user: CurrentUser
) -> dict[str, bool]:
    if database_session.get(CampusPath, request.path_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Path {request.path_id} not found.")
    database_session.add(BlockedPathReport(path_id=request.path_id, user_id=current_user.id, reason=request.reason))
    database_session.commit()
    route_learning.refresh(database_session)
    return {"recorded": True, "active": request.path_id in route_learning.active_blocks(database_session)}


@router.get("/preferences", response_model=RoutePreferencesResponse)
def read_route_preferences(database_session: DatabaseSession, current_user: CurrentUser) -> RoutePreferencesResponse:
    """Suggests (never switches on) avoiding stairs when the person did so in most recent routes."""
    recent = list(database_session.scalars(
        select(RouteObservation).where(RouteObservation.user_id == current_user.id)
        .order_by(RouteObservation.created_at.desc(), RouteObservation.id.desc()).limit(5)))
    avoiding = sum(1 for observation in recent if PathKind.STAIRS.value in observation.avoid.split(","))
    return RoutePreferencesResponse(
        suggest_avoid_stairs=len(recent) >= 3 and avoiding / len(recent) >= 0.6,
        recent_avoid_stairs=avoiding, recent_routes=len(recent),
    )


@router.get("/learning", response_model=RouteLearningResponse)
def read_route_learning(database_session: DatabaseSession, _admin: AdminUser) -> RouteLearningResponse:
    observations, feedback, outcomes = route_learning.counts(database_session)
    learned: list[LearnedPath] = []
    for path_id, (bad, good) in route_learning.evidence(database_session).items():
        value = route_learning.multiplier(bad, good)
        ends = campus_graph_service.path_endpoints(path_id)
        if value != 1.0 and ends:
            learned.append(LearnedPath(path_id=path_id, origin_name=ends[0], destination_name=ends[1],
                kind=PathKind(ends[2]), multiplier=round(value, 3), evidence=round(bad + good, 2)))
    learned.sort(key=lambda item: abs(item.multiplier - 1.0), reverse=True)
    blocked: list[BlockedPathStatus] = []
    at = route_learning.now_utc()
    for path_id, (reports, confirmed, until) in route_learning.block_states(database_session, at).items():
        ends = campus_graph_service.path_endpoints(path_id) or ("?", "?", PathKind.CORRIDOR.value)
        blocked.append(BlockedPathStatus(path_id=path_id, origin_name=ends[0], destination_name=ends[1], reports=reports,
            confirmed=confirmed, active=bool(until and until > at), expires_at=until))
    return RouteLearningResponse(observations=observations, feedback=feedback, outcomes=outcomes,
        learned_paths=learned[:30], blocked_paths=blocked, parameters=route_learning.parameters())


@router.post("/blocked/{path_id}/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_blocked_path(path_id: int, database_session: DatabaseSession, admin: AdminUser) -> Response:
    if database_session.get(CampusPath, path_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Path {path_id} not found.")
    database_session.add(BlockedPathReport(path_id=path_id, user_id=admin.id, reason="confirmed", confirmed=True))
    database_session.commit()
    route_learning.refresh(database_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/blocked/{path_id}", status_code=status.HTTP_204_NO_CONTENT)
def clear_blocked_path(path_id: int, database_session: DatabaseSession, _admin: AdminUser) -> Response:
    database_session.execute(delete(BlockedPathReport).where(BlockedPathReport.path_id == path_id))
    database_session.commit()
    route_learning.refresh(database_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
