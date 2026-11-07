"""Synthetic multi-floor contracts; no unconfirmed campus locations are seeded."""
from copy import deepcopy
import math

import pytest
from sqlalchemy import func, select

from database import SessionLocal
from models import Building, CampusDataRevision, CampusPath, RouteVisit
from schemas.datasets import CampusDataset
from scripts.seed_ucc_floor1 import seed_campus
from scripts.ucc_floor1_data import PLACES, PATHS
from services.datasets import import_dataset


def dataset(scope="test:lower", height=3.5, floor=1):
    return dict(scope=scope, revision="v1", source="Synthetic test fixture only", places=[
        dict(code=f"{scope}:hall", name=f"{scope}:hall", display_name="Hall", x=0, y=0,
             floor=floor, elevation_m=height, elevation_source="Synthetic", block_code="test",
             floor_code=f"test:{floor}")], paths=[])


def post(client, admin_headers, payload):
    return client.post("/campus/datasets/import", headers=admin_headers, json=payload)


@pytest.mark.parametrize("algorithm", ["a_star", "dijkstra"])
def test_route_ids_repeated_labels_and_explicit_elevations(client, admin_headers, algorithm):
    lower, upper = dataset(), dataset("test:upper", 6.44, 2)
    upper["places"][0]["x"] = 4
    upper["paths"] = [dict(code="test:vertical", source_code="test:lower:hall", target_code="test:upper:hall", kind="stairs")]
    assert post(client, admin_headers, lower).status_code == 200
    assert post(client, admin_headers, upper).status_code == 200
    places = client.get("/buildings?search=Hall").json()
    assert len(places) == 2 and {p["display_name"] for p in places} == {"Hall"}
    a, b = sorted(places, key=lambda p: p["floor"])
    assert client.get("/buildings?floor_code=test:2").json() == [b]
    weight = math.hypot(4, 2.94)
    for start, end in ((a, b), (b, a)):
        response = client.post("/routes/calculate", headers=admin_headers, json=dict(origin_id=start["id"], destination_id=end["id"], algorithm=algorithm))
        route = response.json()
        assert response.status_code == 200, route
        assert route["distance"] == pytest.approx(weight)
        assert [p["id"] for p in route["waypoints"]] == [start["id"], end["id"]]
        assert [p["elevation_m"] for p in route["waypoints"]] == [start["elevation_m"], end["elevation_m"]]
        assert route["steps"][0]["connection_code"] == "test:vertical"
        assert route["steps"][0]["origin_id"] == start["id"]
    request = dict(origin_id=a["id"], destination_id=b["id"])
    assert client.post("/routes/calculate", headers=admin_headers, json={**request, "avoid": ["stairs"]}).status_code == 404
    compare = client.post("/routes/compare", json=request).json()
    assert all(result["waypoints"][1]["id"] == b["id"] for result in compare["results"])
    legs = client.post("/routes/multi-stop", json=dict(building_ids=[a["id"], b["id"], a["id"]])).json()["legs"]
    assert legs[1]["waypoints"][1]["id"] == a["id"]
    renamed = client.put(f'/buildings/{a["id"]}', headers=admin_headers, json=dict(name="Changed legacy alias", display_name="Hall renamed", code="ignored")).json()
    assert renamed["code"] == a["code"]
    route = client.post("/routes/calculate", headers=admin_headers, json=request).json()
    assert route["path"][0] == "Changed legacy alias"
    assert route["waypoints"][0]["code"] == a["code"]
    assert route["steps"][0]["origin_display_name"] == "Hall renamed"
    assert client.get(f'/buildings/{a["id"]}/neighbors').json()[0]["building"]["id"] == b["id"]


def test_scopes_idempotence_revisions_and_omitted_records_are_preserved(client, admin_headers):
    lower, upper = dataset(), dataset("test:upper", 6.44, 2)
    for payload in (lower, upper):
        assert post(client, admin_headers, payload).json()["created_places"] == 1
    before = client.get("/buildings").json()
    again = post(client, admin_headers, lower).json()
    assert again["unchanged_revision"] and again["created_places"] == 0
    changed = deepcopy(lower)
    changed["places"][0]["display_name"] = "Renamed"
    assert post(client, admin_headers, changed).status_code == 409
    changed["revision"] = "v2"
    assert post(client, admin_headers, changed).status_code == 200
    after = client.get("/buildings").json()
    assert [p["id"] for p in before] == [p["id"] for p in after]
    assert after[1] == before[1]
    # Replaying an old revision cannot silently roll a newer record backwards.
    assert post(client, admin_headers, lower).status_code == 409
    omitted = deepcopy(changed)
    omitted["revision"] = "v3"
    omitted["places"][0]["code"] = "test:lower:extra"
    omitted["places"][0]["name"] = "Extra synthetic room"
    assert post(client, admin_headers, omitted).status_code == 200
    assert len(client.get("/buildings").json()) == 3


def test_scope_conflict_and_missing_endpoint_roll_back_whole_import(client, admin_headers):
    assert post(client, admin_headers, dataset()).status_code == 200
    foreign = dataset("test:foreign")
    foreign["places"][0]["code"] = "test:lower:hall"
    assert post(client, admin_headers, foreign).status_code == 409
    broken = dataset("test:broken")
    broken["paths"] = [dict(code="broken", source_code="test:broken:hall", target_code="absent")]
    assert post(client, admin_headers, broken).status_code == 409
    assert len(client.get("/buildings").json()) == 1
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(CampusDataRevision)) == 1


def test_import_is_admin_only_and_rejects_incomplete_sources(client, user_headers, admin_headers):
    assert post(client, user_headers, dataset()).status_code == 403
    invalid = dataset()
    del invalid["places"][0]["elevation_m"]
    assert post(client, admin_headers, invalid).status_code == 422
    invalid = dataset()
    invalid["places"] *= 2
    assert post(client, admin_headers, invalid).status_code == 422


def test_outer_rollback_is_not_committed_by_import_savepoint(client):
    with SessionLocal() as session:
        import_dataset(session, CampusDataset.model_validate(dataset()))
        session.rollback()
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Building)) == 0
        assert session.scalar(select(func.count()).select_from(CampusDataRevision)) == 0


def test_seed_adopts_existing_ids_and_history_and_keeps_other_scopes(client, admin_headers):
    # Reproduce the old first-floor seed before explicit codes and elevations.
    with SessionLocal() as session:
        places = {}
        for name, x, y, floor, faculty, kind in PLACES:
            places[name] = Building(name=name, x=x, y=y, floor=floor, faculty=faculty, building_type=kind)
            session.add(places[name])
        session.flush()
        for source, target, kind in PATHS:
            session.add(CampusPath(source_id=places[source].id, target_id=places[target].id, kind=kind, bidirectional=True))
        session.commit()
        ids = {p.name: p.id for p in places.values()}
        edges = list(session.scalars(select(CampusPath.id)))
        session.add(RouteVisit(user_id=1, origin_id=ids["Hall Acceso"], destination_id=ids["ICETEX"], distance=50))
        session.commit()
        assert seed_campus(session) == (0, 0)
        session.commit()
        import_dataset(session, CampusDataset.model_validate(dataset("test:upper", 6.44, 2)))
        session.commit()
        assert seed_campus(session) == (0, 0)
        session.commit()
        assert {p.name: p.id for p in session.scalars(select(Building).where(Building.data_scope == "ucc:floor1"))} == ids
        assert list(session.scalars(select(CampusPath.id))) == edges
        assert session.scalar(select(func.count()).select_from(RouteVisit)) == 1
        assert session.scalar(select(func.count()).select_from(Building)) == 20
        assert all(p.elevation_m == 3.5 for p in session.scalars(select(Building).where(Building.data_scope == "ucc:floor1")))


def test_seed_refuses_sample_campus(client, campus):
    with SessionLocal() as session:
        with pytest.raises(ValueError, match="another campus"):
            seed_campus(session)


def test_legacy_adoption_refuses_changed_coordinates_without_partial_changes(client):
    with SessionLocal() as session:
        for index, (name, x, y, floor, faculty, kind) in enumerate(PLACES):
            session.add(Building(name=name, x=x + (1 if index == 3 else 0), y=y,
                                 floor=floor, faculty=faculty, building_type=kind))
        session.commit()
        with pytest.raises(ValueError):
            seed_campus(session)
        assert all(p.data_scope is None for p in session.scalars(select(Building)))
        assert session.scalar(select(func.count()).select_from(CampusDataRevision)) == 0


def test_dataset_cannot_take_over_another_scopes_path(client, admin_headers):
    lower, upper = dataset(), dataset("test:upper", 6.44, 2)
    upper["paths"] = [dict(code="test:vertical", source_code="test:lower:hall", target_code="test:upper:hall", kind="stairs")]
    assert post(client, admin_headers, lower).status_code == 200
    assert post(client, admin_headers, upper).status_code == 200
    foreign = dict(scope="test:foreign", revision="v1", source="Synthetic", places=[], paths=upper["paths"])
    assert post(client, admin_headers, foreign).status_code == 409
    foreign["paths"] = [{**upper["paths"][0], "code": "test:other"}]
    assert post(client, admin_headers, foreign).status_code == 409
    assert client.get("/paths").json()[0]["code"] == "test:vertical"


def test_same_revision_detects_manual_drift(client, admin_headers):
    payload = dataset()
    assert post(client, admin_headers, payload).status_code == 200
    place = client.get("/buildings").json()[0]
    client.put(f'/buildings/{place["id"]}', headers=admin_headers, json=dict(x=100))
    assert post(client, admin_headers, payload).status_code == 409
    assert client.get("/buildings").json()[0]["x"] == 100
