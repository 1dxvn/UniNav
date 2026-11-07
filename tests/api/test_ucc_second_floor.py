from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from database import SessionLocal
from models import Building, CampusPath
from schemas.datasets import CampusDataset
from scripts.seed_ucc_floor1 import seed_campus
from services.campus_graph import campus_graph_service
from services.datasets import import_dataset


DATASET = Path(__file__).resolve().parents[2] / "data/datasets/ucc-second-floor.json"
DESTINATIONS = (
    "ucc:f2:mixed-reality-entrance",
    "ucc:f2:molecular-biology-entrance",
    "ucc:f2:medical-research-arrival",
)


def load_dataset() -> dict[str, int]:
    with SessionLocal() as session:
        assert seed_campus(session) == (19, 16)
        result = import_dataset(session, CampusDataset.model_validate_json(DATASET.read_text(encoding="utf-8")))
        assert (result.created_places, result.created_paths) == (45, 43)
        session.commit()
        ids = {p.code: p.id for p in session.scalars(select(Building))}
    campus_graph_service.load_from_database()
    return ids


def test_second_floor_import_preserves_base_ids_and_is_repeatable(client: TestClient, user_headers: dict[str, str]) -> None:
    dataset = CampusDataset.model_validate_json(DATASET.read_text(encoding="utf-8"))
    with SessionLocal() as session:
        seed_campus(session)
        session.commit()
        old_places = {p.code: p.id for p in session.scalars(select(Building))}
        old_paths = {p.code: (p.id, p.source_id, p.target_id) for p in session.scalars(select(CampusPath))}
        assert (len(old_places), len(old_paths)) == (19, 16)
        imported = import_dataset(session, dataset)
        session.commit()
        repeated = import_dataset(session, dataset)
        assert repeated.unchanged_revision and repeated.created_places == repeated.created_paths == 0
        all_places = {p.code: p for p in session.scalars(select(Building))}
        all_paths = {p.code: p for p in session.scalars(select(CampusPath))}
        assert (len(all_places), len(all_paths)) == (64, 59)
        assert all(all_places[code].id == place_id for code, place_id in old_places.items())
        assert all((all_paths[code].id, all_paths[code].source_id, all_paths[code].target_id) == values for code, values in old_paths.items())
        assert (imported.created_places, imported.created_paths) == (45, 43)
        ids = {p.name: p.id for p in all_places.values()}
    campus_graph_service.load_from_database()
    for name in ("ICETEX", "Morphology Laboratory", "Elevator and Restroom Hall", "Preclinic / Dentistry Coordination"):
        route = client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["Hall Acceso"], "destination_id": ids[name]})
        assert route.status_code == 200
        assert all(p["floor"] == 1 and p["elevation_m"] == 3.5 for p in route.json()["waypoints"])


@pytest.mark.parametrize("algorithm", ["a_star", "dijkstra"])
def test_second_floor_round_trips_keep_doors_stair_heights_and_ids(client: TestClient, user_headers: dict[str, str], algorithm: str) -> None:
    ids = load_dataset()
    for code, door in zip(DESTINATIONS, ("D14", "D15", "D13")):
        for origin, destination in ((ids["ucc:floor1:p01"], ids[code]), (ids[code], ids["ucc:floor1:p01"])):
            response = client.post("/routes/calculate", headers=user_headers, json={"origin_id": origin, "destination_id": destination, "algorithm": algorithm})
            assert response.status_code == 200
            route = response.json()
            assert route["waypoints"][0]["id"] == origin and route["waypoints"][-1]["id"] == destination
            assert f"{door} doorway centre" in route["path"]
            assert "North circulation / east stair junction" in route["path"]
            assert any(step["kind"] == "stairs" for step in route["steps"])
            assert all(step["path_id"] and step["connection_code"] for step in route["steps"])
            assert any(p["floor"] == 1 and p["elevation_m"] > 3.5 for p in route["waypoints"])
            assert all(p["elevation_m"] == 6.44 for p in route["waypoints"] if p["floor"] == 2)


@pytest.mark.parametrize("code", DESTINATIONS)
def test_second_floor_has_no_invented_step_free_connection(client: TestClient, user_headers: dict[str, str], code: str) -> None:
    ids = load_dataset()
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["ucc:floor1:p01"], "destination_id": ids[code], "avoid": ["stairs"]}).status_code == 404


def test_second_floor_rejects_missing_base_atomically(client: TestClient) -> None:
    with SessionLocal() as session:
        with pytest.raises(ValueError, match="Unknown endpoint"):
            import_dataset(session, CampusDataset.model_validate_json(DATASET.read_text(encoding="utf-8")))
        assert list(session.scalars(select(Building))) == []
        assert list(session.scalars(select(CampusPath))) == []
