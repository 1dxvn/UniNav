from __future__ import annotations

from pydantic import BaseModel, Field


class PopularPlaceResponse(BaseModel):
    rank: int = Field(ge=1)
    building_id: int
    building_name: str
    floor: int
    visits: int = Field(ge=1)
