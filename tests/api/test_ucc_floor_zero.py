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

DATASET = Path(__file__).resolve().parents[2] / "data/datasets/ucc-floor-zero.json"
DESTINATIONS = {
    "ucc:f0:simulation-lab-entrance": "Floor 0 D32 doorway centre",
    "ucc:f0:waiting-room": "Floor 0 facade sliding door",
}
A0, A1, B0 = -0.63, 2.87, 0.56


def load() -> dict[str, int]:
    with SessionLocal() as session:
        result = seed_profile(session, load_profile("ucc-four-floors-c18"))
        assert (result["places"], result["paths"]) == (150, 139)
        session.commit()
        ids = {p.code: p.id for p in session.scalars(select(Building))}
    campus_graph_service.load_from_database()
    return ids


def test_floor_zero_upgrade_preserves_ids_paths_and_history(client: TestClient, user_headers: dict[str, str]) -> None:
    with SessionLocal() as session:
        seed_profile(session, load_profile("ucc-three-floors-c16")); session.commit()
        old_places = {p.code: p.id for p in session.scalars(select(Building))}
        old_paths = {p.code: (p.id, p.source_id, p.target_id, p.kind) for p in session.scalars(select(CampusPath))}
    campus_graph_service.load_from_database()
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": old_places["ucc:floor1:p01"], "destination_id": old_places["ucc:floor1:p06"]}).status_code == 200
    with SessionLocal() as session:
        visits = [v.id for v in session.scalars(select(RouteVisit))]
        result = seed_profile(session, load_profile("ucc-four-floors-c18")); session.commit()
        assert (result["created_places"], result["created_paths"]) == (40, 37)
        assert {p.code: p.id for p in session.scalars(select(Building)) if p.code in old_places} == old_places
        assert {p.code: (p.id, p.source_id, p.target_id, p.kind) for p in session.scalars(select(CampusPath)) if p.code in old_paths} == old_paths
        assert [v.id for v in session.scalars(select(RouteVisit))] == visits
        repeated = seed_profile(session, load_profile("ucc-four-floors-c18"))
        assert repeated["created_places"] == repeated["created_paths"] == 0


@pytest.mark.parametrize("algorithm", ["a_star", "dijkstra"])
def test_floor_zero_destinations_round_trip_over_the_east_tower(client: TestClient, user_headers: dict[str, str], algorithm: str) -> None:
    ids = load()
    for code, doorway in DESTINATIONS.items():
        for origin, destination in ((ids["ucc:floor1:p01"], ids[code]), (ids[code], ids["ucc:floor1:p01"])):
            response = client.post("/routes/calculate", headers=user_headers, json={"origin_id": origin, "destination_id": destination, "algorithm": algorithm})
            assert response.status_code == 200, response.text
            route = response.json()
            assert route["waypoints"][0]["id"] == origin and route["waypoints"][-1]["id"] == destination
            assert doorway in route["path"]
            tower = [w for w in route["waypoints"] if w["code"].startswith("ucc:f0:east-stair-")]
            assert len(tower) == 25
            assert all(w["floor"] == (1 if w["code"].endswith("24") else 0) for w in tower)
            assert {round(w["elevation_m"], 6) for w in tower if w["code"].endswith(("00", "24"))} == {A0, A1}
            assert all(w["elevation_m"] == A0 for w in route["waypoints"] if w["floor"] == 0 and not w["code"].startswith("ucc:f0:east-stair-"))
            assert all(s["connection_code"] and s["path_id"] for s in route["steps"])


@pytest.mark.parametrize("code", DESTINATIONS)
def test_no_invented_step_free_access_to_floor_zero(client: TestClient, user_headers: dict[str, str], code: str) -> None:
    ids = load()
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:floor1:p01"], "destination_id": ids[code], "avoid": ["stairs"]}).status_code == 404
    response = client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:f0:waiting-room"], "destination_id": ids["ucc:f0:simulation-lab-entrance"], "avoid": ["stairs"]})
    assert response.status_code == 200 and all(s["kind"] != "stairs" for s in response.json()["steps"])


def test_floor_zero_scope_needs_existing_floor1_and_fails_atomically(client: TestClient) -> None:
    data = CampusDataset.model_validate_json(DATASET.read_bytes())
    with SessionLocal() as session:
        with pytest.raises(ValueError, match="Unknown endpoint"):
            import_dataset(session, data)
        assert list(session.scalars(select(Building))) == list(session.scalars(select(CampusPath))) == []
        seed_profile(session, load_profile("ucc-three-floors-c16")); session.commit()
        before = [(p.id, p.code) for p in session.scalars(select(Building))]
        profile = load_profile("ucc-four-floors-c18")
        bad = copy.deepcopy(profile.datasets[-1]); bad.paths[-1].target_code = "test:missing"
        broken = Profile(profile.id, (*profile.datasets[:-1], bad), profile.generations, profile.selected_generations, profile.known_scopes)
        with pytest.raises(ValueError, match="Unknown endpoint"):
            seed_profile(session, broken)
        assert [(p.id, p.code) for p in session.scalars(select(Building))] == before
        assert len(list(session.scalars(select(CampusPath)))) == 102


def test_floor_zero_anchors_stay_isolated_at_the_b_datum(client: TestClient, user_headers: dict[str, str]) -> None:
    ids = load()
    for n in (1, 2, 3):
        code = f"ucc:f0:reference-{n}"
        with SessionLocal() as session:
            point = session.get(Building, ids[code])
            assert point.elevation_m == B0 and point.building_type == "reference" and point.floor == 0
        assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:floor1:p01"], "destination_id": ids[code]}).status_code == 404
