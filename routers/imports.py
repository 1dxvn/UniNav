from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from dependencies import AdminUser, DatabaseSession
from models import Building
from schemas.buildings import BuildingCreate, BuildingResponse
from services.campus_graph import campus_graph_service

router = APIRouter(prefix="/buildings", tags=["buildings"])


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


@router.post("/import", response_model=list[BuildingResponse], status_code=status.HTTP_201_CREATED)
def import_buildings(
    buildings_data: list[BuildingCreate],
    database_session: DatabaseSession,
    _admin_user: AdminUser,
) -> list[Building]:
    if not buildings_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The import list is empty.")

    names = [building.name for building in buildings_data]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        raise conflict(f"Duplicated names in the request: {', '.join(repeated)}.")

    stored = sorted(database_session.scalars(select(Building.name).where(Building.name.in_(names))))
    if stored:
        raise conflict(f"Buildings already exist: {', '.join(stored)}.")

    new_buildings = [Building(**building.model_dump()) for building in buildings_data]
    database_session.add_all(new_buildings)
    try:
        database_session.commit()
    except IntegrityError as error:
        database_session.rollback()
        raise conflict("One or more buildings already exist.") from error

    for building in new_buildings:
        database_session.refresh(building)

    campus_graph_service.load_from_database()
    return new_buildings
