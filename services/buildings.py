from __future__ import annotations

import math

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Building


def get_building_or_404(database_session: Session, building_id: int, label: str = "Building") -> Building:
    building = database_session.get(Building, building_id)
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{label} {building_id} not found.",
        )
    return building


def ensure_name_available(
    database_session: Session, name: str, ignore_id: int | None = None
) -> None:
    existing_id = database_session.scalar(select(Building.id).where(Building.name == name))
    if existing_id is not None and existing_id != ignore_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Building '{name}' already exists.",
        )


def distance_between(first: Building, x: float, y: float) -> float:
    return math.hypot(first.x - x, first.y - y)
