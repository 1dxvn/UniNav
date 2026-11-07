"""Atomic, non-destructive imports. Callers own the outer commit and graph reload."""
from __future__ import annotations

import hashlib
import json

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models import Building, CampusDataRevision, CampusPath
from schemas.datasets import CampusDataset, DatasetImportResult


def import_dataset(session: Session, dataset: CampusDataset, *, adopt_legacy: bool = False) -> DatasetImportResult:
    payload_hash = hashlib.sha256(json.dumps(dataset.model_dump(mode="json"),
        sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    counts = [0, 0]
    # sqlite3 legacy mode does not BEGIN on SELECT/SAVEPOINT. Releasing this
    # savepoint must not commit the caller's outer transaction.
    connection = session.connection()
    if connection.dialect.name == "sqlite" and not connection.connection.driver_connection.in_transaction:
        connection.exec_driver_sql("BEGIN")
    with session.begin_nested():
        revision = session.get(CampusDataRevision, (dataset.scope, dataset.revision))
        if revision and revision.payload_hash != payload_hash:
            raise ValueError("This revision already exists with a different payload; create a new revision.")
        places = {place.code: place for place in session.scalars(select(Building))}
        by_name = {place.name: place for place in places.values()}
        for record in dataset.places:
            values = record.model_dump()
            place = places.get(record.code)
            if place is None and record.name in by_name:
                candidate = by_name[record.name]
                same_location = (abs(candidate.x-record.x) < 0.001 and abs(candidate.y-record.y) < 0.001
                    and candidate.floor == record.floor and abs(candidate.effective_elevation_m-record.elevation_m) < 0.001)
                if not (adopt_legacy and candidate.data_scope is None and same_location
                        and candidate.code.startswith(("legacy-place:", "place:"))):
                    raise ValueError(f"Legacy name already belongs to another record: {record.name}.")
                place = candidate
            if place is None:
                if revision:
                    raise ValueError(f"Stored revision has missing place: {record.code}.")
                place = Building(**values, data_scope=dataset.scope)
                session.add(place)
                counts[0] += 1
            else:
                if place.data_scope != dataset.scope and not (adopt_legacy and place.data_scope is None
                        and place.code.startswith(("legacy-place:", "place:"))
                        and abs(place.x-record.x) < 0.001 and abs(place.y-record.y) < 0.001
                        and place.floor == record.floor and abs(place.effective_elevation_m-record.elevation_m) < 0.001):
                    raise ValueError(f"Place is owned by another scope: {record.code}.")
                if revision and any(getattr(place, key) != value for key, value in values.items()):
                    raise ValueError(f"Stored revision has changed place: {record.code}.")
                name_owner = by_name.get(record.name)
                if name_owner is not None and name_owner is not place:
                    raise ValueError(f"Legacy name already exists: {record.name}.")
                by_name.pop(place.name, None)
                for key, value in values.items():
                    setattr(place, key, value)
                place.data_scope = dataset.scope
            places[record.code] = place
            by_name[record.name] = place
        session.flush()
        for record in dataset.paths:
            if record.source_code not in places or record.target_code not in places:
                raise ValueError(f"Unknown endpoint for path: {record.code}.")
            source, target = places[record.source_code], places[record.target_code]
            if source.id == target.id:
                raise ValueError(f"A path must connect different places: {record.code}.")
            values = dict(code=record.code, source_id=source.id, target_id=target.id,
                kind=record.kind.value, bidirectional=record.bidirectional, weight=record.weight)
            path = session.scalar(select(CampusPath).where(CampusPath.code == record.code))
            pair = session.scalar(select(CampusPath).where(or_(
                (CampusPath.source_id == source.id) & (CampusPath.target_id == target.id),
                (CampusPath.source_id == target.id) & (CampusPath.target_id == source.id))))
            if path is None and pair is not None:
                if not (adopt_legacy and pair.data_scope is None
                        and pair.code.startswith(("legacy-path:", "path:"))
                        and all(getattr(pair, key) == value for key, value in values.items() if key != "code")):
                    raise ValueError(f"Path endpoints already belong to another record: {record.code}.")
                path = pair
            elif pair is not None and pair is not path:
                raise ValueError(f"Path endpoints already exist: {record.code}.")
            if path is None:
                if revision:
                    raise ValueError(f"Stored revision has missing path: {record.code}.")
                path = CampusPath(**values, data_scope=dataset.scope)
                session.add(path)
                counts[1] += 1
            else:
                if path.data_scope != dataset.scope and not (adopt_legacy and path.data_scope is None):
                    raise ValueError(f"Path is owned by another scope: {record.code}.")
                if revision and any(getattr(path, key) != value for key, value in values.items()):
                    raise ValueError(f"Stored revision has changed path: {record.code}.")
                for key, value in values.items():
                    setattr(path, key, value)
                path.data_scope = dataset.scope
            session.flush()
        if revision is None:
            session.add(CampusDataRevision(scope=dataset.scope, revision=dataset.revision,
                payload_hash=payload_hash, source=dataset.source))
        session.flush()
    return DatasetImportResult(scope=dataset.scope, revision=dataset.revision, payload_hash=payload_hash,
        created_places=counts[0], created_paths=counts[1], unchanged_revision=revision is not None)
