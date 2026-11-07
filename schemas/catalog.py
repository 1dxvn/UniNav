from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CatalogFloor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    level: int = Field(ge=0, le=7)
    name: str
    source_label: str
    datum_elevation_m: float = Field(allow_inf_nan=False)
    evidence: Literal["confirmed", "derived", "pending"]


class CatalogBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    identity_evidence: Literal["confirmed", "derived", "pending"]
    source: str
    floors: list[CatalogFloor]


class IntegratedDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    revision: str
    label: str
    legacy_floor: int
    model_elevation_m: float = Field(allow_inf_nan=False)
    elevation_evidence: Literal["confirmed", "derived", "provisional"]


class CampusCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    id: str
    revision: str
    source: str
    integrated_dataset: IntegratedDataset
    blocks: list[CatalogBlock]
    unassigned_sheets: list[str]
    notes: list[str]

    @model_validator(mode="after")
    def unique_identifiers(self) -> CampusCatalog:
        identifiers = [b.id for b in self.blocks] + [f.id for b in self.blocks for f in b.floors]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Catalogue block and floor identifiers must be unique.")
        return self


class CatalogResponse(BaseModel):
    available: bool
    catalog: CampusCatalog | None
