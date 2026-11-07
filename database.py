from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

PROJECT_DIRECTORY: Path = Path(__file__).resolve().parent
DATABASE_PATH: Path = PROJECT_DIRECTORY / "uninav.db"
DATABASE_URL: str = os.getenv("UNINAV_DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db() -> None:
    import models  # noqa: F401  (registers the tables on Base.metadata)

    Base.metadata.create_all(bind=engine)
    apply_column_migrations()


COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    ("buildings", "floor", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "role", "VARCHAR(20) NOT NULL DEFAULT 'user'"),
    ("paths", "kind", "VARCHAR(20) NOT NULL DEFAULT 'corridor'"),
    ("buildings", "code", "VARCHAR(128)"),
    ("buildings", "display_name", "VARCHAR(100)"),
    ("buildings", "block_code", "VARCHAR(32)"),
    ("buildings", "floor_code", "VARCHAR(64)"),
    ("buildings", "elevation_m", "FLOAT"),
    ("buildings", "elevation_source", "VARCHAR(1000)"),
    ("buildings", "data_scope", "VARCHAR(128)"),
    ("paths", "code", "VARCHAR(128)"),
    ("paths", "data_scope", "VARCHAR(128)"),
]


def apply_column_migrations() -> None:
    """Adds columns introduced after a database was first created."""
    with engine.begin() as connection:
        for table, column, definition in COLUMN_MIGRATIONS:
            columns = {row[1] for row in connection.exec_driver_sql(f"PRAGMA table_info({table})")}
            if columns and column not in columns:
                connection.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        # Additive migration: preserve row IDs, FK relationships, coordinates and
        # histories. Source datasets can explicitly adopt these legacy codes later.
        for table, prefix in (("buildings", "legacy-place"), ("paths", "legacy-path")):
            connection.exec_driver_sql(f"UPDATE {table} SET code = '{prefix}:' || id WHERE code IS NULL")
            connection.exec_driver_sql(f"CREATE UNIQUE INDEX IF NOT EXISTS ix_{table}_code ON {table} (code)")
            connection.exec_driver_sql(f"CREATE INDEX IF NOT EXISTS ix_{table}_data_scope ON {table} (data_scope)")


def get_db() -> Iterator[Session]:
    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully at: {DATABASE_PATH}")
    print(f"Tables: {', '.join(Base.metadata.tables)}")
