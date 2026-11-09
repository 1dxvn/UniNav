"""Loads the sample campus and two demo users. Safe to run more than once.

Usage: python -m scripts.seed
"""
from __future__ import annotations

import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import ROLE_ADMIN, ROLE_USER
from database import SessionLocal, init_db
from models import Building, CampusPath, User
from scripts.seed_data import PATHS, PLACES
from security.passwords import hash_password

DEMO_PASSWORD: str = "demo1234"


def seed_users(database_session: Session) -> None:
    admin_password = os.getenv("UNINAV_ADMIN_PASSWORD") or DEMO_PASSWORD
    for username, role, password in (
        ("admin", ROLE_ADMIN, admin_password),
        ("student", ROLE_USER, DEMO_PASSWORD),
    ):
        if database_session.scalar(select(User.id).where(User.username == username)) is None:
            database_session.add(
                User(username=username, password_hash=hash_password(password), role=role)
            )


def seed_buildings(database_session: Session) -> tuple[dict[str, Building], int]:
    existing = {b.name: b for b in database_session.scalars(select(Building))}
    created = 0
    for name, x, y, floor, faculty, building_type in PLACES:
        if name not in existing:
            building = Building(
                name=name, x=x, y=y, floor=floor, faculty=faculty, building_type=building_type
            )
            database_session.add(building)
            existing[name] = building
            created += 1
    database_session.flush()
    return existing, created


def seed_paths(database_session: Session, buildings: dict[str, Building]) -> int:
    connected = {
        frozenset((path.source_id, path.target_id))
        for path in database_session.scalars(select(CampusPath))
    }
    created = 0
    for source, target, kind, weight in PATHS:
        pair = frozenset((buildings[source].id, buildings[target].id))
        if pair in connected:
            continue
        database_session.add(
            CampusPath(
                source_id=buildings[source].id,
                target_id=buildings[target].id,
                kind=kind,
                weight=weight,
            )
        )
        connected.add(pair)
        created += 1
    return created


def main() -> None:
    init_db()
    with SessionLocal() as database_session:
        seed_users(database_session)
        buildings, created_places = seed_buildings(database_session)
        created_paths = seed_paths(database_session, buildings)
        database_session.commit()
    print(f"Created {created_places} places and {created_paths} paths.")
    print(f"Users: admin / student (password: {DEMO_PASSWORD} unless UNINAV_ADMIN_PASSWORD is set).")


if __name__ == "__main__":
    main()
