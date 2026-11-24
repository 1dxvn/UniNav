from __future__ import annotations

import threading

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from data_structures.graph import WeightedDirectedGraph
from database import SessionLocal
from models import Building, CampusPath
from schemas.paths import PathKind
from schemas.routes import PathAlgorithm, RouteMode, RouteStep, RouteWaypoint
from services.paths import effective_weight
from services.route_costs import MIN_MULTIPLIER, comfort_cost, estimated_seconds

# (source, target, physical length, kind, path id), one entry per travel direction.
DirectedEdge = tuple[str, str, float, str, int]
SearchKey = tuple[RouteMode, frozenset[PathKind]]


class CampusGraphService:
    def __init__(self) -> None:
        # Physical graph: weights are metres. Used for reported distances, never changed by learning.
        self._graph: WeightedDirectedGraph = WeightedDirectedGraph()
        self._lock: threading.Lock = threading.Lock()
        self._floors: dict[str, int] = {}
        self._kinds: dict[tuple[str, str], str] = {}
        self._places: dict[str, RouteWaypoint] = {}
        self._connections: dict[tuple[str, str], tuple[int, str]] = {}
        self._edges: list[DirectedEdge] = []
        self._path_ends: dict[int, tuple[str, str, str]] = {}
        # Search graphs per (mode, avoided kinds), built on first use and dropped when data or learning change.
        self._search_graphs: dict[SearchKey, WeightedDirectedGraph] = {}
        self._multipliers: dict[int, float] = {}
        self._blocked: frozenset[int] = frozenset()

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
        edges: list[DirectedEdge] = []
        path_ends: dict[int, tuple[str, str, str]] = {}
        for path in paths:
            source, target = str(path.source_id), str(path.target_id)
            length = effective_weight(path)
            graph.add_edge(source, target, length, bidirectional=path.bidirectional)
            kinds[(source, target)] = path.kind
            connections[(source, target)] = (path.id, path.code)
            edges.append((source, target, length, path.kind, path.id))
            path_ends[path.id] = (source, target, path.kind)
            if path.bidirectional:
                kinds[(target, source)] = path.kind
                connections[(target, source)] = (path.id, path.code)
                edges.append((target, source, length, path.kind, path.id))
        with self._lock:
            self._graph = graph
            self._floors = floors
            self._kinds = kinds
            self._places = places
            self._connections = connections
            self._edges = edges
            self._path_ends = path_ends
            self._search_graphs = {}

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
        mode: RouteMode = RouteMode.SHORTEST,
    ) -> tuple[list[str], float]:
        """Returns the route and its physical length in metres, whatever cost the mode searched with."""
        with self._lock:
            graph = self._search_graph(mode, avoid)
            start, goal = str(origin), str(destination)
            if algorithm is PathAlgorithm.DIJKSTRA:
                path, _cost = graph.dijkstra(start, goal)
            else:
                # Learned multipliers may go slightly below 1, so the straight-line estimate is scaled to stay optimistic.
                scale = 1.0 if mode is RouteMode.SHORTEST else MIN_MULTIPLIER
                path, _cost = graph.a_star(start, goal, lambda a, b: scale * graph.euclidean_heuristic(a, b))
            if not path:
                return [], float("inf")
            return path, sum(self._graph.get_weight(a, b) for a, b in zip(path, path[1:]))

    def set_learning(self, multipliers: dict[int, float], blocked: frozenset[int]) -> None:
        """Applies what services.route_learning computed. Blocked connections leave every mode."""
        with self._lock:
            if multipliers == self._multipliers and blocked == self._blocked:
                return
            self._multipliers = dict(multipliers)
            self._blocked = frozenset(blocked)
            self._search_graphs = {}

    def path_ids(self, path: list[str]) -> list[int]:
        with self._lock:
            return [self._connections[(a, b)][0] for a, b in zip(path, path[1:])]

    def path_kinds(self, path: list[str]) -> list[str]:
        with self._lock:
            return [self._kinds.get((a, b), PathKind.CORRIDOR.value) for a, b in zip(path, path[1:])]

    def estimate_seconds(self, path: list[str]) -> float:
        with self._lock:
            return estimated_seconds(
                (self._graph.get_weight(a, b), self._kinds.get((a, b), PathKind.CORRIDOR.value))
                for a, b in zip(path, path[1:])
            )

    def path_endpoints(self, path_id: int) -> tuple[str, str, str] | None:
        """(origin name, destination name, kind) of a stored connection, for admin listings."""
        with self._lock:
            ends = self._path_ends.get(path_id)
            if ends is None:
                return None
            source, target, kind = ends
            return self._places[source].display_name, self._places[target].display_name, kind

    def _search_graph(self, mode: RouteMode, avoid: frozenset[PathKind]) -> WeightedDirectedGraph:
        key = (mode, avoid)
        cached = self._search_graphs.get(key)
        if cached is not None:
            return cached
        avoided = {kind.value for kind in avoid}
        # Shortest keeps its walking meaning: elevators only serve people who avoid stairs.
        if mode is RouteMode.SHORTEST and PathKind.STAIRS.value not in avoided:
            avoided.add(PathKind.ELEVATOR.value)
        graph = WeightedDirectedGraph()
        for name in self._graph.get_nodes():
            graph.add_node(name, self._graph.get_coordinates(name))
        for source, target, length, kind, path_id in self._edges:
            if kind in avoided or path_id in self._blocked:
                continue
            if mode is RouteMode.SHORTEST:
                graph.add_edge(source, target, length)
            else:
                graph.add_edge(source, target, comfort_cost(length, kind, self._multipliers.get(path_id, 1.0)))
        self._search_graphs[key] = graph
        return graph

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
