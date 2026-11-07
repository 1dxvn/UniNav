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

DATASET = Path(__file__).resolve().parents[2] / "data/datasets/ucc-third-floor.json"
DESTINATIONS = tuple(f"ucc:f3:computer-lab-{n}-entrance" for n in (1, 2, 3))


def load() -> dict[str, int]:
    with SessionLocal() as session:
        result = seed_profile(session, load_profile("ucc-three-floors-c16"))
        assert (result["places"], result["paths"]) == (110, 102)
        session.commit()
        ids = {p.code: p.id for p in session.scalars(select(Building))}
    campus_graph_service.load_from_database()
    return ids


def test_third_floor_upgrade_preserves_ids_paths_and_history(client: TestClient, user_headers: dict[str, str]) -> None:
    with SessionLocal() as session:
        seed_profile(session, load_profile("ucc-two-floors-c15")); session.commit()
        old_places = {p.code: p.id for p in session.scalars(select(Building))}
        old_paths = {p.code: (p.id, p.source_id, p.target_id, p.kind) for p in session.scalars(select(CampusPath))}
    campus_graph_service.load_from_database()
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": old_places["ucc:floor1:p01"], "destination_id": old_places["ucc:floor1:p06"]}).status_code == 200
    with SessionLocal() as session:
        visits = [v.id for v in session.scalars(select(RouteVisit))]
        result = seed_profile(session, load_profile("ucc-three-floors-c16")); session.commit()
        assert (result["created_places"], result["created_paths"]) == (42, 39)
        assert {p.code: p.id for p in session.scalars(select(Building)) if p.code in old_places} == old_places
        assert {p.code: (p.id, p.source_id, p.target_id, p.kind) for p in session.scalars(select(CampusPath)) if p.code in old_paths} == old_paths
        assert [v.id for v in session.scalars(select(RouteVisit))] == visits
        repeated = seed_profile(session, load_profile("ucc-three-floors-c16"))
        assert repeated["created_places"] == repeated["created_paths"] == 0


@pytest.mark.parametrize("algorithm", ["a_star", "dijkstra"])
def test_three_labs_round_trip_keep_doors_both_stairs_and_explicit_floors(client: TestClient, user_headers: dict[str, str], algorithm: str) -> None:
    ids = load()
    for code, door in zip(DESTINATIONS, ("D15", "D14", "D13"), strict=True):
        for origin, destination in ((ids["ucc:floor1:p01"], ids[code]), (ids[code], ids["ucc:floor1:p01"])):
            response = client.post("/routes/calculate", headers=user_headers, json={"origin_id": origin, "destination_id": destination, "algorithm": algorithm})
            assert response.status_code == 200, response.text
            route = response.json()
            assert route["waypoints"][0]["id"] == origin and route["waypoints"][-1]["id"] == destination
            assert f"Floor 3 {door} doorway centre" in route["path"]
            assert "Third-floor stair approach on floor 2" in route["path"]
            assert any(w["code"].startswith("ucc:f2:east-stair-") for w in route["waypoints"])
            upper = [w for w in route["waypoints"] if w["code"].startswith("ucc:f3:east-stair-")]
            assert len(upper) == 25
            assert all(w["floor"] == (3 if w["code"].endswith("24") else 2) for w in upper)
            assert any(w["floor"] == 2 and w["elevation_m"] > 9.38 for w in upper)
            assert all(w["elevation_m"] == 9.87 for w in route["waypoints"] if w["floor"] == 3)
            assert all(s["connection_code"] and s["path_id"] for s in route["steps"])


@pytest.mark.parametrize("code", DESTINATIONS)
def test_no_invented_step_free_access_to_floor3(client: TestClient, user_headers: dict[str, str], code: str) -> None:
    ids = load()
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:floor1:p01"], "destination_id": ids[code], "avoid": ["stairs"]}).status_code == 404
    response = client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids[DESTINATIONS[0]], "destination_id": ids[DESTINATIONS[1]], "avoid": ["stairs"]})
    assert response.status_code == 200 and all(s["kind"] != "stairs" for s in response.json()["steps"])


def test_new_scope_needs_existing_floor2_and_fails_atomically(client: TestClient) -> None:
    data = CampusDataset.model_validate_json(DATASET.read_bytes())
    with SessionLocal() as session:
        with pytest.raises(ValueError, match="Unknown endpoint"):
            import_dataset(session, data)
        assert list(session.scalars(select(Building))) == list(session.scalars(select(CampusPath))) == []
        seed_profile(session, load_profile("ucc-two-floors-c15")); session.commit()
        before = [(p.id, p.code) for p in session.scalars(select(Building))]
        profile = load_profile("ucc-three-floors-c16")
        bad = copy.deepcopy(profile.datasets[-1]); bad.paths[-1].target_code = "test:missing"
        broken = Profile(profile.id, (*profile.datasets[:-1], bad), profile.generations, profile.selected_generations, profile.known_scopes)
        with pytest.raises(ValueError, match="Unknown endpoint"):
            seed_profile(session, broken)
        assert [(p.id, p.code) for p in session.scalars(select(Building))] == before
        assert len(list(session.scalars(select(CampusPath)))) == 63


def test_structural_anchors_remain_isolated_at_b_datum(client: TestClient, user_headers: dict[str, str]) -> None:
    ids = load()
    for n in (1, 2, 3):
        code = f"ucc:f3:reference-{n}"
        with SessionLocal() as session:
            point = session.get(Building, ids[code])
            assert point.elevation_m == 9.38 and point.building_type == "reference"
        assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:floor1:p01"], "destination_id": ids[code]}).status_code == 404
