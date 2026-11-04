from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from config import MAX_MULTI_STOP_BUILDINGS
from schemas.paths import PathKind


class PathAlgorithm(str, Enum):
    A_STAR = "a_star"
    DIJKSTRA = "dijkstra"


class RouteStep(BaseModel):
    origin_name: str
    destination_name: str
    kind: PathKind
    distance: float = Field(ge=0)


class RouteRequest(BaseModel):
    origin_id: int = Field(gt=0)
    destination_id: int = Field(gt=0)
    algorithm: PathAlgorithm = PathAlgorithm.A_STAR
    avoid: list[PathKind] = Field(default_factory=list, description="Path kinds to avoid, e.g. stairs.")


class RouteResponse(BaseModel):
    path: list[str]
    steps: list[RouteStep]
    distance: float = Field(ge=0)
    origin_name: str
    destination_name: str


class AlgorithmResult(BaseModel):
    algorithm: PathAlgorithm
    path: list[str]
    distance: float = Field(ge=0)


class RouteComparisonResponse(BaseModel):
    origin_name: str
    destination_name: str
    results: list[AlgorithmResult]


class MultiStopRequest(BaseModel):
    building_ids: list[int] = Field(min_length=2, max_length=MAX_MULTI_STOP_BUILDINGS)
    algorithm: PathAlgorithm = PathAlgorithm.A_STAR
    avoid: list[PathKind] = Field(default_factory=list)


class RouteLeg(BaseModel):
    origin_name: str
    destination_name: str
    path: list[str]
    steps: list[RouteStep]
    distance: float = Field(ge=0)


class MultiStopResponse(BaseModel):
    legs: list[RouteLeg]
    total_distance: float = Field(ge=0)


class PopularRouteResponse(BaseModel):
    origin_name: str
    destination_name: str
    frequency: int = Field(ge=1)


class RouteVisitResponse(BaseModel):
    id: int
    origin_name: str
    destination_name: str
    distance: float
    visited_at: datetime
