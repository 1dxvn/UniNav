from __future__ import annotations

import math
import threading

from sqlalchemy import select

from data_structures.graph import WeightedDirectedGraph
from database import SessionLocal
from models import Building
from schemas.routes import PathAlgorithm


def connect_building(graph: WeightedDirectedGraph, name: str, x: float, y: float) -> None:
    existing = [(other, graph.get_coordinates(other)) for other in graph.get_nodes()]
    graph.add_node(name, (x, y))
    for other, coordinates in existing:
        if other == name or coordinates is None:
            continue
        distance = math.hypot(coordinates[0] - x, coordinates[1] - y)
        graph.add_edge(name, other, distance, bidirectional=True)


class CampusGraphService:
    def __init__(self) -> None:
        self._graph: WeightedDirectedGraph = WeightedDirectedGraph()
        self._lock: threading.Lock = threading.Lock()

    def rebuild(self, buildings: list[Building]) -> None:
        graph = WeightedDirectedGraph()
        for building in buildings:
            connect_building(graph, building.name, building.x, building.y)
        with self._lock:
            self._graph = graph

    def load_from_database(self) -> None:
        with SessionLocal() as database_session:
            buildings = list(database_session.scalars(select(Building).order_by(Building.id)))
        self.rebuild(buildings)

    def add_building(self, name: str, x: float, y: float) -> None:
        with self._lock:
            connect_building(self._graph, name, x, y)

    def remove_building(self, name: str) -> None:
        with self._lock:
            if name in self._graph:
                self._graph.remove_node(name)

    def contains(self, *names: str) -> bool:
        with self._lock:
            return all(name in self._graph for name in names)

    def find_path(
        self, origin: str, destination: str, algorithm: PathAlgorithm
    ) -> tuple[list[str], float]:
        with self._lock:
            if algorithm is PathAlgorithm.DIJKSTRA:
                return self._graph.dijkstra(origin, destination)
            return self._graph.a_star(origin, destination)

    def neighbors(self, name: str) -> dict[str, float]:
        with self._lock:
            return self._graph.get_neighbors(name)

    def counts(self) -> tuple[int, int]:
        with self._lock:
            return self._graph.node_count(), self._graph.edge_count()

    def snapshot(self) -> tuple[list[tuple[str, float, float]], list[tuple[str, str, float]]]:
        with self._lock:
            nodes = [
                (name, *(self._graph.get_coordinates(name) or (0.0, 0.0)))
                for name in self._graph.get_nodes()
            ]
            edges = [edge for edge in self._graph.get_edges() if edge[0] < edge[1]]
        return nodes, edges


campus_graph_service: CampusGraphService = CampusGraphService()
