from __future__ import annotations

from pydantic import BaseModel, Field


class GraphNodeResponse(BaseModel):
    name: str
    x: float
    y: float


class GraphEdgeResponse(BaseModel):
    source: str
    target: str
    weight: float = Field(ge=0)


class GraphResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
