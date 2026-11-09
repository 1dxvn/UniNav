"""Persist the existing FIFO/linked-list services without replacing their algorithms.

One backend worker owns these structures. Each mutation writes an atomic snapshot
while holding the structure's lock, and rolls memory back if storage fails.
Databases are isolated through the injected SQLAlchemy session factory.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy.orm import Session, sessionmaker

from database import SessionLocal
from models import RuntimeState


class SnapshotStore:
    def __init__(self, namespace: str, factory: sessionmaker[Session] = SessionLocal) -> None:
        self.namespace = namespace
        self.factory = factory

    def load(self) -> dict[str, Any]:
        with self.factory() as db:
            row = db.get(RuntimeState, self.namespace)
            if row is None:
                return {}
            if row.schema_version != 1:
                raise ValueError(f"Unsupported runtime-state schema for {self.namespace}")
            payload = json.loads(row.payload)
            if not isinstance(payload, dict):
                raise ValueError(f"Invalid runtime state for {self.namespace}")
            return payload

    def save(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with self.factory.begin() as db:
            row = db.get(RuntimeState, self.namespace)
            if row is None:
                db.add(RuntimeState(namespace=self.namespace, schema_version=1, payload=encoded))
            else:
                row.payload = encoded


class DurableState:
    _store: SnapshotStore | None = None

    def attach_store(self, store: SnapshotStore | None) -> None:
        with self._lock:
            if store is not None:
                self._restore(store.load())
            self._store = store

    def _dump(self) -> dict[str, Any]:
        raise NotImplementedError

    def _restore(self, payload: dict[str, Any]) -> None:
        raise NotImplementedError

    @contextmanager
    def _mutation(self) -> Iterator[None]:
        previous = self._dump() if self._store is not None else None
        try:
            yield
            if self._store is not None:
                current = self._dump()
                if current != previous:
                    self._store.save(current)
        except Exception:
            if previous is not None:
                self._restore(previous)
            raise


def attach_runtime_stores() -> None:
    from services.navigation_history import navigation_histories
    from services.tour_sessions import tour_sessions
    from services.waiting_lines import waiting_lines

    for namespace, service in (("queues", waiting_lines), ("navigation", navigation_histories), ("tour-sessions", tour_sessions)):
        service.attach_store(SnapshotStore(namespace))


def detach_runtime_stores() -> None:
    from services.navigation_history import navigation_histories
    from services.tour_sessions import tour_sessions
    from services.waiting_lines import waiting_lines

    for service in (waiting_lines, navigation_histories, tour_sessions):
        service.attach_store(None)
