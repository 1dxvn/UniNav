from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from config import MAX_MULTI_STOP_BUILDINGS
from schemas.paths import PathKind


class PathAlgorithm(str, Enum):
    A_STAR = "a_star"
    DIJKSTRA = "dijkstra"


class RouteMode(str, Enum):
    # shortest: walking metres, as before (elevators only when stairs are avoided).
    # comfortable: estimated effort (slower stairs, elevator wait) plus what users taught the router.
    SHORTEST = "shortest"
    COMFORTABLE = "comfortable"


class FeedbackReason(str, Enum):
    TOO_LONG = "too_long"
    CONFUSING = "confusing"
    CROWDED = "crowded"
    CLOSED = "closed"
    OTHER = "other"


class RouteOutcome(str, Enum):
    ARRIVED = "arrived"
    ABANDONED = "abandoned"


class RouteStep(BaseModel):
    origin_name: str
    destination_name: str
    kind: PathKind
    distance: float = Field(ge=0)
    origin_id: int
    destination_id: int
    path_id: int
    connection_code: str
    origin_display_name: str
    destination_display_name: str


class RouteWaypoint(BaseModel):
    id: int
    code: str
    name: str
    display_name: str
    x: float
    y: float
    floor: int
    elevation_m: float
    block_code: str | None
    floor_code: str | None


class RouteRequest(BaseModel):
    origin_id: int = Field(gt=0)
    destination_id: int = Field(gt=0)
    algorithm: PathAlgorithm = PathAlgorithm.A_STAR
    avoid: list[PathKind] = Field(default_factory=list, description="Path kinds to avoid, e.g. stairs.")
    mode: RouteMode = RouteMode.SHORTEST


class RouteResponse(BaseModel):
    path: list[str]
    steps: list[RouteStep]
    distance: float = Field(ge=0)
    origin_name: str
    destination_name: str
    waypoints: list[RouteWaypoint]
    mode: RouteMode = RouteMode.SHORTEST
    estimated_seconds: float | None = Field(default=None, ge=0)
    observation_id: int | None = None


class RouteAlternative(BaseModel):
    key: str
    label: str
    mode: RouteMode
    avoid: list[PathKind]
    distance: float = Field(ge=0)
    estimated_seconds: float = Field(ge=0)
    steps: int = Field(ge=0)
    uses_stairs: bool
    uses_elevator: bool


class RouteFeedbackRequest(BaseModel):
    observation_id: int = Field(gt=0)
    rating: int = Field(description="1 = good route, -1 = bad route.")
    reason: FeedbackReason | None = None
    step_index: int | None = Field(default=None, ge=0, description="Route step where the problem was.")


class RouteOutcomeRequest(BaseModel):
    outcome: RouteOutcome


class BlockedPathRequest(BaseModel):
    path_id: int = Field(gt=0)
    reason: str = Field(default="closed", max_length=30)


class LearnedPath(BaseModel):
    path_id: int
    origin_name: str
    destination_name: str
    kind: PathKind
    multiplier: float
    evidence: float


class BlockedPathStatus(BaseModel):
    path_id: int
    origin_name: str
    destination_name: str
    reports: int
    confirmed: bool
    active: bool
    expires_at: datetime | None


class RouteLearningResponse(BaseModel):
    observations: int
    feedback: dict[str, int]
    outcomes: dict[str, int]
    learned_paths: list[LearnedPath]
    blocked_paths: list[BlockedPathStatus]
    parameters: dict[str, float]


class RoutePreferencesResponse(BaseModel):
    suggest_avoid_stairs: bool
    recent_avoid_stairs: int
    recent_routes: int


class AlgorithmResult(BaseModel):
    algorithm: PathAlgorithm
    path: list[str]
    distance: float = Field(ge=0)
    waypoints: list[RouteWaypoint]


class RouteComparisonResponse(BaseModel):
    origin_name: str
    destination_name: str
    results: list[AlgorithmResult]


class MultiStopRequest(BaseModel):
    building_ids: list[int] = Field(min_length=2, max_length=MAX_MULTI_STOP_BUILDINGS)
    algorithm: PathAlgorithm = PathAlgorithm.A_STAR
    avoid: list[PathKind] = Field(default_factory=list)
    mode: RouteMode = RouteMode.SHORTEST


class RouteLeg(BaseModel):
    origin_name: str
    destination_name: str
    path: list[str]
    steps: list[RouteStep]
    distance: float = Field(ge=0)
    waypoints: list[RouteWaypoint]


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
