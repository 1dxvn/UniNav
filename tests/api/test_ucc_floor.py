from fastapi.testclient import TestClient
import pytest

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


@pytest.mark.parametrize("algorithm", ["a_star", "dijkstra"])
def test_real_floor_routes_keep_corners_and_confirmed_destinations(client: TestClient, user_headers: dict[str, str], algorithm: str) -> None:
    ids = load_campus()
    for name in ("ICETEX", "Morphology Laboratory", "Elevator and Restroom Hall", "Preclinic / Dentistry Coordination"):
        response = client.post("/routes/calculate", headers=user_headers, json={
            "origin_id": ids["Hall Acceso"], "destination_id": ids[name], "avoid": ["stairs"], "algorithm": algorithm,
        })
        assert response.status_code == 200
        route = response.json()
        assert route["path"][:3] == ["Hall Acceso", "Access courtyard", "South circulation"]
        assert route["path"][-1] == name
        assert len(route["steps"]) == len(route["path"]) - 1
        assert route["distance"] > 40
        reverse = client.post("/routes/calculate", headers=user_headers, json={
            "origin_id": ids[name], "destination_id": ids["Hall Acceso"], "avoid": ["stairs"], "algorithm": algorithm,
        })
        assert reverse.status_code == 200
        back = reverse.json()
        assert back["path"] == list(reversed(route["path"]))
        assert back["distance"] == pytest.approx(route["distance"])
        assert len(back["steps"]) == len(back["path"]) - 1


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


def test_isolated_test_destination_keeps_no_route_case(client: TestClient, user_headers: dict[str, str]) -> None:
    from models import Building

    ids = load_campus()
    # Synthetic destination exists only in conftest's temporary test database.
    with SessionLocal() as session:
        isolated = Building(name="Isolated test destination", x=70, y=0, floor=1)
        session.add(isolated)
        session.commit()
        isolated_id = isolated.id
    campus_graph_service.load_from_database()
    for origin, destination in ((ids["Hall Acceso"], isolated_id), (isolated_id, ids["Hall Acceso"])):
        response = client.post("/routes/calculate", headers=user_headers, json={
            "origin_id": origin, "destination_id": destination,
        })
        assert response.status_code == 404
        assert "no route" in response.json()["detail"].lower()
