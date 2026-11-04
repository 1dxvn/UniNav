from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Building
from schemas.routes import PathAlgorithm
from services.buildings import get_building_or_404
from services.campus_graph import campus_graph_service


def resolve_endpoints(
    database_session: Session, origin_id: int, destination_id: int
) -> tuple[Building, Building]:
    origin = get_building_or_404(database_session, origin_id, "Origin building")
    destination = get_building_or_404(database_session, destination_id, "Destination building")
    return origin, destination


def compute_path(
    origin: Building, destination: Building, algorithm: PathAlgorithm
) -> tuple[list[str], float]:
    if not campus_graph_service.contains(origin.name, destination.name):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The campus graph is out of sync with the database. Reload the graph.",
        )

    path, distance = campus_graph_service.find_path(origin.name, destination.name, algorithm)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"There is no route from '{origin.name}' to '{destination.name}'.",
        )
    return path, distance
