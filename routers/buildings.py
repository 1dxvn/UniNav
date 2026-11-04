from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import select

from config import NEAREST_BUILDINGS_LIMIT
from dependencies import CurrentUser, DatabaseSession
from models import Building
from schemas.buildings import (
    BuildingCreate,
    BuildingResponse,
    BuildingUpdate,
    NearbyBuildingResponse,
)
from services.buildings import distance_between, ensure_name_available, get_building_or_404
from services.campus_graph import campus_graph_service

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[BuildingResponse])
def list_buildings(
    database_session: DatabaseSession,
    search: Optional[str] = Query(default=None, min_length=1, description="Name contains"),
    faculty: Optional[str] = None,
    building_type: Optional[str] = None,
    floor: Optional[int] = Query(default=None, ge=0),
) -> list[Building]:
    query = select(Building).order_by(Building.name)
    if search:
        query = query.where(Building.name.ilike(f"%{search}%"))
    if faculty:
        query = query.where(Building.faculty == faculty)
    if building_type:
        query = query.where(Building.building_type == building_type)
    if floor is not None:
        query = query.where(Building.floor == floor)
    return list(database_session.scalars(query))


@router.post("", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
def create_building(
    building_data: BuildingCreate,
    database_session: DatabaseSession,
    _current_user: CurrentUser,
) -> Building:
    ensure_name_available(database_session, building_data.name)

    new_building = Building(**building_data.model_dump())
    database_session.add(new_building)
    database_session.commit()
    database_session.refresh(new_building)

    campus_graph_service.add_building(
        new_building.name, new_building.x, new_building.y, new_building.floor
    )
    return new_building


@router.get("/faculties", response_model=list[str])
def list_faculties(database_session: DatabaseSession) -> list[str]:
    query = select(Building.faculty).where(Building.faculty.is_not(None)).distinct()
    return sorted(database_session.scalars(query))


@router.get("/types", response_model=list[str])
def list_building_types(database_session: DatabaseSession) -> list[str]:
    query = select(Building.building_type).where(Building.building_type.is_not(None)).distinct()
    return sorted(database_session.scalars(query))


@router.get("/nearest", response_model=list[NearbyBuildingResponse])
def find_nearest_buildings(
    database_session: DatabaseSession,
    x: float,
    y: float,
    limit: int = Query(default=NEAREST_BUILDINGS_LIMIT, ge=1, le=50),
) -> list[NearbyBuildingResponse]:
    buildings = database_session.scalars(select(Building)).all()
    ranked = sorted(buildings, key=lambda building: distance_between(building, x, y))
    return [
        NearbyBuildingResponse(building=building, distance=distance_between(building, x, y))
        for building in ranked[:limit]
    ]


@router.get("/{building_id}", response_model=BuildingResponse)
def read_building(building_id: int, database_session: DatabaseSession) -> Building:
    return get_building_or_404(database_session, building_id)


@router.get("/{building_id}/neighbors", response_model=list[NearbyBuildingResponse])
def read_building_neighbors(
    building_id: int,
    database_session: DatabaseSession,
    limit: int = Query(default=NEAREST_BUILDINGS_LIMIT, ge=1, le=50),
) -> list[NearbyBuildingResponse]:
    building = get_building_or_404(database_session, building_id)
    if not campus_graph_service.contains(building.name):
        return []

    closest = sorted(campus_graph_service.neighbors(building.name).items(), key=lambda p: p[1])
    names = [name for name, _ in closest[:limit]]
    by_name = {
        found.name: found
        for found in database_session.scalars(select(Building).where(Building.name.in_(names)))
    }
    return [
        NearbyBuildingResponse(building=by_name[name], distance=distance)
        for name, distance in closest[:limit]
        if name in by_name
    ]


@router.put("/{building_id}", response_model=BuildingResponse)
def update_building(
    building_id: int,
    building_data: BuildingUpdate,
    database_session: DatabaseSession,
    _current_user: CurrentUser,
) -> Building:
    building = get_building_or_404(database_session, building_id)
    changes = building_data.model_dump(exclude_unset=True)
    if "name" in changes:
        if changes["name"] is None:
            changes.pop("name")
        else:
            ensure_name_available(database_session, changes["name"], ignore_id=building.id)
    for field in ("x", "y", "floor"):
        if changes.get(field, 0.0) is None:
            changes.pop(field)

    for field, value in changes.items():
        setattr(building, field, value)
    database_session.commit()
    database_session.refresh(building)

    campus_graph_service.load_from_database()
    return building


@router.delete("/{building_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_building(
    building_id: int,
    database_session: DatabaseSession,
    _current_user: CurrentUser,
) -> Response:
    building = get_building_or_404(database_session, building_id)
    campus_graph_service.remove_building(building.name)
    database_session.delete(building)
    database_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
