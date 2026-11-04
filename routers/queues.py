from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from dependencies import AdminUser, CurrentUser, DatabaseSession
from schemas.queues import QueuePositionResponse, QueueStatusResponse, ServedResponse
from services.buildings import get_building_or_404
from services.waiting_lines import waiting_lines

router = APIRouter(prefix="/queues", tags=["queues"])


def not_waiting(building_name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"You are not waiting at '{building_name}'.",
    )


@router.get("/{building_id}", response_model=QueueStatusResponse)
def read_queue(building_id: int, database_session: DatabaseSession) -> QueueStatusResponse:
    building = get_building_or_404(database_session, building_id)
    return QueueStatusResponse(
        building_id=building.id,
        building_name=building.name,
        length=waiting_lines.length(building.id),
    )


@router.post(
    "/{building_id}/join",
    response_model=QueuePositionResponse,
    status_code=status.HTTP_201_CREATED,
)
def join_queue(
    building_id: int, database_session: DatabaseSession, current_user: CurrentUser
) -> QueuePositionResponse:
    building = get_building_or_404(database_session, building_id)
    position = waiting_lines.join(building.id, current_user.username)
    if position is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You are already waiting at '{building.name}'.",
        )
    return QueuePositionResponse(
        building_id=building.id,
        building_name=building.name,
        length=waiting_lines.length(building.id),
        position=position,
    )


@router.get("/{building_id}/position", response_model=QueuePositionResponse)
def read_my_position(
    building_id: int, database_session: DatabaseSession, current_user: CurrentUser
) -> QueuePositionResponse:
    building = get_building_or_404(database_session, building_id)
    position = waiting_lines.position(building.id, current_user.username)
    if position is None:
        raise not_waiting(building.name)
    return QueuePositionResponse(
        building_id=building.id,
        building_name=building.name,
        length=waiting_lines.length(building.id),
        position=position,
    )


@router.delete("/{building_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_queue(
    building_id: int, database_session: DatabaseSession, current_user: CurrentUser
) -> Response:
    building = get_building_or_404(database_session, building_id)
    if not waiting_lines.leave(building.id, current_user.username):
        raise not_waiting(building.name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{building_id}/serve", response_model=ServedResponse)
def serve_next_in_queue(
    building_id: int, database_session: DatabaseSession, _admin_user: AdminUser
) -> ServedResponse:
    building = get_building_or_404(database_session, building_id)
    served_username = waiting_lines.serve_next(building.id)
    if served_username is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nobody is waiting.")
    return ServedResponse(
        building_id=building.id,
        building_name=building.name,
        length=waiting_lines.length(building.id),
        served_username=served_username,
    )
