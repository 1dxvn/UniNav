from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from config import MAX_FLOOR


class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
    floor: int = Field(default=0, ge=0, le=MAX_FLOOR)
    faculty: Optional[str] = Field(default=None, max_length=100)
    building_type: Optional[str] = Field(default=None, max_length=50)
    code: Optional[str] = Field(default=None, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    block_code: Optional[str] = Field(default=None, max_length=32)
    floor_code: Optional[str] = Field(default=None, max_length=64)
    elevation_m: Optional[float] = Field(default=None, allow_inf_nan=False)
    elevation_source: Optional[str] = Field(default=None, max_length=1000)


class BuildingUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    x: Optional[float] = Field(default=None, allow_inf_nan=False)
    y: Optional[float] = Field(default=None, allow_inf_nan=False)
    floor: Optional[int] = Field(default=None, ge=0, le=MAX_FLOOR)
    faculty: Optional[str] = Field(default=None, max_length=100)
    building_type: Optional[str] = Field(default=None, max_length=50)
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    block_code: Optional[str] = Field(default=None, max_length=32)
    floor_code: Optional[str] = Field(default=None, max_length=64)
    elevation_m: Optional[float] = Field(default=None, allow_inf_nan=False)
    elevation_source: Optional[str] = Field(default=None, max_length=1000)


class BuildingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    x: float
    y: float
    floor: int
    faculty: Optional[str]
    building_type: Optional[str]
    code: str
    display_name: Optional[str]
    block_code: Optional[str]
    floor_code: Optional[str]
    elevation_m: Optional[float]
    elevation_source: Optional[str]
    effective_elevation_m: float
    data_scope: Optional[str]


class NearbyBuildingResponse(BaseModel):
    building: BuildingResponse
    distance: float = Field(ge=0)
