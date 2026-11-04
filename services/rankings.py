from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data_structures.max_heap import MaxHeap
from models import Building, RouteVisit
from schemas.rankings import PopularPlaceResponse


def rank_places_by_visits(database_session: Session, limit: int) -> list[PopularPlaceResponse]:
    """Places ordered by how many times they were chosen as a route destination."""
    rows = database_session.execute(
        select(Building.id, Building.name, Building.floor, func.count(RouteVisit.id))
        .join(RouteVisit, RouteVisit.destination_id == Building.id)
        .group_by(Building.id, Building.name, Building.floor)
        .order_by(Building.name)
    ).all()

    heap: MaxHeap[tuple[int, str, int]] = MaxHeap()
    for building_id, name, floor, visits in rows:
        heap.push((building_id, name, floor), visits)

    ranking: list[PopularPlaceResponse] = []
    while not heap.is_empty() and len(ranking) < limit:
        (building_id, name, floor), visits = heap.pop_max()
        ranking.append(
            PopularPlaceResponse(
                rank=len(ranking) + 1,
                building_id=building_id,
                building_name=name,
                floor=floor,
                visits=int(visits),
            )
        )
    return ranking
