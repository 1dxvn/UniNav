from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HierarchyNodeResponse(BaseModel):
    name: str
    data: dict[str, Any]
    children: list[HierarchyNodeResponse]


class HierarchyResponse(BaseModel):
    height: int
    total_nodes: int
    root: HierarchyNodeResponse
