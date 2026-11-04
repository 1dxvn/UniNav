from __future__ import annotations

from pydantic import BaseModel, Field


class QueueStatusResponse(BaseModel):
    building_id: int
    building_name: str
    length: int = Field(ge=0)


class QueuePositionResponse(QueueStatusResponse):
    position: int = Field(ge=1)


class ServedResponse(QueueStatusResponse):
    served_username: str
