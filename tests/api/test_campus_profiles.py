from __future__ import annotations

import copy
import json
from pathlib import Path
import socket

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete, select

from database import SessionLocal
from models import Building, CampusDataRevision, CampusPath, RouteVisit
from scripts.campus_profiles import Profile, load_profile, payload_hash, profile_ids, seed_profile
from services.campus_graph import campus_graph_service


def snapshot(session) -> tuple:
    return ([(p.id, p.code, p.x, p.y, p.elevation_m) for p in session.scalars(select(Building).order_by(Building.id))],
        [(p.id, p.code, p.source_id, p.target_id, p.kind) for p in session.scalars(select(CampusPath).order_by(CampusPath.id))],
        [(r.scope, r.revision, r.payload_hash) for r in session.scalars(select(CampusDataRevision).order_by(CampusDataRevision.scope, CampusDataRevision.revision))])


@pytest.mark.parametrize("profile_id,counts", zip(profile_ids(), [(19,16),(64,59),(19,16),(64,59),(68,63),(110,102)], strict=True))
def test_profiles_start_and_repeat_without_replaying_old_revisions(client: TestClient, profile_id: str, counts: tuple[int,int]) -> None:
    profile = load_profile(profile_id)
    with SessionLocal() as session:
        result = seed_profile(session, profile)
        assert (result["places"], result["paths"]) == counts
        assert (result["created_places"], result["created_paths"]) == counts
        session.commit()
        before = snapshot(session)
        again = seed_profile(session, profile)
        assert again["created_places"] == again["created_paths"] == 0
        assert all(r["unchanged_revision"] for r in again["revisions"])
        session.commit()
        assert snapshot(session) == before
        for data in profile.datasets:
            revision = session.get(CampusDataRevision, (data.scope, data.revision))
            assert revision.payload_hash == payload_hash(data)


def test_upgrade_preserves_ids_history_and_other_scoped_blocks(client: TestClient, user_headers: dict[str,str]) -> None:
    with SessionLocal() as session:
        seed_profile(session, load_profile("ucc-two-floors-stair-review"))
        session.commit()
        ids = {p.code:p.id for p in session.scalars(select(Building))}
        paths = {p.code:p.id for p in session.scalars(select(CampusPath))}
        other = Building(code="test:block:q1", name="Other scoped block", x=150, y=150, floor=1, data_scope="test:block:q")
        other2=Building(code="test:block:q2",name="Other scoped destination",x=151,y=150,floor=1,data_scope="test:block:q")
        session.add_all([other,other2]);session.flush();other_id=other.id
        other_path=CampusPath(code="test:block:q-edge",source_id=other.id,target_id=other2.id,kind="corridor",bidirectional=True,data_scope="test:block:q")
        session.add(other_path);session.commit();other_path_id=other_path.id
    campus_graph_service.load_from_database()
    route = client.post("/routes/calculate",headers=user_headers,json={"origin_id":ids["ucc:floor1:p01"],"destination_id":ids["ucc:floor1:p06"]})
    assert route.status_code == 200
    with SessionLocal() as session:
        history = list(session.scalars(select(RouteVisit)))
        assert len(history)==1
        result = seed_profile(session, load_profile("ucc-two-floors-c15"))
        session.commit()
        assert (result["places"],result["paths"]) == (70,64)
        assert {p.code:p.id for p in session.scalars(select(Building)) if p.code in ids} == ids
        assert {p.code:p.id for p in session.scalars(select(CampusPath)) if p.code in paths} == paths
        assert session.get(Building,other_id).data_scope == "test:block:q"
        assert session.get(CampusPath,other_path_id).code=="test:block:q-edge"
        assert [v.id for v in session.scalars(select(RouteVisit))] == [v.id for v in history]


def test_c15_scopes_and_bootstrap_roll_back_together(client: TestClient) -> None:
    profile=load_profile("ucc-two-floors-c15")
    bad=copy.deepcopy(profile.datasets[1]);bad.paths[-1].target_code="test:missing"
    broken=Profile(profile.id,(profile.datasets[0],bad),profile.generations,profile.selected_generations,profile.known_scopes)
    with SessionLocal() as session:
        before=snapshot(session)
        with pytest.raises(ValueError,match="Unknown endpoint"):
            seed_profile(session,broken)
        assert snapshot(session)==before
        seed_profile(session,profile)
        session.rollback()
        assert snapshot(session)==before


@pytest.mark.parametrize("old,new",[("ucc-three-floors-c16","ucc-two-floors-c15"),("ucc-two-floors-c15","base"),("ucc-two-floors-c15","ucc-two-floors-stair-review"),("ucc-first-floor-stair-review","base"),("ucc-two-floors","base")])
def test_profile_downgrades_do_not_remove_or_revert_records(client: TestClient,old:str,new:str)->None:
    with SessionLocal() as session:
        seed_profile(session,load_profile(old));session.commit();before=snapshot(session)
        with pytest.raises(ValueError,match="downgrade|omits"):
            seed_profile(session,load_profile(new))
        assert snapshot(session)==before


def test_profile_rejects_drifted_inputs_before_import(client:TestClient,tmp_path:Path,monkeypatch:pytest.MonkeyPatch)->None:
    import scripts.campus_profiles as module
    source=module.ROOT
    (tmp_path/"data/datasets").mkdir(parents=True)
    dataset=json.loads((source/"data/datasets/ucc-first-floor-c15.json").read_text(encoding="utf-8"));dataset["places"][0]["x"]+=1
    (tmp_path/"data/datasets/ucc-first-floor-c15.json").write_text(json.dumps(dataset),encoding="utf-8")
    monkeypatch.setattr(module,"ROOT",tmp_path)
    with pytest.raises(ValueError,match="Reviewed startup dataset changed"):
        load_profile("ucc-two-floors-c15")


def test_sample_and_active_legacy_campus_are_protected_before_configuring_database(tmp_path:Path,monkeypatch:pytest.MonkeyPatch)->None:
    import os
    import scripts.seed_campus as module
    sample=tmp_path/"sample.db";sample.write_bytes(b"sample untouched")
    campus=tmp_path/"campus.db";campus.write_bytes(b"campus untouched")
    monkeypatch.setattr(module,"SAMPLE_DATABASE",sample);monkeypatch.setattr(module,"CAMPUS_DATABASE",campus)
    old=os.environ["UNINAV_DATABASE_URL"]
    with pytest.raises(ValueError,match="sample uninav.db is protected"):
        module.configure_database(sample)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1",0));listener.listen()
        monkeypatch.setattr(module,"CAMPUS_SERVICE_PORT",listener.getsockname()[1])
        with pytest.raises(ValueError,match="existing 8001 service"):
            module.configure_database(campus)
    assert os.environ["UNINAV_DATABASE_URL"]==old
    assert sample.read_bytes()==b"sample untouched" and campus.read_bytes()==b"campus untouched"


def test_legacy_adoption_bootstraps_once_then_upgrades_in_place(client:TestClient)->None:
    with SessionLocal() as session:
        seed_profile(session,load_profile("base"));session.commit()
        ids=[p.id for p in session.scalars(select(Building).order_by(Building.id))]
        for p in session.scalars(select(Building)):
            p.code=f"legacy-place:{p.id}";p.data_scope=None
        for p in session.scalars(select(CampusPath)):
            p.code=f"legacy-path:{p.id}";p.data_scope=None
        session.execute(delete(CampusDataRevision));session.commit()
        result=seed_profile(session,load_profile("ucc-two-floors-c15"));session.commit()
        assert (result["places"],result["paths"])==(68,63)
        assert [p.id for p in session.scalars(select(Building).order_by(Building.id).limit(19))]==ids
        assert seed_profile(session,load_profile("ucc-two-floors-c15"))["created_places"]==0


def test_foreign_unscoped_campus_is_not_adopted(client:TestClient)->None:
    with SessionLocal() as session:
        session.add(Building(name="Unrelated sample entrance",x=0,y=0,floor=0));session.commit();before=snapshot(session)
        with pytest.raises(ValueError,match="another campus"):
            seed_profile(session,load_profile("ucc-two-floors-c15"))
        assert snapshot(session)==before
