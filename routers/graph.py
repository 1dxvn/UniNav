from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from dependencies import CurrentUser
from schemas.graph import GraphEdgeResponse, GraphNodeResponse, GraphResponse
from services.campus_graph import campus_graph_service

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
def read_graph() -> GraphResponse:
    nodes, edges = campus_graph_service.snapshot()
    return GraphResponse(
        nodes=[GraphNodeResponse(name=name, x=x, y=y) for name, x, y in nodes],
        edges=[GraphEdgeResponse(source=s, target=t, weight=w) for s, t, w in edges],
    )


@router.post("/reload")
def reload_graph(_current_user: CurrentUser) -> dict[str, Any]:
    campus_graph_service.load_from_database()
    buildings, edges = campus_graph_service.counts()
    return {"status": "reloaded", "buildings": buildings, "edges": edges}
