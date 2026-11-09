from __future__ import annotations

import threading

from data_structures.queue import Queue
from services.runtime_state import DurableState


class WaitingLines(DurableState):
    """One FIFO per place, with optional durable storage for the API worker."""

    def __init__(self) -> None:
        self._lines: dict[int, Queue[str]] = {}
        self._lock: threading.Lock = threading.Lock()

    def join(self, building_id: int, username: str) -> int | None:
        """Returns the 1-based position, or None if the user is already waiting."""
        with self._lock, self._mutation():
            line = self._lines.setdefault(building_id, Queue())
            if line.contains(username):
                return None
            line.enqueue(username)
            return line.size()

    def leave(self, building_id: int, username: str) -> bool:
        with self._lock, self._mutation():
            line = self._lines.get(building_id)
            return line is not None and line.remove(username)

    def position(self, building_id: int, username: str) -> int | None:
        with self._lock:
            line = self._lines.get(building_id)
            if line is None or not line.contains(username):
                return None
            return line.position_of(username) + 1

    def length(self, building_id: int) -> int:
        with self._lock:
            line = self._lines.get(building_id)
            return line.size() if line is not None else 0

    def serve_next(self, building_id: int) -> str | None:
        with self._lock, self._mutation():
            line = self._lines.get(building_id)
            if line is None or line.is_empty():
                return None
            return line.dequeue()

    def clear(self, building_id: int) -> None:
        with self._lock, self._mutation():
            self._lines.pop(building_id, None)

    def clear_all(self) -> None:
        with self._lock, self._mutation():
            self._lines.clear()

    def _dump(self) -> dict:
        return {str(building): line.to_list() for building, line in self._lines.items() if len(line)}

    def _restore(self, payload: dict) -> None:
        restored = {}
        for building, users in payload.items():
            line: Queue[str] = Queue()
            for user in users:
                line.enqueue(user)
            restored[int(building)] = line
        self._lines = restored


waiting_lines: WaitingLines = WaitingLines()
