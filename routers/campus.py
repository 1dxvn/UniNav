from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from dependencies import AdminUser, DatabaseSession
from schemas.datasets import CampusDataset, DatasetImportResult
from services.datasets import import_dataset
from services.campus_graph import campus_graph_service
from schemas.campus import HierarchyResponse
from schemas.catalog import CatalogResponse
from services.catalog import catalog_for_database
from services.hierarchy import build_campus_tree, describe_campus

router = APIRouter(prefix="/campus", tags=["campus"])
PLACE_GUIDE_PATH: Path = Path(__file__).resolve().parent.parent / "data" / "place-guide.json"


@router.post("/datasets/import", response_model=DatasetImportResult)
def import_campus_dataset(
    dataset: CampusDataset, database_session: DatabaseSession, _admin_user: AdminUser
) -> DatasetImportResult:
    try:
        result = import_dataset(database_session, dataset)
        database_session.commit()
    except (ValueError, IntegrityError) as error:
        database_session.rollback()
        detail = str(error) if isinstance(error, ValueError) else "Dataset conflicts with existing records."
        raise HTTPException(status_code=409, detail=detail) from error
    campus_graph_service.load_from_database()
    return result


@router.get("/catalog", response_model=CatalogResponse)
def read_campus_catalog(database_session: DatabaseSession) -> CatalogResponse:
    return catalog_for_database(database_session)


@router.get("/hierarchy", response_model=HierarchyResponse)
def read_campus_hierarchy(database_session: DatabaseSession) -> HierarchyResponse:
    return describe_campus(build_campus_tree(database_session))


@router.get("/place-guide")
def read_place_guide() -> dict[str, Any]:
    """Reviewed search vocabulary for existing places (category, aliases, uses) and needs the map lacks.

    Labels only: it never adds a place. Built by scripts/build_place_guide.py into data/place-guide.json."""
    return place_guide()


@lru_cache(maxsize=1)
def place_guide() -> dict[str, Any]:
    if not PLACE_GUIDE_PATH.is_file():
        return {"version": 0, "places": {}, "categories": {}, "needs": {}, "missing": {}}
    return json.loads(PLACE_GUIDE_PATH.read_text(encoding="utf-8"))
