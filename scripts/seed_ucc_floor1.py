"""Idempotent real-floor seed in a dedicated development DB; leaves uninav.db alone."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from scripts.ucc_floor1_data import PATHS, PLACES


def seed_campus(database_session: Session) -> tuple[int, int]:
    from sqlalchemy import select
    from models import Building, CampusPath

    expected_names = {place[0] for place in PLACES}
    buildings = {place.name: place for place in database_session.scalars(select(Building))}
    if set(buildings) - expected_names:
        raise ValueError("This database contains another campus. Use the dedicated uninav-campus.db.")
    created_places = 0
    for name, x, y, floor, faculty, building_type in PLACES:
        if name in buildings:
            place = buildings[name]
            if abs(place.x - x) > 0.001 or abs(place.y - y) > 0.001 or place.floor != floor:
                raise ValueError(f"Existing coordinates differ for {name}; review the campus data first.")
            continue
        place = Building(name=name, x=x, y=y, floor=floor, faculty=faculty, building_type=building_type)
        database_session.add(place)
        buildings[name] = place
        created_places += 1
    database_session.flush()
    existing = {(edge.source_id, edge.target_id) for edge in database_session.scalars(select(CampusPath))}
    created_paths = 0
    for source, target, kind in PATHS:
        pair = (buildings[source].id, buildings[target].id)
        if pair not in existing:
            database_session.add(CampusPath(source_id=pair[0], target_id=pair[1], kind=kind, bidirectional=True))
            created_paths += 1
    return created_places, created_paths


def main() -> None:
    campus_db = Path(__file__).resolve().parents[1] / "uninav-campus.db"
    os.environ.setdefault("UNINAV_DATABASE_URL", f"sqlite:///{campus_db.as_posix()}")
    from database import SessionLocal, init_db
    from scripts.seed import seed_users

    init_db()
    with SessionLocal() as session:
        counts = seed_campus(session)
        seed_users(session)
        session.commit()
    print(f"UCC floor 1: created {counts[0]} places and {counts[1]} paths. Sample campus unchanged.")


if __name__ == "__main__":
    main()
