from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from services.campus_graph import campus_graph_service

router = APIRouter(tags=["status"])


@router.get("/health")
def health_check() -> dict[str, Any]:
    building_count, edge_count = campus_graph_service.counts()
    return {"status": "ok", "buildings": building_count, "edges": edge_count}
