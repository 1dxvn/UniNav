from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import delete
from sqlalchemy.orm import Session, selectinload

from dependencies import CurrentUser, DatabaseSession
from models import RouteVisit
from schemas.routes import RouteVisitResponse
from services.history import to_visit_response, user_history_newest_first

router = APIRouter(prefix="/routes/history", tags=["history"])


@router.get("", response_model=list[RouteVisitResponse])
def read_route_history(
    database_session: DatabaseSession,
    current_user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[RouteVisitResponse]:
    visits = user_history_newest_first(database_session, current_user.id)
    return [to_visit_response(visit) for visit in visits[:limit]]


@router.get("/last", response_model=RouteVisitResponse)
def read_last_route(
    database_session: DatabaseSession, current_user: CurrentUser
) -> RouteVisitResponse:
    visits = user_history_newest_first(database_session, current_user.id)
    if not visits:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No routes recorded yet.")
    return to_visit_response(visits[0])


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_route_history(database_session: DatabaseSession, current_user: CurrentUser) -> Response:
    database_session.execute(delete(RouteVisit).where(RouteVisit.user_id == current_user.id))
    database_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def get_own_visit(database_session: Session, user_id: int, visit_id: int) -> RouteVisit:
    visit = database_session.get(
        RouteVisit,
        visit_id,
        options=[selectinload(RouteVisit.origin), selectinload(RouteVisit.destination)],
    )
    if visit is None or visit.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Visit {visit_id} not found.")
    return visit


@router.get("/{visit_id}", response_model=RouteVisitResponse)
def read_route_visit(
    visit_id: int, database_session: DatabaseSession, current_user: CurrentUser
) -> RouteVisitResponse:
    return to_visit_response(get_own_visit(database_session, current_user.id, visit_id))


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route_visit(
    visit_id: int, database_session: DatabaseSession, current_user: CurrentUser
) -> Response:
    database_session.delete(get_own_visit(database_session, current_user.id, visit_id))
    database_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
