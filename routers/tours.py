from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from dependencies import AdminUser, CurrentUser, DatabaseSession
from models import Building, Tour, TourStop
from schemas.tours import (
    TourCreate,
    TourResponse,
    TourSessionResponse,
    TourSummaryResponse,
)
from services.tour_sessions import TourSession, tour_sessions
from services.tours import (
    get_tour_or_404,
    session_stops,
    to_session_response,
    to_tour_response,
    to_tour_summary,
)

router = APIRouter(prefix="/tours", tags=["tours"])


def require_session(username: str) -> TourSession:
    session = tour_sessions.get(username)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have no active tour. Start one with POST /tours/{id}/start.",
        )
    return session


@router.get("", response_model=list[TourSummaryResponse])
def list_tours(database_session: DatabaseSession) -> list[TourSummaryResponse]:
    tours = database_session.scalars(
        select(Tour).options(selectinload(Tour.stops)).order_by(Tour.name)
    )
    return [to_tour_summary(tour) for tour in tours]


@router.post("", response_model=TourResponse, status_code=status.HTTP_201_CREATED)
def create_tour(
    tour_data: TourCreate, database_session: DatabaseSession, _admin_user: AdminUser
) -> TourResponse:
    if len(set(tour_data.building_ids)) != len(tour_data.building_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A tour cannot visit the same place twice.",
        )
    found = set(
        database_session.scalars(select(Building.id).where(Building.id.in_(tour_data.building_ids)))
    )
    missing = [building_id for building_id in tour_data.building_ids if building_id not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Buildings not found: {', '.join(map(str, missing))}.",
        )
    if database_session.scalar(select(Tour.id).where(Tour.name == tour_data.name)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Tour '{tour_data.name}' already exists."
        )

    tour = Tour(
        name=tour_data.name,
        description=tour_data.description,
        stops=[
            TourStop(building_id=building_id, position=index)
            for index, building_id in enumerate(tour_data.building_ids, start=1)
        ],
    )
    database_session.add(tour)
    database_session.commit()
    return to_tour_response(get_tour_or_404(database_session, tour.id))


@router.get("/session", response_model=TourSessionResponse)
def read_current_stop(current_user: CurrentUser) -> TourSessionResponse:
    return to_session_response(require_session(current_user.username))


@router.post("/session/next", response_model=TourSessionResponse)
def go_to_next_stop(current_user: CurrentUser) -> TourSessionResponse:
    require_session(current_user.username)
    return to_session_response(tour_sessions.advance(current_user.username))


@router.post("/session/previous", response_model=TourSessionResponse)
def go_to_previous_stop(current_user: CurrentUser) -> TourSessionResponse:
    require_session(current_user.username)
    return to_session_response(tour_sessions.go_back(current_user.username))


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
def end_tour(current_user: CurrentUser) -> Response:
    require_session(current_user.username)
    tour_sessions.end(current_user.username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{tour_id}", response_model=TourResponse)
def read_tour(tour_id: int, database_session: DatabaseSession) -> TourResponse:
    return to_tour_response(get_tour_or_404(database_session, tour_id))


@router.post("/{tour_id}/start", response_model=TourSessionResponse)
def start_tour(
    tour_id: int, database_session: DatabaseSession, current_user: CurrentUser
) -> TourSessionResponse:
    tour = get_tour_or_404(database_session, tour_id)
    session = tour_sessions.start(current_user.username, tour.id, tour.name, session_stops(tour))
    return to_session_response(session)


@router.delete("/{tour_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tour(
    tour_id: int, database_session: DatabaseSession, _admin_user: AdminUser
) -> Response:
    database_session.delete(get_tour_or_404(database_session, tour_id))
    database_session.commit()
    tour_sessions.end_all_for_tour(tour_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
