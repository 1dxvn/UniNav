from fastapi.testclient import TestClient

from database import SessionLocal
from scripts.seed_ucc_floor1 import seed_campus
from services.campus_graph import campus_graph_service


def load_campus() -> dict[str, int]:
    from sqlalchemy import select
    from models import Building

    with SessionLocal() as session:
        assert seed_campus(session) == (19, 16)
        session.commit()
        assert seed_campus(session) == (0, 0)
        ids = {place.name: place.id for place in session.scalars(select(Building))}
    campus_graph_service.load_from_database()
    return ids


def test_real_floor_routes_keep_corners_and_confirmed_destinations(client: TestClient, user_headers: dict[str, str]) -> None:
    ids = load_campus()
    for name in ("ICETEX", "Morphology Laboratory", "Elevator and Restroom Hall"):
        response = client.post("/routes/calculate", headers=user_headers, json={
            "origin_id": ids["Hall Acceso"], "destination_id": ids[name], "avoid": ["stairs"],
        })
        assert response.status_code == 200
        route = response.json()
        assert route["path"][:3] == ["Hall Acceso", "Access courtyard", "South circulation"]
        assert route["path"][-1] == name
        assert len(route["steps"]) == len(route["path"]) - 1
        assert route["distance"] > 40


def test_preclinic_is_reached_through_north_circulation_and_storeroom(client: TestClient, user_headers: dict[str, str]) -> None:
    ids = load_campus()
    response = client.post("/routes/calculate", headers=user_headers, json={
        "origin_id": ids["Hall Acceso"], "destination_id": ids["Preclinic / Dentistry Coordination"], "avoid": ["stairs"],
    })
    assert response.status_code == 200
    route = response.json()
    assert route["path"][-5:] == [
        "Elevator and Restroom Hall", "North circulation west", "North circulation east",
        "Preclinic storeroom", "Preclinic / Dentistry Coordination",
    ]
    assert len(route["steps"]) == len(route["path"]) - 1
