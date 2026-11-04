from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Building, RouteVisit
from schemas.auth import UserStatsResponse


def compute_user_stats(database_session: Session, user_id: int) -> UserStatsResponse:
    total_routes, total_distance = database_session.execute(
        select(func.count(), func.coalesce(func.sum(RouteVisit.distance), 0.0)).where(
            RouteVisit.user_id == user_id
        )
    ).one()

    favorite = database_session.execute(
        select(Building.name)
        .join(RouteVisit, RouteVisit.destination_id == Building.id)
        .where(RouteVisit.user_id == user_id)
        .group_by(Building.id, Building.name)
        .order_by(func.count().desc(), Building.name)
        .limit(1)
    ).scalar_one_or_none()

    return UserStatsResponse(
        total_routes=total_routes,
        total_distance=total_distance,
        average_distance=total_distance / total_routes if total_routes else 0.0,
        most_visited_destination=favorite,
    )
