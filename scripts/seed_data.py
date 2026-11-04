"""Sample campus used for development. It is NOT the real university."""
from __future__ import annotations


# name, x, y, floor, faculty, building_type
PLACES: list[tuple[str, float, float, int, str, str]] = [
    ("Main Entrance", 0, 0, 0, "Administration", "entrance"),
    ("Reception", 12, 0, 0, "Administration", "service"),
    ("Restrooms F0", 12, -12, 0, "Administration", "restroom"),
    ("Cafeteria", 40, 0, 0, "Administration", "dining"),
    ("Stairs F0", 25, 8, 0, "Administration", "stairs"),
    ("Elevator F0", 30, 8, 0, "Administration", "elevator"),
    ("Classroom 101", 10, 0, 1, "Engineering", "classroom"),
    ("Classroom 102", 20, 0, 1, "Engineering", "classroom"),
    ("Library", 40, 0, 1, "Humanities", "library"),
    ("Stairs F1", 25, 8, 1, "Administration", "stairs"),
    ("Elevator F1", 30, 8, 1, "Administration", "elevator"),
    ("Computer Lab", 15, 0, 2, "Engineering", "laboratory"),
    ("Physics Lab", 35, 0, 2, "Engineering", "laboratory"),
    ("Stairs F2", 25, 8, 2, "Administration", "stairs"),
    ("Elevator F2", 30, 8, 2, "Administration", "elevator"),
    ("Faculty Offices", 10, 0, 3, "Engineering", "office"),
    ("Auditorium", 30, -5, 3, "Humanities", "auditorium"),
    ("Stairs F3", 25, 8, 3, "Administration", "stairs"),
    ("Elevator F3", 30, 8, 3, "Administration", "elevator"),
    ("Terrace Lounge", 20, 0, 6, "Humanities", "terrace"),
    ("Stairs F6", 25, 8, 6, "Administration", "stairs"),
]

# source, target, kind, weight (None = straight-line distance)
PATHS: list[tuple[str, str, str, float | None]] = [
    ("Main Entrance", "Reception", "corridor", None),
    ("Reception", "Restrooms F0", "corridor", None),
    ("Reception", "Stairs F0", "corridor", None),
    ("Stairs F0", "Elevator F0", "corridor", None),
    ("Stairs F0", "Cafeteria", "corridor", None),
    ("Elevator F0", "Cafeteria", "corridor", None),
    ("Stairs F1", "Classroom 102", "corridor", None),
    ("Classroom 102", "Classroom 101", "corridor", None),
    ("Stairs F1", "Elevator F1", "corridor", None),
    ("Elevator F1", "Library", "corridor", None),
    ("Stairs F2", "Computer Lab", "corridor", None),
    ("Computer Lab", "Physics Lab", "corridor", None),
    ("Stairs F2", "Elevator F2", "corridor", None),
    ("Elevator F2", "Physics Lab", "corridor", None),
    ("Stairs F3", "Faculty Offices", "corridor", None),
    ("Stairs F3", "Elevator F3", "corridor", None),
    ("Elevator F3", "Auditorium", "corridor", None),
    ("Stairs F6", "Terrace Lounge", "corridor", None),
    ("Stairs F0", "Stairs F1", "stairs", 8),
    ("Stairs F1", "Stairs F2", "stairs", 8),
    ("Stairs F2", "Stairs F3", "stairs", 8),
    ("Stairs F3", "Stairs F6", "stairs", 24),
    ("Elevator F0", "Elevator F1", "elevator", 12),
    ("Elevator F1", "Elevator F2", "elevator", 12),
    ("Elevator F2", "Elevator F3", "elevator", 12),
]
