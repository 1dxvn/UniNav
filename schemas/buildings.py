from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
    faculty: Optional[str] = Field(default=None, max_length=100)
    building_type: Optional[str] = Field(default=None, max_length=50)


class BuildingUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    x: Optional[float] = Field(default=None, allow_inf_nan=False)
    y: Optional[float] = Field(default=None, allow_inf_nan=False)
    faculty: Optional[str] = Field(default=None, max_length=100)
    building_type: Optional[str] = Field(default=None, max_length=50)


class BuildingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    x: float
    y: float
    faculty: Optional[str]
    building_type: Optional[str]


class NearbyBuildingResponse(BaseModel):
    building: BuildingResponse
    distance: float = Field(ge=0)
