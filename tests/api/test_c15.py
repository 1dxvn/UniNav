from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from database import SessionLocal
from models import Building, CampusPath
from schemas.datasets import CampusDataset
from services.datasets import import_dataset
from services.campus_graph import campus_graph_service
from scripts.seed_ucc_floor1 import seed_campus

DATA = Path(__file__).resolve().parents[2] / "data/datasets"


def dataset(name: str) -> CampusDataset:
    return CampusDataset.model_validate_json((DATA / name).read_text(encoding="utf-8"))


def load() -> dict[str, int]:
    with SessionLocal() as session:
        seed_campus(session)
        import_dataset(session, dataset("ucc-first-floor-c15.json"))
        import_dataset(session, dataset("ucc-second-floor-c15.json"))
        session.commit()
        ids = {p.code: p.id for p in session.scalars(select(Building))}
    campus_graph_service.load_from_database()
    return ids


def test_c15_preserves_existing_ids_and_atomically_replaces_hall_bypass(client: TestClient) -> None:
    with SessionLocal() as session:
        seed_campus(session)
        import_dataset(session, dataset("ucc-second-floor.json"))
        session.commit()
        ids = {p.code: p.id for p in session.scalars(select(Building))}
        path_ids = {p.code: p.id for p in session.scalars(select(CampusPath))}
        assert (len(ids), len(path_ids)) == (64, 59)
        for name in ("ucc-first-floor-c15.json", "ucc-second-floor-c15.json"):
            import_dataset(session, dataset(name))
        session.commit()
        for name in ("ucc-first-floor-c15.json", "ucc-second-floor-c15.json"):
            repeated = import_dataset(session, dataset(name))
            assert repeated.unchanged_revision and repeated.created_places == repeated.created_paths == 0
        all_places = {p.code: p for p in session.scalars(select(Building))}
        all_paths = {p.code: p for p in session.scalars(select(CampusPath))}
        assert (len(all_places), len(all_paths)) == (68, 63)
        assert all(all_places[k].id == v for k, v in ids.items())
        assert all(all_paths[k].id == v for k, v in path_ids.items())
        assert all_places["ucc:floor1:p09"].y == 47.6
        assert all_paths["ucc:floor1:e09"].source_id == all_places["ucc:floor1:hall-after"].id
        assert not any(p.source_id == ids["ucc:floor1:p09"] and p.target_id == ids["ucc:floor1:p10"] for p in all_paths.values())
        for code in ("ucc:floor1:p11", "ucc:floor1:p12", "ucc:floor1:p13", "ucc:floor1:p19"):
            assert all_places[code].elevation_m == 3.5
            assert "pending" in all_places[code].elevation_source.lower()


@pytest.mark.parametrize("algorithm", ["a_star", "dijkstra"])
def test_c15_round_trips_preserve_hall_treads_heights_and_exclusion(client: TestClient, user_headers: dict[str, str], algorithm: str) -> None:
    ids = load()
    destinations = ["ucc:floor1:p06", "ucc:floor1:p10", "ucc:floor1:p14", "ucc:floor1:p13", "ucc:f2:mixed-reality-entrance", "ucc:f2:molecular-biology-entrance", "ucc:f2:medical-research-arrival"]
    for code in destinations:
        for a, b in ((ids["ucc:floor1:p01"], ids[code]), (ids[code], ids["ucc:floor1:p01"])):
            body = {"origin_id": a, "destination_id": b, "algorithm": algorithm}
            r = client.post("/routes/calculate", headers=user_headers, json=body)
            assert r.status_code == 200
            route = r.json()
            if code not in ("ucc:floor1:p06", "ucc:floor1:p13"):
                codes = [p["code"] for p in route["waypoints"]]
                for c in ("ucc:floor1:hall-tread-01", "ucc:floor1:hall-tread-02", "ucc:floor1:hall-tread-03", "ucc:floor1:hall-after"):
                    assert c in codes
                assert any(p["elevation_m"] == 2.87 for p in route["waypoints"])
            if code.startswith("ucc:f2:"):
                assert route["waypoints"][-1 if b == ids[code] else 0]["elevation_m"] == 6.18
            avoided = client.post("/routes/calculate", headers=user_headers, json={**body, "avoid": ["stairs"]})
            assert avoided.status_code == (200 if code == "ucc:floor1:p06" else 404)


def test_c15_bad_update_rolls_back_new_points_and_endpoint_changes(client: TestClient) -> None:
    with SessionLocal() as session:
        seed_campus(session)
        session.commit()
        before = [(p.code, p.x, p.y, p.elevation_m) for p in session.scalars(select(Building).order_by(Building.id))]
        bad = dataset("ucc-first-floor-c15.json")
        bad.paths[-1].target_code = "missing:point"
        with pytest.raises(ValueError, match="Unknown endpoint"):
            import_dataset(session, bad)
        assert before == [(p.code, p.x, p.y, p.elevation_m) for p in session.scalars(select(Building).order_by(Building.id))]
        assert len(list(session.scalars(select(CampusPath)))) == 16
