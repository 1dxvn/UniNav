from __future__ import annotations

from fastapi import APIRouter, Query

from config import POPULAR_ROUTES_LIMIT
from dependencies import DatabaseSession
from schemas.rankings import PopularPlaceResponse
from services.rankings import rank_places_by_visits

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/places", response_model=list[PopularPlaceResponse])
def read_most_visited_places(
    database_session: DatabaseSession,
    limit: int = Query(default=POPULAR_ROUTES_LIMIT, ge=1, le=50),
) -> list[PopularPlaceResponse]:
    return rank_places_by_visits(database_session, limit)
