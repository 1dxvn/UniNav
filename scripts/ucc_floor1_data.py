"""Confirmed Bloque B first-floor places, in plan metres relative to Hall Acceso.

Source: UniNav-Frontend/public/models/campus-reference.md and the exported GLB.
Corridor waypoints were checked against the GLB at body height with 0.38 m
clearance. The Preclinic is reached from the north circulation through the
PRECLINICA ALMACEN room and its east doorway, as drawn in the DWG.
"""
from __future__ import annotations

# name, x, y, floor, faculty, building_type
PLACES: list[tuple[str, float, float, int, str, str]] = [
    ("Hall Acceso", 0, 0, 1, "Administration", "entrance"),
    ("Access courtyard", 6, 16.5, 1, "Administration", "waypoint"),
    ("South circulation", 21.5, 33.5, 1, "Administration", "waypoint"),
    ("ICETEX approach", 23, 34, 1, "Administration", "waypoint"),
    ("ICETEX doorway", 23.5, 36, 1, "Administration", "waypoint"),
    ("ICETEX", 24.55, 41.78, 1, "Administration", "service"),
    ("Hall junction", 24, 36.5, 1, "Administration", "waypoint"),
    ("Hall corridor south", 28, 36.5, 1, "Administration", "waypoint"),
    ("Hall corridor north", 28, 48, 1, "Administration", "waypoint"),
    ("Elevator and Restroom Hall", 25.77, 51.97, 1, "Administration", "service"),
    ("Laboratory corridor west", 41.5, 33.5, 1, "Health Sciences", "waypoint"),
    ("Laboratory corridor east", 46.5, 32, 1, "Health Sciences", "waypoint"),
    ("Morphology Laboratory", 42.96, 27.77, 1, "Health Sciences", "laboratory"),
    ("Preclinic / Dentistry Coordination", 56.84, 51.96, 1, "Health Sciences", "clinic"),
    ("North circulation west", 32, 54.4, 1, "Health Sciences", "waypoint"),
    ("North circulation east", 58.26, 54.7, 1, "Health Sciences", "waypoint"),
    ("Preclinic storeroom", 58.26, 51.68, 1, "Health Sciences", "waypoint"),
    ("ICETEX column reference", 27.26, 41.77, 1, "Administration", "reference"),
    ("Lockers column reference", 46.97, 36.94, 1, "Administration", "reference"),
]

# Edges are straight; preserve each doorway and turn. No runtime client routing.
PATHS: list[tuple[str, str, str]] = [
    ("Hall Acceso", "Access courtyard", "outdoor"),
    ("Access courtyard", "South circulation", "outdoor"),
    ("South circulation", "ICETEX approach", "corridor"),
    ("ICETEX approach", "ICETEX doorway", "corridor"),
    ("ICETEX doorway", "ICETEX", "corridor"),
    ("ICETEX doorway", "Hall junction", "corridor"),
    ("Hall junction", "Hall corridor south", "corridor"),
    ("Hall corridor south", "Hall corridor north", "corridor"),
    ("Hall corridor north", "Elevator and Restroom Hall", "corridor"),
    ("South circulation", "Laboratory corridor west", "corridor"),
    ("Laboratory corridor west", "Laboratory corridor east", "corridor"),
    ("Laboratory corridor east", "Morphology Laboratory", "corridor"),
    ("Elevator and Restroom Hall", "North circulation west", "corridor"),
    ("North circulation west", "North circulation east", "corridor"),
    ("North circulation east", "Preclinic storeroom", "corridor"),
    ("Preclinic storeroom", "Preclinic / Dentistry Coordination", "corridor"),
]
