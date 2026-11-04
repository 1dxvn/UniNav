from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from models import Tour, TourStop
from schemas.tours import (
    TourResponse,
    TourSessionResponse,
    TourStopResponse,
    TourSummaryResponse,
)
from services.tour_sessions import SessionStop, TourSession


def get_tour_or_404(database_session: Session, tour_id: int) -> Tour:
    tour = database_session.get(
        Tour,
        tour_id,
        options=[selectinload(Tour.stops).selectinload(TourStop.building)],
    )
    if tour is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tour {tour_id} not found.")
    return tour


def to_stop_response(stop: SessionStop) -> TourStopResponse:
    return TourStopResponse(
        position=stop.position,
        building_id=stop.building_id,
        building_name=stop.building_name,
        floor=stop.floor,
    )


def session_stops(tour: Tour) -> list[SessionStop]:
    return [
        SessionStop(index, stop.building_id, stop.building.name, stop.building.floor)
        for index, stop in enumerate(tour.stops, start=1)
    ]


def to_tour_response(tour: Tour) -> TourResponse:
    return TourResponse(
        id=tour.id,
        name=tour.name,
        description=tour.description,
        stops=[to_stop_response(stop) for stop in session_stops(tour)],
    )


def to_tour_summary(tour: Tour) -> TourSummaryResponse:
    return TourSummaryResponse(
        id=tour.id, name=tour.name, description=tour.description, stop_count=len(tour.stops)
    )


def to_session_response(session: TourSession) -> TourSessionResponse:
    return TourSessionResponse(
        tour_id=session.tour_id,
        tour_name=session.tour_name,
        current_stop=to_stop_response(session.current_stop),
        total_stops=session.total_stops,
    )
