from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from passlib.context import CryptContext
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

BACKEND_DIRECTORY: Path = Path(__file__).resolve().parent
DATABASE_PATH: Path = BACKEND_DIRECTORY / "uninav.db"
DATABASE_URL: str = f"sqlite:///{DATABASE_PATH.as_posix()}"

BCRYPT_MAX_PASSWORD_BYTES: int = 72

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

password_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    route_visits: Mapped[list[RouteVisit]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username!r})"


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    faculty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    building_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"Building(id={self.id}, name={self.name!r}, x={self.x}, y={self.y})"


class RouteVisit(Base):
    __tablename__ = "route_visits"
    __table_args__ = (
        CheckConstraint("distance >= 0", name="check_route_visit_distance_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    origin_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
    )
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
    )
    distance: Mapped[float] = mapped_column(Float, nullable=False)
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="route_visits")
    origin: Mapped[Building] = relationship(foreign_keys=[origin_id])
    destination: Mapped[Building] = relationship(foreign_keys=[destination_id])

    def __repr__(self) -> str:
        return (
            f"RouteVisit(id={self.id}, user_id={self.user_id}, "
            f"origin_id={self.origin_id}, destination_id={self.destination_id}, "
            f"distance={self.distance})"
        )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close()


def hash_password(plain: str) -> str:
    if not plain:
        raise ValueError("Password cannot be empty.")
    if len(plain.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"Password cannot exceed {BCRYPT_MAX_PASSWORD_BYTES} bytes.")
    return password_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return password_context.verify(plain, hashed)
    except (ValueError, TypeError):
        return False


if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully at: {DATABASE_PATH}")
    print(f"Tables: {', '.join(Base.metadata.tables)}")