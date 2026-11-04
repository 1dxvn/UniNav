from __future__ import annotations

from pydantic import BaseModel


class FloorResponse(BaseModel):
    level: int
    name: str
    building_count: int
