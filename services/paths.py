from __future__ import annotations

import math

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from config import FLOOR_HEIGHT
from models import CampusPath
from schemas.paths import PathResponse


def effective_weight(path: CampusPath) -> float:
    straight_line = math.hypot(
        path.source.x - path.target.x,
        path.source.y - path.target.y,
        (path.source.floor - path.target.floor) * FLOOR_HEIGHT,
    )
    return max(path.weight or 0.0, straight_line)


def to_path_response(path: CampusPath) -> PathResponse:
    return PathResponse(
        id=path.id,
        source_id=path.source_id,
        target_id=path.target_id,
        source_name=path.source.name,
        target_name=path.target.name,
        weight=effective_weight(path),
        bidirectional=path.bidirectional,
        kind=path.kind,
    )


def get_path_or_404(database_session: Session, path_id: int) -> CampusPath:
    path = database_session.get(
        CampusPath,
        path_id,
        options=[selectinload(CampusPath.source), selectinload(CampusPath.target)],
    )
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Path {path_id} not found.")
    return path


def ensure_pair_is_free(database_session: Session, source_id: int, target_id: int) -> None:
    existing = database_session.scalar(
        select(CampusPath.id).where(
            or_(
                and_(CampusPath.source_id == source_id, CampusPath.target_id == target_id),
                and_(CampusPath.source_id == target_id, CampusPath.target_id == source_id),
            )
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Buildings {source_id} and {target_id} are already connected by path {existing}.",
        )
