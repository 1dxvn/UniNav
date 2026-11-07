"""Seed a reviewed campus profile; keeps the sample DB and other scoped blocks."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import sys

from scripts.campus_profiles import ROOT, load_profile, profile_ids, seed_profile

SAMPLE_DATABASE = ROOT / "uninav.db"
CAMPUS_DATABASE = ROOT / "uninav-campus.db"
CAMPUS_SERVICE_PORT = 8001


def campus_service_running() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", CAMPUS_SERVICE_PORT), timeout=0.3):
            return True
    except OSError:
        return False


def configure_database(path: Path | None) -> Path:
    from sqlalchemy.engine import make_url

    raw = f"sqlite:///{path.resolve().as_posix()}" if path is not None else os.getenv("UNINAV_DATABASE_URL", f"sqlite:///{(ROOT / 'uninav-campus.db').as_posix()}")
    url = make_url(raw)
    if url.drivername != "sqlite" or not url.database or url.database == ":memory:" or url.query:
        raise ValueError("Campus startup needs a SQLite database file.")
    target = Path(url.database).resolve()
    if target == SAMPLE_DATABASE.resolve() or (target.exists() and SAMPLE_DATABASE.exists() and target.samefile(SAMPLE_DATABASE)):
        raise ValueError("The sample uninav.db is protected. Use uninav-campus.db or a separate rehearsal database.")
    if target == CAMPUS_DATABASE.resolve() and campus_service_running():
        raise ValueError("The existing 8001 service may hold this campus database. Leave it running and use a separate rehearsal database.")
    normalized = f"sqlite:///{target.as_posix()}"
    loaded = sys.modules.get("database")
    if loaded is not None and loaded.DATABASE_URL != normalized:
        raise ValueError("Database module is already loaded for a different URL. Start a fresh process.")
    os.environ["UNINAV_DATABASE_URL"] = normalized
    return target


def seed_database(profile_id: str, path: Path | None = None) -> dict:
    target = configure_database(path)
    profile = load_profile(profile_id)  # Validate pinned inputs before creating tables.
    from database import SessionLocal, init_db
    from scripts.seed import seed_users

    init_db()
    with SessionLocal() as session:
        report = seed_profile(session, profile)
        seed_users(session)
        session.commit()
    return {**report, "database": str(target)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=profile_ids(), default="base")
    parser.add_argument("--database", type=Path, help="Dedicated SQLite file; the sample uninav.db is protected.")
    args = parser.parse_args()
    try:
        report = seed_database(args.profile, args.database)
    except ValueError as error:
        parser.error(str(error))
    print("UNINAV_CAMPUS_SEEDED=" + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
