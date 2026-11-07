from __future__ import annotations

from fastapi import APIRouter

from dependencies import DatabaseSession
from schemas.campus import HierarchyResponse
from schemas.catalog import CatalogResponse
from services.catalog import catalog_for_database
from services.hierarchy import build_campus_tree, describe_campus

router = APIRouter(prefix="/campus", tags=["campus"])


@router.get("/catalog", response_model=CatalogResponse)
def read_campus_catalog(database_session: DatabaseSession) -> CatalogResponse:
    return catalog_for_database(database_session)


@router.get("/hierarchy", response_model=HierarchyResponse)
def read_campus_hierarchy(database_session: DatabaseSession) -> HierarchyResponse:
    return describe_campus(build_campus_tree(database_session))
