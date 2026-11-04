from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Response, status

from dependencies import CurrentUser, DatabaseSession
from schemas.navigation import (
    NavigationStateResponse,
    NavigationStopResponse,
    NavigationTrailResponse,
    TrailEntryResponse,
    VisitRequest,
)
from services.buildings import get_building_or_404
from services.navigation_history import (
    NavigationTrail,
    NavStop,
    navigation_histories,
)

router = APIRouter(prefix="/navigation", tags=["navigation"])


def to_stop_response(stop: Optional[NavStop]) -> Optional[NavigationStopResponse]:
    if stop is None:
        return None
    return NavigationStopResponse(
        building_id=stop.building_id, building_name=stop.building_name, floor=stop.floor
    )


def to_state(trail: NavigationTrail) -> NavigationStateResponse:
    return NavigationStateResponse(
        current=to_stop_response(trail.current),
        can_go_back=trail.can_go_back,
        can_go_forward=trail.can_go_forward,
    )


def nothing_to(direction: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail=f"There is nothing to go {direction} to."
    )


@router.get("", response_model=NavigationTrailResponse)
def read_trail(current_user: CurrentUser) -> NavigationTrailResponse:
    trail = navigation_histories.get(current_user.username)
    state = to_state(trail)
    return NavigationTrailResponse(
        **state.model_dump(),
        trail=[
            TrailEntryResponse(**to_stop_response(stop).model_dump(), is_current=is_current)
            for stop, is_current in trail.entries()
        ],
    )


@router.post("/visit", response_model=NavigationStateResponse)
def visit_place(
    visit: VisitRequest, database_session: DatabaseSession, current_user: CurrentUser
) -> NavigationStateResponse:
    building = get_building_or_404(database_session, visit.building_id)
    stop = NavStop(building.id, building.name, building.floor)
    return to_state(navigation_histories.visit(current_user.username, stop))


@router.post("/back", response_model=NavigationStateResponse)
def go_back(current_user: CurrentUser) -> NavigationStateResponse:
    trail = navigation_histories.go_back(current_user.username)
    if trail is None:
        raise nothing_to("back")
    return to_state(trail)


@router.post("/forward", response_model=NavigationStateResponse)
def go_forward(current_user: CurrentUser) -> NavigationStateResponse:
    trail = navigation_histories.go_forward(current_user.username)
    if trail is None:
        raise nothing_to("forward")
    return to_state(trail)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_trail(current_user: CurrentUser) -> Response:
    navigation_histories.clear(current_user.username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
