from sqlalchemy import func, select

from database import SessionLocal
from models import Building, CampusPath
from scripts.seed_ucc_floor1 import seed_campus
from services.catalog import read_catalog


def test_unrelated_campus_has_no_ucc_catalog(client, campus):
    assert client.get("/campus/catalog").json() == {"available": False, "catalog": None}


def test_catalog_preserves_documented_levels_and_current_flat_model(client):
    with SessionLocal() as session:
        assert seed_campus(session) == (19, 16)
        session.commit()
    result = client.get("/campus/catalog").json()
    assert result["available"] is True
    catalog = result["catalog"]
    blocks = {block["id"]: block for block in catalog["blocks"]}
    assert blocks["A"]["identity_evidence"] == "derived"
    assert blocks["B"]["floors"][2]["datum_elevation_m"] == 2.94
    assert blocks["A"]["floors"][1]["datum_elevation_m"] == -0.63
    assert all(floor["evidence"] == "derived" for block in blocks.values() for floor in block["floors"])
    assert catalog["integrated_dataset"]["model_elevation_m"] == 3.5
    assert catalog["integrated_dataset"]["elevation_evidence"] == "provisional"
    assert catalog["unassigned_sheets"]  # Roofs are not assigned invented floor numbers.
    for _ in range(2):
        assert client.get("/campus/catalog").json() == result
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Building)) == 19
        assert session.scalar(select(func.count()).select_from(CampusPath)) == 16
        assert {b.floor for b in session.scalars(select(Building))} == {1}
        session.get(Building, 1).x += 1
        session.commit()
    assert client.get("/campus/catalog").json()["available"] is False


def test_catalog_ids_are_unique_and_versioned():
    catalog = read_catalog()
    assert catalog.version == 1 and catalog.revision == "dwg-a35f892"
    ids = [floor.id for block in catalog.blocks for floor in block.floors]
    assert len(ids) == len(set(ids)) == 12
