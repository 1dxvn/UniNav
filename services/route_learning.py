"""Learns which campus connections people find worse or better, and which are temporarily blocked.

Free and local: plain statistics over the route_observations / route_feedback / blocked_path_reports tables.
It only re-weights connections that already exist in the reviewed graph; it never adds one, and the
"shortest" mode ignores the learned multipliers (blocked connections leave every mode).

Each connection's share of bad signals has a Beta(PRIOR_BAD, PRIOR_GOOD) prior (mean 0.2): with little
evidence it stays at 1.0, and the multiplier is bounded to [MIN_MULTIPLIER, MAX_MULTIPLIER].
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from models import BlockedPathReport, RouteFeedback, RouteObservation
from schemas.routes import FeedbackReason, RouteOutcome
from services.campus_graph import campus_graph_service
from services.route_costs import (
    ELEVATOR_HOP_PENALTY_M,
    KIND_FACTORS,
    MAX_MULTIPLIER,
    MIN_MULTIPLIER,
)

PRIOR_BAD: float = 1.0
PRIOR_GOOD: float = 4.0
PRIOR_MEAN: float = PRIOR_BAD / (PRIOR_BAD + PRIOR_GOOD)
SENSITIVITY: float = 3.0
MIN_EVIDENCE: float = 5.0
STEP_WEIGHT: float = 1.0      # the step the person pointed at
ROUTE_WEIGHT: float = 0.3     # every connection of a rated route
OUTCOME_WEIGHT: float = 0.15  # every connection of a route that was finished or abandoned
BLOCK_REPORTS: int = 3
BLOCK_WINDOW: timedelta = timedelta(hours=24)
BLOCK_TTL: timedelta = timedelta(days=7)
RETENTION_DAYS: int = 180

BAD_REASONS = {FeedbackReason.TOO_LONG.value, FeedbackReason.CONFUSING.value, FeedbackReason.CROWDED.value,
               FeedbackReason.CLOSED.value, FeedbackReason.OTHER.value}


def _naive(moment: datetime) -> datetime:
    # SQLite returns naive datetimes; everything here is UTC.
    return moment.replace(tzinfo=None) if moment.tzinfo else moment


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def multiplier(bad: float, good: float) -> float:
    if bad + good < MIN_EVIDENCE:
        return 1.0
    share = (PRIOR_BAD + bad) / (PRIOR_BAD + PRIOR_GOOD + bad + good)
    return max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, 1.0 + SENSITIVITY * (share - PRIOR_MEAN)))


def evidence(session: Session) -> dict[int, tuple[float, float]]:
    """(bad, good) weighted signals per connection."""
    observations = {o.id: o for o in session.scalars(select(RouteObservation))}
    signals: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0])

    def add(path_ids: list[int], weight: float, bad: bool) -> None:
        for path_id in path_ids:
            signals[path_id][0 if bad else 1] += weight

    for feedback in session.scalars(select(RouteFeedback)):
        observation = observations.get(feedback.observation_id)
        if observation is None:
            continue
        bad = feedback.rating < 0
        add(json.loads(observation.path_ids), ROUTE_WEIGHT, bad)
        if feedback.path_id is not None:
            add([feedback.path_id], STEP_WEIGHT, bad)
    for observation in observations.values():
        if observation.outcome in (RouteOutcome.ARRIVED.value, RouteOutcome.ABANDONED.value):
            add(json.loads(observation.path_ids), OUTCOME_WEIGHT, observation.outcome == RouteOutcome.ABANDONED.value)
    return {path_id: (values[0], values[1]) for path_id, values in signals.items()}


def block_states(session: Session, at: datetime | None = None) -> dict[int, tuple[int, bool, datetime | None]]:
    """path id -> (reports in the window, confirmed by an admin, active until). Inactive when the date is None or past."""
    at = at or now_utc()
    reports: dict[int, list[BlockedPathReport]] = defaultdict(list)
    for report in session.scalars(select(BlockedPathReport)):
        reports[report.path_id].append(report)
    states: dict[int, tuple[int, bool, datetime | None]] = {}
    for path_id, items in reports.items():
        confirmed = [_naive(r.created_at) for r in items if r.confirmed]
        recent_users = {r.user_id for r in items if at - _naive(r.created_at) <= BLOCK_WINDOW}
        until: datetime | None = None
        if confirmed:
            until = max(confirmed) + BLOCK_TTL
        if len(recent_users) >= BLOCK_REPORTS:
            latest = max(_naive(r.created_at) for r in items)
            until = max(until or latest, latest + BLOCK_TTL)
        states[path_id] = (len(items), bool(confirmed), until)
    return states


def active_blocks(session: Session) -> frozenset[int]:
    at = now_utc()
    return frozenset(path_id for path_id, (_n, _c, until) in block_states(session, at).items() if until and until > at)


def refresh(session: Session) -> None:
    """Recomputes multipliers and blocks and hands them to the router. Cheap: the tables are small."""
    multipliers = {path_id: m for path_id, (bad, good) in evidence(session).items() if (m := multiplier(bad, good)) != 1.0}
    campus_graph_service.set_learning(multipliers, active_blocks(session))


def purge_expired(session: Session) -> int:
    cutoff = now_utc() - timedelta(days=RETENTION_DAYS)
    removed = session.execute(delete(RouteObservation).where(RouteObservation.created_at < cutoff)).rowcount or 0
    session.execute(delete(BlockedPathReport).where(BlockedPathReport.created_at < cutoff))
    session.commit()
    return removed


def startup(session: Session) -> None:
    purge_expired(session)
    refresh(session)


def parameters() -> dict[str, float]:
    return {
        "stairs_factor": KIND_FACTORS["stairs"], "ramp_factor": KIND_FACTORS["ramp"],
        "elevator_hop_penalty_m": ELEVATOR_HOP_PENALTY_M, "min_multiplier": MIN_MULTIPLIER,
        "max_multiplier": MAX_MULTIPLIER, "min_evidence": MIN_EVIDENCE, "block_reports": float(BLOCK_REPORTS),
        "block_days": BLOCK_TTL.days, "retention_days": float(RETENTION_DAYS),
    }


def counts(session: Session) -> tuple[int, dict[str, int], dict[str, int]]:
    observations = session.scalar(select(func.count()).select_from(RouteObservation)) or 0
    feedback: dict[str, int] = defaultdict(int)
    for rating, reason, count in session.execute(
            select(RouteFeedback.rating, RouteFeedback.reason, func.count()).group_by(RouteFeedback.rating, RouteFeedback.reason)):
        feedback["positive" if rating > 0 else reason or "negative"] += count
    outcomes = {outcome: count for outcome, count in session.execute(
        select(RouteObservation.outcome, func.count()).where(RouteObservation.outcome.is_not(None)).group_by(RouteObservation.outcome))}
    return observations, feedback, outcomes
