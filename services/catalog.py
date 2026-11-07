"""Read-only, versioned source inventory. Does not seed places or change elevations."""
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Building, CampusPath
from schemas.catalog import CampusCatalog, CatalogResponse
from scripts.ucc_floor1_data import PATHS, PLACES

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "campus-catalog.json"


def read_catalog() -> CampusCatalog:
    return CampusCatalog.model_validate_json(CATALOG_PATH.read_text(encoding="utf-8"))


def catalog_for_database(session: Session) -> CatalogResponse:
    # Do not present UCC observations as the catalogue of an unrelated sample DB.
    catalog = read_catalog()
    places = {place.name: place for place in session.scalars(select(Building))}
    for name, x, y, floor, *_ in PLACES:
        place = places.get(name)
        if (place is None or place.floor != floor or abs(place.x-x) > 0.001 or abs(place.y-y) > 0.001
                or abs(place.effective_elevation_m-catalog.integrated_dataset.model_elevation_m) > 0.001):
            return CatalogResponse(available=False, catalog=None)
    edges = {
        (edge.source.name, edge.target.name, edge.kind, edge.bidirectional)
        for edge in session.scalars(select(CampusPath).options(selectinload(CampusPath.source), selectinload(CampusPath.target)))
    }
    for source, target, kind in PATHS:
        if (source, target, kind, True) not in edges and (target, source, kind, True) not in edges:
            return CatalogResponse(available=False, catalog=None)
    return CatalogResponse(available=True, catalog=catalog)
