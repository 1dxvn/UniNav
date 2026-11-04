from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from data_structures.avl_tree import AVLTree
from models import Building, RouteVisit
from schemas.routes import PopularRouteResponse


def rank_popular_routes(database_session: Session, limit: int) -> list[PopularRouteResponse]:
    origin = aliased(Building)
    destination = aliased(Building)

    frequencies = database_session.execute(
        select(origin.name, destination.name, func.count())
        .select_from(RouteVisit)
        .join(origin, RouteVisit.origin_id == origin.id)
        .join(destination, RouteVisit.destination_id == destination.id)
        .group_by(RouteVisit.origin_id, RouteVisit.destination_id, origin.name, destination.name)
    ).all()

    ranking: AVLTree[int, tuple[str, str]] = AVLTree()
    for origin_name, destination_name, frequency in frequencies:
        ranking.insert(frequency, (origin_name, destination_name))

    return [
        PopularRouteResponse(origin_name=o, destination_name=d, frequency=frequency)
        for frequency, (o, d) in ranking.reverse_in_order()[:limit]
    ]
