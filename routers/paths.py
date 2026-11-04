from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from dependencies import AdminUser, DatabaseSession
from models import CampusPath
from schemas.paths import PathCreate, PathResponse, PathUpdate
from services.buildings import get_building_or_404
from services.campus_graph import campus_graph_service
from services.paths import (
    ensure_pair_is_free,
    get_path_or_404,
    to_path_response,
)

router = APIRouter(prefix="/paths", tags=["paths"])


def create_path_record(database_session: DatabaseSession, data: PathCreate) -> CampusPath:
    if data.source_id == data.target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A path must connect two different buildings.",
        )
    get_building_or_404(database_session, data.source_id, "Source building")
    get_building_or_404(database_session, data.target_id, "Target building")
    ensure_pair_is_free(database_session, data.source_id, data.target_id)

    path = CampusPath(**data.model_dump(mode="json"))
    database_session.add(path)
    return path


@router.get("", response_model=list[PathResponse])
def list_paths(
    database_session: DatabaseSession, building_id: Optional[int] = None
) -> list[PathResponse]:
    query = (
        select(CampusPath)
        .options(selectinload(CampusPath.source), selectinload(CampusPath.target))
        .order_by(CampusPath.id)
    )
    if building_id is not None:
        query = query.where(
            or_(CampusPath.source_id == building_id, CampusPath.target_id == building_id)
        )
    return [to_path_response(path) for path in database_session.scalars(query)]


@router.post("", response_model=PathResponse, status_code=status.HTTP_201_CREATED)
def create_path(
    path_data: PathCreate, database_session: DatabaseSession, _admin_user: AdminUser
) -> PathResponse:
    path = create_path_record(database_session, path_data)
    database_session.commit()

    campus_graph_service.load_from_database()
    return to_path_response(get_path_or_404(database_session, path.id))


@router.post("/import", response_model=list[PathResponse], status_code=status.HTTP_201_CREATED)
def import_paths(
    paths_data: list[PathCreate], database_session: DatabaseSession, _admin_user: AdminUser
) -> list[PathResponse]:
    if not paths_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The import list is empty.")

    created: list[CampusPath] = []
    for data in paths_data:
        created.append(create_path_record(database_session, data))
        database_session.flush()
    database_session.commit()

    campus_graph_service.load_from_database()
    return [to_path_response(get_path_or_404(database_session, path.id)) for path in created]


@router.get("/{path_id}", response_model=PathResponse)
def read_path(path_id: int, database_session: DatabaseSession) -> PathResponse:
    return to_path_response(get_path_or_404(database_session, path_id))


@router.put("/{path_id}", response_model=PathResponse)
def update_path(
    path_id: int,
    path_data: PathUpdate,
    database_session: DatabaseSession,
    _admin_user: AdminUser,
) -> PathResponse:
    path = get_path_or_404(database_session, path_id)
    changes = path_data.model_dump(exclude_unset=True)
    for field in ("bidirectional", "kind"):
        if changes.get(field, True) is None:
            changes.pop(field)

    for field, value in changes.items():
        setattr(path, field, getattr(value, "value", value))
    database_session.commit()

    campus_graph_service.load_from_database()
    return to_path_response(path)


@router.delete("/{path_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_path(
    path_id: int, database_session: DatabaseSession, _admin_user: AdminUser
) -> Response:
    database_session.delete(get_path_or_404(database_session, path_id))
    database_session.commit()

    campus_graph_service.load_from_database()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
