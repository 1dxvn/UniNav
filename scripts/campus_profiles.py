"""Reviewed startup datasets. Importing this module never opens a database."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from schemas.datasets import CampusDataset

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data/campus-profiles.json"


def registry() -> dict:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if data["version"] != 1:
        raise ValueError("Unsupported campus profile registry.")
    return data


def profile_ids() -> tuple[str, ...]:
    return tuple(registry()["profiles"])


def payload_hash(dataset: CampusDataset) -> str:
    # Same canonical payload as services.datasets; independent of CRLF and IDs.
    return hashlib.sha256(json.dumps(dataset.model_dump(mode="json"), sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class Profile:
    id: str
    datasets: tuple[CampusDataset, ...]
    generations: dict[tuple[str, str], int]
    selected_generations: dict[str, int]
    known_scopes: frozenset[str]


def load_profile(profile_id: str) -> Profile:
    from schemas.datasets import CampusDataset

    data = registry()
    if profile_id not in data["profiles"]:
        raise ValueError(f"Unknown campus profile: {profile_id}.")
    selected = data["profiles"][profile_id]
    groups: dict[str, list[CampusDataset]] = defaultdict(list)
    generations = {(d["scope"], d["revision"]): d["generation"] for d in data["datasets"].values()}
    for p in data["profiles"].values():
        for scope, revision in p.get("composed_revisions", {}).items():
            generations[scope, revision] = max(data["datasets"][name]["generation"]
                for name in p["datasets"] if data["datasets"][name]["scope"] == scope)
    for name in selected["datasets"]:
        spec = data["datasets"][name]
        dataset = CampusDataset.model_validate_json((ROOT / "data/datasets" / name).read_text(encoding="utf-8"))
        if (dataset.scope, dataset.revision, payload_hash(dataset)) != (spec["scope"], spec["revision"], spec["sha256"]):
            raise ValueError(f"Reviewed startup dataset changed: {name}. Review a new profile revision first.")
        groups[dataset.scope].append(dataset)
    effective = []
    for scope, parts in groups.items():
        if len(parts) == 1:
            effective.append(parts[0])
            continue
        # Compose patches in memory, so a restart never replays the flat baseline
        # into an already upgraded scope. Source order preserves stable insert IDs.
        places = {p.code: p for d in parts for p in d.places}
        paths = {p.code: p for d in parts for p in d.paths}
        effective.append(CampusDataset(scope=scope, revision=selected["composed_revisions"][scope],
            source="Startup composition: " + ", ".join(f"{d.scope}@{d.revision}" for d in parts),
            places=list(places.values()), paths=list(paths.values())))
    return Profile(profile_id, tuple(effective), generations,
        {d.scope: generations[d.scope, d.revision] for d in effective},
        frozenset(d["scope"] for d in data["datasets"].values()))


def seed_profile(session: Session, profile: Profile) -> dict:
    """Atomic across scopes; the caller owns commit and any live graph reload."""
    from sqlalchemy import func, select
    from models import Building, CampusDataRevision, CampusPath
    from scripts.seed_ucc_floor1 import seed_campus
    from services.datasets import import_dataset

    # Begin before the outer savepoint: sqlite's legacy driver otherwise releases
    # its first savepoint as a commit, defeating the caller's rollback.
    connection = session.connection()
    if connection.dialect.name == "sqlite" and not connection.connection.driver_connection.in_transaction:
        connection.exec_driver_sql("BEGIN")
    with session.begin_nested():
        scopes = set(session.scalars(select(Building.data_scope))) | set(session.scalars(select(CampusPath.data_scope)))
        excluded = (scopes & profile.known_scopes) - profile.selected_generations.keys()
        if excluded:
            raise ValueError("Selected profile omits an installed campus scope. Use a matching profile or a separate database; no records were removed.")
        for revision in session.scalars(select(CampusDataRevision)):
            previous = profile.generations.get((revision.scope, revision.revision), 0)
            if revision.scope in profile.selected_generations and previous > profile.selected_generations[revision.scope]:
                raise ValueError("Refusing to downgrade an installed campus revision. Use a separate database or a reviewed migration.")
        created = [0, 0]
        if "ucc:floor1" not in scopes:
            # Fresh DB or recognized legacy identities: bootstrap once, then apply
            # the full target. Existing upgraded scopes never enter this branch.
            created[:] = seed_campus(session)
        results = []
        for dataset in profile.datasets:
            result = import_dataset(session, dataset)
            results.append(result.model_dump(mode="json"))
            created[0] += result.created_places
            created[1] += result.created_paths
        report = {"profile": profile.id, "created_places": created[0], "created_paths": created[1],
            "places": session.scalar(select(func.count()).select_from(Building)),
            "paths": session.scalar(select(func.count()).select_from(CampusPath)), "revisions": results}
    return report
