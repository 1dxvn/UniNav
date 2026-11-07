from __future__ import annotations

import threading

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from data_structures.graph import WeightedDirectedGraph
from database import SessionLocal
from models import Building, CampusPath
from schemas.paths import PathKind
from schemas.routes import PathAlgorithm, RouteStep, RouteWaypoint
from services.paths import effective_weight


class CampusGraphService:
    def __init__(self) -> None:
        self._graph: WeightedDirectedGraph = WeightedDirectedGraph()
        self._lock: threading.Lock = threading.Lock()
        self._floors: dict[str, int] = {}
        self._kinds: dict[tuple[str, str], str] = {}
        self._places: dict[str, RouteWaypoint] = {}
        self._connections: dict[tuple[str, str], tuple[int, str]] = {}

    def rebuild(self, buildings: list[Building], paths: list[CampusPath]) -> None:
        graph = WeightedDirectedGraph()
        for building in buildings:
            graph.add_node(str(building.id), (building.x, building.y))
        floors = {str(building.id): building.floor for building in buildings}
        places = {
            str(b.id): RouteWaypoint(
                id=b.id, code=b.code, name=b.name, display_name=b.display_name or b.name,
                x=b.x, y=b.y, floor=b.floor, elevation_m=b.effective_elevation_m,
                block_code=b.block_code, floor_code=b.floor_code,
            )
            for b in buildings
        }
        kinds: dict[tuple[str, str], str] = {}
        connections: dict[tuple[str, str], tuple[int, str]] = {}
        for path in paths:
            source, target = str(path.source_id), str(path.target_id)
            graph.add_edge(
                source,
                target,
                effective_weight(path),
                bidirectional=path.bidirectional,
            )
            kinds[(source, target)] = path.kind
            connections[(source, target)] = (path.id, path.code)
            if path.bidirectional:
                kinds[(target, source)] = path.kind
                connections[(target, source)] = (path.id, path.code)
        with self._lock:
            self._graph = graph
            self._floors = floors
            self._kinds = kinds
            self._places = places
            self._connections = connections

    def load_from_database(self) -> None:
        with SessionLocal() as database_session:
            buildings = list(database_session.scalars(select(Building).order_by(Building.id)))
            paths = list(
                database_session.scalars(
                    select(CampusPath)
                    .options(selectinload(CampusPath.source), selectinload(CampusPath.target))
                    .order_by(CampusPath.id)
                )
            )
        self.rebuild(buildings, paths)

    def contains(self, *ids: int) -> bool:
        with self._lock:
            return all(str(id_) in self._graph for id_ in ids)

    def find_path(
        self,
        origin: int,
        destination: int,
        algorithm: PathAlgorithm,
        avoid: frozenset[PathKind] = frozenset(),
    ) -> tuple[list[str], float]:
        with self._lock:
            graph = self._without_kinds(avoid) if avoid else self._graph
            if algorithm is PathAlgorithm.DIJKSTRA:
                return graph.dijkstra(str(origin), str(destination))
            return graph.a_star(str(origin), str(destination))

    def names(self, path: list[str]) -> list[str]:
        with self._lock:
            return [self._places[id_].name for id_ in path]

    def waypoints(self, path: list[str]) -> list[RouteWaypoint]:
        with self._lock:
            return [self._places[id_].model_copy() for id_ in path]

    def describe_steps(self, path: list[str]) -> list[RouteStep]:
        with self._lock:
            return [
                RouteStep(
                    origin_name=self._places[source].name,
                    destination_name=self._places[target].name,
                    origin_id=int(source), destination_id=int(target),
                    path_id=self._connections[(source, target)][0],
                    connection_code=self._connections[(source, target)][1],
                    origin_display_name=self._places[source].display_name,
                    destination_display_name=self._places[target].display_name,
                    kind=PathKind(self._kinds.get((source, target), PathKind.CORRIDOR.value)),
                    distance=self._graph.get_weight(source, target),
                )
                for source, target in zip(path, path[1:])
            ]

    def _without_kinds(self, avoid: frozenset[PathKind]) -> WeightedDirectedGraph:
        avoided = {kind.value for kind in avoid}
        graph = WeightedDirectedGraph()
        for name in self._graph.get_nodes():
            graph.add_node(name, self._graph.get_coordinates(name))
        for source, target, weight in self._graph.get_edges():
            if self._kinds.get((source, target)) not in avoided:
                graph.add_edge(source, target, weight)
        return graph

    def neighbors(self, id_: int) -> dict[int, float]:
        with self._lock:
            return {int(key): value for key, value in self._graph.get_neighbors(str(id_)).items()}

    def counts(self) -> tuple[int, int]:
        with self._lock:
            return self._graph.node_count(), self._graph.edge_count()

    def snapshot(
        self,
    ) -> tuple[list[tuple[str, float, float, int]], list[tuple[str, str, float, bool]]]:
        with self._lock:
            nodes = [
                (self._places[name].name, *(self._graph.get_coordinates(name) or (0.0, 0.0)), self._floors.get(name, 0))
                for name in self._graph.get_nodes()
            ]
            edges = [
                (self._places[source].name, self._places[target].name, weight, self._graph.has_edge(target, source))
                for source, target, weight in self._graph.get_edges()
                if not self._graph.has_edge(target, source) or source < target
            ]
        return nodes, edges


campus_graph_service: CampusGraphService = CampusGraphService()
