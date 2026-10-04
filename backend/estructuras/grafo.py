from __future__ import annotations

from typing import Callable, Optional

Node = str
Coordinates = tuple[float, float]
Heuristic = Callable[[Node, Node], float]
Path = tuple[list[Node], float]

INFINITY: float = float("inf")


class _MinPriorityQueue:
    def __init__(self) -> None:
        self._items: list[tuple[float, int, Node]] = []
        self._insertion_order: int = 0

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def push(self, node: Node, priority: float) -> None:
        self._items.append((priority, self._insertion_order, node))
        self._insertion_order += 1
        self._sift_up(len(self._items) - 1)

    def pop_min(self) -> tuple[Node, float]:
        if self.is_empty():
            raise IndexError("Cannot pop from an empty priority queue.")

        priority, _, node = self._items[0]
        last = self._items.pop()
        if self._items:
            self._items[0] = last
            self._sift_down(0)
        return node, priority

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self._items[index] >= self._items[parent]:
                break
            self._swap(index, parent)
            index = parent

    def _sift_down(self, index: int) -> None:
        size = len(self._items)
        while True:
            left = 2 * index + 1
            right = left + 1
            smallest = index

            if left < size and self._items[left] < self._items[smallest]:
                smallest = left
            if right < size and self._items[right] < self._items[smallest]:
                smallest = right

            if smallest == index:
                return
            self._swap(index, smallest)
            index = smallest

    def _swap(self, i: int, j: int) -> None:
        self._items[i], self._items[j] = self._items[j], self._items[i]


class WeightedDirectedGraph:
    def __init__(self) -> None:
        self._adjacency: dict[Node, dict[Node, float]] = {}
        self._coordinates: dict[Node, Coordinates] = {}
        self._edge_count: int = 0

    def add_node(self, node: Node, coordinates: Optional[Coordinates] = None) -> None:
        if not node:
            raise ValueError("Node identifier cannot be empty.")

        self._adjacency.setdefault(node, {})
        if coordinates is not None:
            self._coordinates[node] = (float(coordinates[0]), float(coordinates[1]))

    def remove_node(self, node: Node) -> None:
        self._validate_node(node)

        self._edge_count -= len(self._adjacency.pop(node))
        self._coordinates.pop(node, None)

        for neighbors in self._adjacency.values():
            if neighbors.pop(node, None) is not None:
                self._edge_count -= 1

    def has_node(self, node: Node) -> bool:
        return node in self._adjacency

    def get_nodes(self) -> list[Node]:
        return list(self._adjacency)

    def get_coordinates(self, node: Node) -> Optional[Coordinates]:
        self._validate_node(node)
        return self._coordinates.get(node)

    def add_edge(
        self,
        source: Node,
        target: Node,
        weight: float,
        bidirectional: bool = False,
    ) -> None:
        is_number = isinstance(weight, (int, float)) and not isinstance(weight, bool)
        if not is_number:
            raise ValueError(f"Weight must be numeric, got: {weight!r}")
        if weight < 0:
            raise ValueError(f"Weight cannot be negative (got {weight}).")

        self.add_node(source)
        self.add_node(target)

        self._insert_edge(source, target, float(weight))
        if bidirectional:
            self._insert_edge(target, source, float(weight))

    def remove_edge(self, source: Node, target: Node, bidirectional: bool = False) -> None:
        if not self.has_edge(source, target):
            raise KeyError(f"Edge '{source}' -> '{target}' does not exist.")

        del self._adjacency[source][target]
        self._edge_count -= 1

        if bidirectional and self.has_edge(target, source):
            del self._adjacency[target][source]
            self._edge_count -= 1

    def has_edge(self, source: Node, target: Node) -> bool:
        return target in self._adjacency.get(source, {})

    def get_weight(self, source: Node, target: Node) -> float:
        if not self.has_edge(source, target):
            raise KeyError(f"Edge '{source}' -> '{target}' does not exist.")
        return self._adjacency[source][target]

    def get_neighbors(self, node: Node) -> dict[Node, float]:
        self._validate_node(node)
        return dict(self._adjacency[node])

    def get_edges(self) -> list[tuple[Node, Node, float]]:
        return [
            (source, target, weight)
            for source, neighbors in self._adjacency.items()
            for target, weight in neighbors.items()
        ]

    def node_count(self) -> int:
        return len(self._adjacency)

    def edge_count(self) -> int:
        return self._edge_count

    def dijkstra(self, start: Node, goal: Node) -> Path:
        return self._find_path(start, goal, self._zero_heuristic)

    def a_star(
        self,
        start: Node,
        goal: Node,
        heuristic: Optional[Heuristic] = None,
    ) -> Path:
        return self._find_path(start, goal, heuristic or self.euclidean_heuristic)

    def euclidean_heuristic(self, current: Node, goal: Node) -> float:
        current_coordinates = self._coordinates.get(current)
        goal_coordinates = self._coordinates.get(goal)
        if current_coordinates is None or goal_coordinates is None:
            return 0.0

        dx = goal_coordinates[0] - current_coordinates[0]
        dy = goal_coordinates[1] - current_coordinates[1]
        return (dx * dx + dy * dy) ** 0.5

    @staticmethod
    def _zero_heuristic(_current: Node, _goal: Node) -> float:
        return 0.0

    def _find_path(self, start: Node, goal: Node, heuristic: Heuristic) -> Path:
        self._validate_node(start)
        self._validate_node(goal)

        if start == goal:
            return [start], 0.0

        distance_from_start: dict[Node, float] = {start: 0.0}
        predecessors: dict[Node, Optional[Node]] = {start: None}
        settled_nodes: set[Node] = set()

        frontier = _MinPriorityQueue()
        frontier.push(start, heuristic(start, goal))

        while not frontier.is_empty():
            current, _ = frontier.pop_min()

            if current in settled_nodes:
                continue
            settled_nodes.add(current)

            if current == goal:
                path = self._reconstruct_path(predecessors, goal)
                return path, distance_from_start[goal]

            for neighbor, weight in self._adjacency[current].items():
                if neighbor in settled_nodes:
                    continue

                candidate_distance = distance_from_start[current] + weight
                if candidate_distance < distance_from_start.get(neighbor, INFINITY):
                    distance_from_start[neighbor] = candidate_distance
                    predecessors[neighbor] = current
                    frontier.push(neighbor, candidate_distance + heuristic(neighbor, goal))

        return [], INFINITY

    @staticmethod
    def _reconstruct_path(predecessors: dict[Node, Optional[Node]], goal: Node) -> list[Node]:
        path: list[Node] = []
        current: Optional[Node] = goal
        while current is not None:
            path.append(current)
            current = predecessors[current]
        path.reverse()
        return path

    def _insert_edge(self, source: Node, target: Node, weight: float) -> None:
        if target not in self._adjacency[source]:
            self._edge_count += 1
        self._adjacency[source][target] = weight

    def _validate_node(self, node: Node) -> None:
        if node not in self._adjacency:
            raise KeyError(f"Node '{node}' does not exist in the graph.")

    def __contains__(self, node: object) -> bool:
        return node in self._adjacency

    def __len__(self) -> int:
        return len(self._adjacency)

    def __repr__(self) -> str:
        return (
            f"WeightedDirectedGraph(nodes={self.node_count()}, "
            f"edges={self.edge_count()})"
        )

    def __str__(self) -> str:
        if not self._adjacency:
            return "Empty graph"
        lines: list[str] = []
        for node, neighbors in self._adjacency.items():
            connections = ", ".join(f"{n} ({w:g})" for n, w in neighbors.items()) or "no outgoing edges"
            lines.append(f"{node} -> {connections}")
        return "\n".join(lines)


if __name__ == "__main__":
    campus = WeightedDirectedGraph()

    campus.add_node("Entrance", (0, 0))
    campus.add_node("Library", (100, 0))
    campus.add_node("Building A", (100, 100))
    campus.add_node("Cafeteria", (200, 50))
    campus.add_node("Auditorium", (300, 100))

    campus.add_edge("Entrance", "Library", 100, bidirectional=True)
    campus.add_edge("Entrance", "Building A", 150, bidirectional=True)
    campus.add_edge("Library", "Cafeteria", 120, bidirectional=True)
    campus.add_edge("Building A", "Cafeteria", 115, bidirectional=True)
    campus.add_edge("Cafeteria", "Auditorium", 115, bidirectional=True)
    campus.add_edge("Building A", "Auditorium", 260)

    print(campus, end="\n\n")
    print("Dijkstra:", campus.dijkstra("Entrance", "Auditorium"))
    print("A*:      ", campus.a_star("Entrance", "Auditorium"))