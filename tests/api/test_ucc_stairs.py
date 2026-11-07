"""Prepared stair classification; physical-level geometry is still pending."""
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

DATA = Path(__file__).resolve().parents[2] / "data/datasets"


def dataset(name: str) -> CampusDataset:
    return CampusDataset.model_validate_json((DATA / name).read_text(encoding="utf-8"))


def load_review(upper: bool) -> dict[str, int]:
    with SessionLocal() as session:
        seed_campus(session)
        if upper:
            import_dataset(session, dataset("ucc-second-floor.json"))
        import_dataset(session, dataset("ucc-first-floor-stairs.json"))
        session.commit()
        ids = {p.name: p.id for p in session.scalars(select(Building))}
    campus_graph_service.load_from_database()
    return ids


@pytest.mark.parametrize("upper", [False, True])
def test_stair_review_preserves_ids_positions_other_paths_and_scopes(client: TestClient, upper: bool) -> None:
    with SessionLocal() as session:
        seed_campus(session)
        if upper:
            import_dataset(session, dataset("ucc-second-floor.json"))
        places = {p.code: (p.id, p.x, p.y, p.floor, p.elevation_m, p.data_scope) for p in session.scalars(select(Building))}
        paths = {p.code: (p.id, p.source_id, p.target_id, p.weight, p.bidirectional, p.kind, p.data_scope) for p in session.scalars(select(CampusPath))}
        imported = import_dataset(session, dataset("ucc-first-floor-stairs.json"))
        session.commit()
        repeated = import_dataset(session, dataset("ucc-first-floor-stairs.json"))
        assert imported.created_places == imported.created_paths == 0
        assert repeated.unchanged_revision
        assert places == {p.code: (p.id, p.x, p.y, p.floor, p.elevation_m, p.data_scope) for p in session.scalars(select(Building))}
        after = {p.code: (p.id, p.source_id, p.target_id, p.weight, p.bidirectional, p.kind, p.data_scope) for p in session.scalars(select(CampusPath))}
        changed = {code for code in paths if paths[code] != after[code]}
        assert changed == {"ucc:floor1:e08", "ucc:floor1:e09", "ucc:floor1:e10"}
        for code in changed:
            assert paths[code][:5] == after[code][:5] and after[code][5:] == ("stairs", "ucc:floor1")


@pytest.mark.parametrize("upper", [False, True])
@pytest.mark.parametrize("algorithm", ["a_star", "dijkstra"])
def test_review_excludes_confirmed_steps_in_both_directions_without_inventing_alternatives(client: TestClient, user_headers: dict[str, str], upper: bool, algorithm: str) -> None:
    ids = load_review(upper)
    for target in ("ICETEX", "Morphology Laboratory", "Elevator and Restroom Hall", "Preclinic / Dentistry Coordination"):
        for origin, destination in (("Hall Acceso", target), (target, "Hall Acceso")):
            body = {"origin_id": ids[origin], "destination_id": ids[destination], "algorithm": algorithm}
            normal = client.post("/routes/calculate", headers=user_headers, json=body)
            assert normal.status_code == 200
            assert all(p["elevation_m"] == 3.5 for p in normal.json()["waypoints"])
            avoided = client.post("/routes/calculate", headers=user_headers, json={**body, "avoid": ["stairs"]})
            assert avoided.status_code == (200 if target == "ICETEX" else 404)
    # Avoiding stairs does not close the whole A area: only connections with steps.
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": ids["Elevator and Restroom Hall"], "destination_id": ids["Preclinic / Dentistry Coordination"], "avoid": ["stairs"]}).status_code == 200
    if upper:
        with SessionLocal() as session:
            upper_ids = [p.id for p in session.scalars(select(Building)) if p.code in {"ucc:f2:mixed-reality-entrance", "ucc:f2:molecular-biology-entrance", "ucc:f2:medical-research-arrival"}]
        assert len(upper_ids) == 3
        for target_id in upper_ids:
            for origin_id, destination_id in ((ids["Hall Acceso"], target_id), (target_id, ids["Hall Acceso"])):
                assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": origin_id, "destination_id": destination_id, "algorithm": algorithm, "avoid": ["stairs"]}).status_code == 404


def test_stair_review_rejects_missing_base_and_stale_baseline_reapply(client: TestClient) -> None:
    with SessionLocal() as session:
        with pytest.raises(ValueError, match="Unknown endpoint"):
            import_dataset(session, dataset("ucc-first-floor-stairs.json"))
        assert list(session.scalars(select(CampusPath))) == []
    load_review(False)
    with SessionLocal() as session:
        with pytest.raises(ValueError, match="Stored revision has changed path"):
            seed_campus(session)
        # An outdated seed cannot silently undo the reviewed stair classification.
        assert session.scalar(select(CampusPath).where(CampusPath.code == "ucc:floor1:e10")).kind == "stairs"
