"""Effort model for the "comfortable" route mode. Costs are metre-equivalents of level walking.

Starting values are assumptions (SUPUESTO), not survey data: a metre of stairs costs as much as 1.6 m of
corridor, a ramp 1.2 m, and each elevator hop adds the wait and the ride (~12 s, about 15 m of walking).
What users report then moves each connection within [MIN_MULTIPLIER, MAX_MULTIPLIER] (services.route_learning).
"""
from __future__ import annotations

from collections.abc import Iterable

KIND_FACTORS: dict[str, float] = {"corridor": 1.0, "outdoor": 1.0, "ramp": 1.2, "stairs": 1.6, "elevator": 1.0}
ELEVATOR_HOP_PENALTY_M: float = 15.0
WALKING_SPEED_M_S: float = 1.25
MIN_MULTIPLIER: float = 0.85
MAX_MULTIPLIER: float = 3.0


def comfort_cost(length: float, kind: str, multiplier: float = 1.0) -> float:
    penalty = ELEVATOR_HOP_PENALTY_M if kind == "elevator" else 0.0
    return length * KIND_FACTORS.get(kind, 1.0) * multiplier + penalty


def estimated_seconds(steps: Iterable[tuple[float, str]]) -> float:
    """Walking time of a route, from its (physical length, kind) steps, before any learned multiplier."""
    return sum(comfort_cost(length, kind) for length, kind in steps) / WALKING_SPEED_M_S
