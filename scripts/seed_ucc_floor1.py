"""Versioned real-floor seed; preserves other scoped floors and the sample DB."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DATASET_PATH = Path(__file__).resolve().parents[1] / "data/datasets/ucc-first-floor.json"


def seed_campus(database_session: Session) -> tuple[int, int]:
    from sqlalchemy import select
    from models import Building
    from schemas.datasets import CampusDataset
    from services.datasets import import_dataset

    dataset = CampusDataset.model_validate_json(DATASET_PATH.read_text(encoding="utf-8"))
    expected_names = {place.name for place in dataset.places}
    unrelated = database_session.scalars(select(Building).where(Building.data_scope.is_(None)))
    if any(place.name not in expected_names for place in unrelated):
        raise ValueError("This database contains another campus. Use the dedicated uninav-campus.db.")
    result = import_dataset(database_session, dataset, adopt_legacy=True)
    return result.created_places, result.created_paths


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
