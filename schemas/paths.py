from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PathKind(str, Enum):
    CORRIDOR = "corridor"
    STAIRS = "stairs"
    ELEVATOR = "elevator"
    RAMP = "ramp"
    OUTDOOR = "outdoor"


class PathCreate(BaseModel):
    source_id: int = Field(gt=0)
    target_id: int = Field(gt=0)
    weight: Optional[float] = Field(
        default=None,
        ge=0,
        allow_inf_nan=False,
        description="Walking cost. Never lower than the straight-line distance.",
    )
    bidirectional: bool = True
    kind: PathKind = PathKind.CORRIDOR


class PathUpdate(BaseModel):
    weight: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    bidirectional: Optional[bool] = None
    kind: Optional[PathKind] = None


class PathResponse(BaseModel):
    id: int
    source_id: int
    target_id: int
    source_name: str
    target_name: str
    weight: float = Field(ge=0, description="Effective weight used by the route algorithms.")
    bidirectional: bool
    kind: PathKind
