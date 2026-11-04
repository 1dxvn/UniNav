from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func, select

from config import FLOORS
from dependencies import DatabaseSession
from models import Building
from schemas.floors import FloorResponse

router = APIRouter(prefix="/floors", tags=["floors"])


@router.get("", response_model=list[FloorResponse])
def list_floors(database_session: DatabaseSession) -> list[FloorResponse]:
    counts = dict(
        database_session.execute(
            select(Building.floor, func.count()).group_by(Building.floor)
        ).all()
    )
    return [
        FloorResponse(level=level, name=name, building_count=counts.get(level, 0))
        for level, name in FLOORS.items()
    ]
