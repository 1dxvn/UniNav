from fastapi.testclient import TestClient

from database import SessionLocal
from scripts.seed_ucc_floor1 import seed_campus
from services.campus_graph import campus_graph_service


def load_campus() -> dict[str, int]:
    from sqlalchemy import select
    from models import Building

    with SessionLocal() as session:
        assert seed_campus(session) == (16, 12)
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


def test_unconfirmed_preclinic_connection_returns_no_route(client: TestClient, user_headers: dict[str, str]) -> None:
    ids = load_campus()
    response = client.post("/routes/calculate", headers=user_headers, json={
        "origin_id": ids["Hall Acceso"], "destination_id": ids["Preclinic / Dentistry Coordination"],
    })
    assert response.status_code == 404
    assert "There is no route" in response.json()["detail"]
