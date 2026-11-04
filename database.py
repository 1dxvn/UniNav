from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

PROJECT_DIRECTORY: Path = Path(__file__).resolve().parent
DATABASE_PATH: Path = PROJECT_DIRECTORY / "uninav.db"
DATABASE_URL: str = f"sqlite:///{DATABASE_PATH.as_posix()}"

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
