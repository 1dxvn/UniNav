from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config import ROLE_USER
from database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ROLE_USER, server_default=ROLE_USER
    )
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
    floor: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    faculty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    building_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"Building(id={self.id}, name={self.name!r}, x={self.x}, y={self.y})"


class CampusPath(Base):
    __tablename__ = "paths"
    __table_args__ = (
        CheckConstraint("weight IS NULL OR weight >= 0", name="check_path_weight_non_negative"),
        CheckConstraint("source_id != target_id", name="check_path_distinct_endpoints"),
        UniqueConstraint("source_id", "target_id", name="uq_path_endpoints"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bidirectional: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False, default="corridor", server_default="corridor"
    )

    source: Mapped[Building] = relationship(foreign_keys=[source_id])
    target: Mapped[Building] = relationship(foreign_keys=[target_id])

    def __repr__(self) -> str:
        return (
            f"CampusPath(id={self.id}, source_id={self.source_id}, "
            f"target_id={self.target_id}, weight={self.weight})"
        )


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
