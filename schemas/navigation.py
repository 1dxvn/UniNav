from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class VisitRequest(BaseModel):
    building_id: int = Field(gt=0)


class NavigationStopResponse(BaseModel):
    building_id: int
    building_name: str
    floor: int


class NavigationStateResponse(BaseModel):
    current: Optional[NavigationStopResponse]
    can_go_back: bool
    can_go_forward: bool


class TrailEntryResponse(NavigationStopResponse):
    is_current: bool


class NavigationTrailResponse(NavigationStateResponse):
    trail: list[TrailEntryResponse]
