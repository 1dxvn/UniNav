from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

USERNAME_PATTERN: str = r"^[A-Za-z0-9_.-]+$"


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=72)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
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


class RouteRequest(BaseModel):
    origin_id: int = Field(gt=0)
    destination_id: int = Field(gt=0)


class RouteResponse(BaseModel):
    path: list[str]
    distance: float = Field(ge=0)
    origin_name: str
    destination_name: str


class PopularRouteResponse(BaseModel):
    origin_name: str
    destination_name: str
    frequency: int = Field(ge=1)