from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import NamedTuple

from data_structures.circular_doubly_linked_list import CircularDoublyLinkedList
from services.runtime_state import DurableState


class SessionStop(NamedTuple):
    position: int
    building_id: int
    building_name: str
    floor: int


@dataclass
class TourSession:
    tour_id: int
    tour_name: str
    stops: CircularDoublyLinkedList[SessionStop]

    @property
    def current_stop(self) -> SessionStop:
        return self.stops.current

    @property
    def total_stops(self) -> int:
        return self.stops.size()


class TourSessions(DurableState):
    """The tour each user is currently walking. The stops form a circle."""

    def __init__(self) -> None:
        self._sessions: dict[str, TourSession] = {}
        self._lock: threading.Lock = threading.Lock()

    def start(
        self, username: str, tour_id: int, tour_name: str, stops: list[SessionStop]
    ) -> TourSession:
        circle: CircularDoublyLinkedList[SessionStop] = CircularDoublyLinkedList()
        for stop in stops:
            circle.append(stop)
        session = TourSession(tour_id, tour_name, circle)
        with self._lock, self._mutation():
            self._sessions[username] = session
        return session

    def get(self, username: str) -> TourSession | None:
        with self._lock:
            return self._sessions.get(username)

    def advance(self, username: str) -> TourSession | None:
        with self._lock, self._mutation():
            session = self._sessions.get(username)
            if session is not None:
                session.stops.next()
            return session

    def go_back(self, username: str) -> TourSession | None:
        with self._lock, self._mutation():
            session = self._sessions.get(username)
            if session is not None:
                session.stops.previous()
            return session

    def end(self, username: str) -> bool:
        with self._lock, self._mutation():
            return self._sessions.pop(username, None) is not None

    def end_all_for_tour(self, tour_id: int) -> None:
        with self._lock, self._mutation():
            ended = [name for name, s in self._sessions.items() if s.tour_id == tour_id]
            for username in ended:
                del self._sessions[username]

    def clear_all(self) -> None:
        with self._lock, self._mutation():
            self._sessions.clear()

    def _dump(self) -> dict:
        return {name: {"tour_id": session.tour_id, "tour_name": session.tour_name,
            "stops": [list(stop) for stop in session.stops], "current": session.current_stop.position}
            for name, session in self._sessions.items()}

    def _restore(self, payload: dict) -> None:
        restored = {}
        for name, record in payload.items():
            circle: CircularDoublyLinkedList[SessionStop] = CircularDoublyLinkedList()
            for stop in record["stops"]:
                circle.append(SessionStop(*stop))
            for stop in circle:
                if stop.position == record["current"]:
                    circle.move_to(stop)
                    break
            restored[name] = TourSession(record["tour_id"], record["tour_name"], circle)
        self._sessions = restored


tour_sessions: TourSessions = TourSessions()
