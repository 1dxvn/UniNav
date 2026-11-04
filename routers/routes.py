from __future__ import annotations

from fastapi import APIRouter

from config import POPULAR_ROUTES_LIMIT
from dependencies import CurrentUser, DatabaseSession
from models import RouteVisit
from schemas.routes import (
    AlgorithmResult,
    MultiStopRequest,
    MultiStopResponse,
    PathAlgorithm,
    PopularRouteResponse,
    RouteComparisonResponse,
    RouteLeg,
    RouteRequest,
    RouteResponse,
)
from services.buildings import get_building_or_404
from services.popular_routes import rank_popular_routes
from services.routing import compute_path, resolve_endpoints

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/calculate", response_model=RouteResponse)
def calculate_route(
    route_request: RouteRequest,
    database_session: DatabaseSession,
    current_user: CurrentUser,
) -> RouteResponse:
    origin, destination = resolve_endpoints(
        database_session, route_request.origin_id, route_request.destination_id
    )
    path, distance = compute_path(origin, destination, route_request.algorithm)

    database_session.add(
        RouteVisit(
            user_id=current_user.id,
            origin_id=origin.id,
            destination_id=destination.id,
            distance=distance,
        )
    )
    database_session.commit()

    return RouteResponse(
        path=path, distance=distance, origin_name=origin.name, destination_name=destination.name
    )


@router.post("/compare", response_model=RouteComparisonResponse)
def compare_algorithms(
    route_request: RouteRequest, database_session: DatabaseSession
) -> RouteComparisonResponse:
    origin, destination = resolve_endpoints(
        database_session, route_request.origin_id, route_request.destination_id
    )
    results: list[AlgorithmResult] = []
    for algorithm in PathAlgorithm:
        path, distance = compute_path(origin, destination, algorithm)
        results.append(AlgorithmResult(algorithm=algorithm, path=path, distance=distance))

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
        path, distance = compute_path(origin, destination, request.algorithm)
        legs.append(
            RouteLeg(
                origin_name=origin.name,
                destination_name=destination.name,
                path=path,
                distance=distance,
            )
        )
    return MultiStopResponse(legs=legs, total_distance=sum(leg.distance for leg in legs))


@router.get("/popular", response_model=list[PopularRouteResponse])
def list_popular_routes(database_session: DatabaseSession) -> list[PopularRouteResponse]:
    return rank_popular_routes(database_session, POPULAR_ROUTES_LIMIT)
