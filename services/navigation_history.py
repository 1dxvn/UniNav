from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import NamedTuple, Optional

from data_structures.doubly_linked_list import DoublyLinkedList, DoublyNode
from services.runtime_state import DurableState

MAX_TRAIL_LENGTH: int = 50


class NavStop(NamedTuple):
    building_id: int
    building_name: str
    floor: int


@dataclass
class NavigationTrail:
    """Places a user has been to, with a cursor marking where they are now."""

    places: DoublyLinkedList[NavStop] = field(default_factory=DoublyLinkedList)
    cursor: Optional[DoublyNode[NavStop]] = None

    @property
    def current(self) -> Optional[NavStop]:
        return self.cursor.value if self.cursor is not None else None

    @property
    def can_go_back(self) -> bool:
        return self.cursor is not None and self.cursor.previous is not None

    @property
    def can_go_forward(self) -> bool:
        return self.cursor is not None and self.cursor.next is not None

    def entries(self) -> list[tuple[NavStop, bool]]:
        found: list[tuple[NavStop, bool]] = []
        node = self.places.head
        while node is not None:
            found.append((node.value, node is self.cursor))
            node = node.next
        return found


class NavigationHistories(DurableState):
    """Back and forward navigation per user, like the history of a web browser."""

    def __init__(self) -> None:
        self._trails: dict[str, NavigationTrail] = {}
        self._lock: threading.Lock = threading.Lock()

    def visit(self, username: str, stop: NavStop) -> NavigationTrail:
        with self._lock, self._mutation():
            trail = self._trails.setdefault(username, NavigationTrail())
            if trail.current is not None and trail.current.building_id == stop.building_id:
                return trail
            if trail.cursor is not None:
                trail.places.truncate_after(trail.cursor)
            trail.cursor = trail.places.append(stop)
            while len(trail.places) > MAX_TRAIL_LENGTH:
                trail.places.pop_front()
            return trail

    def get(self, username: str) -> NavigationTrail:
        with self._lock:
            return self._trails.setdefault(username, NavigationTrail())

    def go_back(self, username: str) -> Optional[NavigationTrail]:
        with self._lock, self._mutation():
            trail = self._trails.setdefault(username, NavigationTrail())
            if not trail.can_go_back:
                return None
            trail.cursor = trail.cursor.previous
            return trail

    def go_forward(self, username: str) -> Optional[NavigationTrail]:
        with self._lock, self._mutation():
            trail = self._trails.setdefault(username, NavigationTrail())
            if not trail.can_go_forward:
                return None
            trail.cursor = trail.cursor.next
            return trail

    def clear(self, username: str) -> None:
        with self._lock, self._mutation():
            self._trails.pop(username, None)

    def clear_all(self) -> None:
        with self._lock, self._mutation():
            self._trails.clear()

    def _dump(self) -> dict:
        return {name: {"entries": [[list(stop), current] for stop, current in trail.entries()]}
                for name, trail in self._trails.items() if trail.current is not None}

    def _restore(self, payload: dict) -> None:
        restored = {}
        for name, record in payload.items():
            trail = NavigationTrail()
            for stop, current in record["entries"]:
                node = trail.places.append(NavStop(*stop))
                if current:
                    trail.cursor = node
            restored[name] = trail
        self._trails = restored


navigation_histories: NavigationHistories = NavigationHistories()
