from __future__ import annotations

from fastapi import APIRouter

from dependencies import DatabaseSession
from schemas.campus import HierarchyResponse
from services.hierarchy import build_campus_tree, describe_campus

router = APIRouter(prefix="/campus", tags=["campus"])


@router.get("/hierarchy", response_model=HierarchyResponse)
def read_campus_hierarchy(database_session: DatabaseSession) -> HierarchyResponse:
    return describe_campus(build_campus_tree(database_session))
