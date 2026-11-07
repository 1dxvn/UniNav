from __future__ import annotations

import copy
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from database import SessionLocal
from models import Building, CampusPath, RouteVisit
from schemas.datasets import CampusDataset
from scripts.campus_profiles import Profile, load_profile, seed_profile
from services.campus_graph import campus_graph_service
from services.datasets import import_dataset

DATASET = Path(__file__).resolve().parents[2] / "data/datasets/ucc-floors-4-5.json"
DESTINATIONS = {
    "ucc:f45:classroom-420-entrance": (4, "D27"), "ucc:f45:classroom-421-entrance": (4, "D26"), "ucc:f45:classroom-422-entrance": (4, "D28"),
    "ucc:f45:classroom-512-entrance": (5, "D18"), "ucc:f45:classroom-513-entrance": (5, "D19"), "ucc:f45:classroom-515-entrance": (5, "D11"),
}
A = {3: 9.87, 4: 13.37, 5: 16.87}


def load() -> dict[str, int]:
    with SessionLocal() as session:
        result = seed_profile(session, load_profile("ucc-six-floors-c18"))
        assert (result["places"], result["paths"]) == (235, 218)
        session.commit()
        ids = {p.code: p.id for p in session.scalars(select(Building))}
    campus_graph_service.load_from_database()
    return ids


def test_upper_floors_upgrade_preserves_ids_paths_and_history(client: TestClient, user_headers: dict[str, str]) -> None:
    with SessionLocal() as session:
        seed_profile(session, load_profile("ucc-four-floors-c18")); session.commit()
        old_places = {p.code: p.id for p in session.scalars(select(Building))}
        old_paths = {p.code: (p.id, p.source_id, p.target_id, p.kind) for p in session.scalars(select(CampusPath))}
    campus_graph_service.load_from_database()
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": old_places["ucc:floor1:p01"], "destination_id": old_places["ucc:f0:waiting-room"]}).status_code == 200
    with SessionLocal() as session:
        visits = [v.id for v in session.scalars(select(RouteVisit))]
        result = seed_profile(session, load_profile("ucc-six-floors-c18")); session.commit()
        assert (result["created_places"], result["created_paths"]) == (85, 79)
        assert {p.code: p.id for p in session.scalars(select(Building)) if p.code in old_places} == old_places
        assert {p.code: (p.id, p.source_id, p.target_id, p.kind) for p in session.scalars(select(CampusPath)) if p.code in old_paths} == old_paths
        assert [v.id for v in session.scalars(select(RouteVisit))] == visits
        repeated = seed_profile(session, load_profile("ucc-six-floors-c18"))
        assert repeated["created_places"] == repeated["created_paths"] == 0


@pytest.mark.parametrize("algorithm", ["a_star", "dijkstra"])
def test_upper_classrooms_round_trip_over_each_tower_flight(client: TestClient, user_headers: dict[str, str], algorithm: str) -> None:
    ids = load()
    for code, (floor, door) in DESTINATIONS.items():
        for origin, destination in ((ids["ucc:floor1:p01"], ids[code]), (ids[code], ids["ucc:floor1:p01"])):
            response = client.post("/routes/calculate", headers=user_headers, json={"origin_id": origin, "destination_id": destination, "algorithm": algorithm})
            assert response.status_code == 200, response.text
            route = response.json()
            assert route["waypoints"][0]["id"] == origin and route["waypoints"][-1]["id"] == destination
            assert f"Floor {floor} {door} doorway centre" in route["path"]
            for lo in range(3, floor):
                flight = [w for w in route["waypoints"] if w["code"].startswith(f"ucc:f45:east-stair-{lo}{lo + 1}-")]
                assert len(flight) == 25
                assert all(w["floor"] == (lo + 1 if w["code"].endswith("24") else lo) for w in flight)
            assert all(abs(w["elevation_m"] - A[floor]) < 1e-6 for w in route["waypoints"] if w["floor"] == floor and "east-stair" not in w["code"])
            assert all(s["connection_code"] and s["path_id"] for s in route["steps"])


@pytest.mark.parametrize("code", ["ucc:f45:classroom-420-entrance", "ucc:f45:classroom-512-entrance"])
def test_no_invented_step_free_access_to_upper_floors(client: TestClient, user_headers: dict[str, str], code: str) -> None:
    ids = load()
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:floor1:p01"], "destination_id": ids[code], "avoid": ["stairs"]}).status_code == 404
    response = client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:f45:classroom-420-entrance"], "destination_id": ids["ucc:f45:classroom-422-entrance"], "avoid": ["stairs"]})
    assert response.status_code == 200 and all(s["kind"] != "stairs" for s in response.json()["steps"])


def test_upper_scope_needs_existing_floor3_and_fails_atomically(client: TestClient) -> None:
    data = CampusDataset.model_validate_json(DATASET.read_bytes())
    with SessionLocal() as session:
        with pytest.raises(ValueError, match="Unknown endpoint"):
            import_dataset(session, data)
        assert list(session.scalars(select(Building))) == list(session.scalars(select(CampusPath))) == []
        seed_profile(session, load_profile("ucc-four-floors-c18")); session.commit()
        before = [(p.id, p.code) for p in session.scalars(select(Building))]
        profile = load_profile("ucc-six-floors-c18")
        bad = copy.deepcopy(profile.datasets[-1]); bad.paths[-1].target_code = "test:missing"
        broken = Profile(profile.id, (*profile.datasets[:-1], bad), profile.generations, profile.selected_generations, profile.known_scopes)
        with pytest.raises(ValueError, match="Unknown endpoint"):
            seed_profile(session, broken)
        assert [(p.id, p.code) for p in session.scalars(select(Building))] == before
        assert len(list(session.scalars(select(CampusPath)))) == 139


@pytest.mark.parametrize("floor,datum", [(4, 12.32), (5, 15.26)])
def test_upper_anchors_stay_isolated_at_their_b_datum(client: TestClient, user_headers: dict[str, str], floor: int, datum: float) -> None:
    ids = load()
    for n in (1, 2, 3):
        code = f"ucc:f45:f{floor}-reference-{n}"
        with SessionLocal() as session:
            point = session.get(Building, ids[code])
            assert point.elevation_m == datum and point.building_type == "reference" and point.floor == floor
        assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:floor1:p01"], "destination_id": ids[code]}).status_code == 404
