from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

MAX_TOUR_STOPS: int = 30


class TourCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    building_ids: list[int] = Field(min_length=2, max_length=MAX_TOUR_STOPS)


class TourStopResponse(BaseModel):
    position: int = Field(ge=1)
    building_id: int
    building_name: str
    floor: int


class TourSummaryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    stop_count: int


class TourResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    stops: list[TourStopResponse]


class TourSessionResponse(BaseModel):
    tour_id: int
    tour_name: str
    current_stop: TourStopResponse
    total_stops: int
