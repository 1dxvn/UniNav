"""Import an explicit dataset into an explicit DB, without deleting other scopes."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    os.environ["UNINAV_DATABASE_URL"] = f"sqlite:///{args.database.resolve().as_posix()}"
    from database import SessionLocal, init_db
    from schemas.datasets import CampusDataset
    from services.datasets import import_dataset

    dataset = CampusDataset.model_validate_json(args.dataset.read_text(encoding="utf-8"))
    init_db()
    with SessionLocal() as session:
        result = import_dataset(session, dataset)
        session.commit()
    print(result.model_dump_json())


if __name__ == "__main__":
    main()
