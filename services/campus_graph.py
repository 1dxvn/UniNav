from __future__ import annotations

import threading

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from data_structures.graph import WeightedDirectedGraph
from database import SessionLocal
from models import Building, CampusPath
from schemas.paths import PathKind
from schemas.routes import PathAlgorithm, RouteStep
from services.paths import effective_weight


class CampusGraphService:
    def __init__(self) -> None:
        self._graph: WeightedDirectedGraph = WeightedDirectedGraph()
        self._lock: threading.Lock = threading.Lock()
        self._floors: dict[str, int] = {}
        self._kinds: dict[tuple[str, str], str] = {}

    def rebuild(self, buildings: list[Building], paths: list[CampusPath]) -> None:
        graph = WeightedDirectedGraph()
        for building in buildings:
            graph.add_node(building.name, (building.x, building.y))
        floors = {building.name: building.floor for building in buildings}
        kinds: dict[tuple[str, str], str] = {}
        for path in paths:
            graph.add_edge(
                path.source.name,
                path.target.name,
                effective_weight(path),
                bidirectional=path.bidirectional,
            )
            kinds[(path.source.name, path.target.name)] = path.kind
            if path.bidirectional:
                kinds[(path.target.name, path.source.name)] = path.kind
        with self._lock:
            self._graph = graph
            self._floors = floors
            self._kinds = kinds

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

    def add_building(self, name: str, x: float, y: float, floor: int) -> None:
        with self._lock:
            self._graph.add_node(name, (x, y))
            self._floors[name] = floor

    def remove_building(self, name: str) -> None:
        with self._lock:
            if name in self._graph:
                self._graph.remove_node(name)
            self._floors.pop(name, None)

    def contains(self, *names: str) -> bool:
        with self._lock:
            return all(name in self._graph for name in names)

    def find_path(
        self,
        origin: str,
        destination: str,
        algorithm: PathAlgorithm,
        avoid: frozenset[PathKind] = frozenset(),
    ) -> tuple[list[str], float]:
        with self._lock:
            graph = self._without_kinds(avoid) if avoid else self._graph
            if algorithm is PathAlgorithm.DIJKSTRA:
                return graph.dijkstra(origin, destination)
            return graph.a_star(origin, destination)

    def describe_steps(self, path: list[str]) -> list[RouteStep]:
        with self._lock:
            return [
                RouteStep(
                    origin_name=source,
                    destination_name=target,
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

    def neighbors(self, name: str) -> dict[str, float]:
        with self._lock:
            return self._graph.get_neighbors(name)

    def counts(self) -> tuple[int, int]:
        with self._lock:
            return self._graph.node_count(), self._graph.edge_count()

    def snapshot(
        self,
    ) -> tuple[list[tuple[str, float, float, int]], list[tuple[str, str, float, bool]]]:
        with self._lock:
            nodes = [
                (name, *(self._graph.get_coordinates(name) or (0.0, 0.0)), self._floors.get(name, 0))
                for name in self._graph.get_nodes()
            ]
            edges = [
                (source, target, weight, self._graph.has_edge(target, source))
                for source, target, weight in self._graph.get_edges()
                if not self._graph.has_edge(target, source) or source < target
            ]
        return nodes, edges


campus_graph_service: CampusGraphService = CampusGraphService()
