from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.buildings import BuildingCreate
from schemas.paths import PathKind


class DatasetPlace(BuildingCreate):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")
    elevation_m: float = Field(allow_inf_nan=False)
    elevation_source: str = Field(min_length=1, max_length=1000)


class DatasetPath(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")
    source_code: str
    target_code: str
    kind: PathKind = PathKind.CORRIDOR
    bidirectional: bool = True
    weight: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class CampusDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")
    revision: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=1000)
    places: list[DatasetPlace]
    paths: list[DatasetPath]

    @model_validator(mode="after")
    def unique_records(self) -> CampusDataset:
        for records in (self.places, self.paths):
            codes = [record.code for record in records]
            if len(codes) != len(set(codes)):
                raise ValueError("Dataset codes must be unique within each record type.")
        names = [place.name for place in self.places]
        if len(names) != len(set(names)):
            raise ValueError("Legacy names must be unique; use display_name for repeated labels.")
        if not self.places and not self.paths:
            raise ValueError("The dataset is empty.")
        return self


class DatasetImportResult(BaseModel):
    scope: str
    revision: str
    payload_hash: str
    created_places: int
    created_paths: int
    unchanged_revision: bool
