from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from data_structures.stack import Stack
from models import RouteVisit
from schemas.routes import RouteVisitResponse


def to_visit_response(visit: RouteVisit) -> RouteVisitResponse:
    return RouteVisitResponse(
        id=visit.id,
        origin_name=visit.origin.name,
        destination_name=visit.destination.name,
        distance=visit.distance,
        visited_at=visit.visited_at,
    )


def user_history_newest_first(database_session: Session, user_id: int) -> list[RouteVisit]:
    visits_oldest_first = database_session.scalars(
        select(RouteVisit)
        .where(RouteVisit.user_id == user_id)
        .options(selectinload(RouteVisit.origin), selectinload(RouteVisit.destination))
        .order_by(RouteVisit.visited_at, RouteVisit.id)
    ).all()

    history: Stack[RouteVisit] = Stack()
    for visit in visits_oldest_first:
        history.push(visit)

    visits: list[RouteVisit] = []
    while not history.is_empty():
        visits.append(history.pop())
    return visits
