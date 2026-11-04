import pytest

from data_structures.graph import INFINITY, WeightedDirectedGraph
from data_structures.heaps import MinPriorityQueue


@pytest.fixture()
def graph():
    campus = WeightedDirectedGraph()
    for name, coordinates in {"A": (0, 0), "B": (100, 0), "C": (100, 100), "D": (200, 50)}.items():
        campus.add_node(name, coordinates)
    campus.add_edge("A", "B", 100, bidirectional=True)
    campus.add_edge("A", "C", 400, bidirectional=True)
    campus.add_edge("B", "C", 100, bidirectional=True)
    campus.add_edge("C", "D", 120, bidirectional=True)
    return campus


def test_shortest_path_prefers_cheaper_detour(graph):
    assert graph.dijkstra("A", "D") == (["A", "B", "C", "D"], 320.0)


def test_a_star_matches_dijkstra(graph):
    assert graph.a_star("A", "D") == graph.dijkstra("A", "D")


def test_start_equals_goal(graph):
    assert graph.a_star("A", "A") == (["A"], 0.0)


def test_unreachable_node_returns_empty_path(graph):
    graph.add_node("Island", (999, 999))
    assert graph.dijkstra("A", "Island") == ([], INFINITY)


def test_one_way_edges_are_respected():
    graph = WeightedDirectedGraph()
    graph.add_edge("A", "B", 1)
    assert graph.dijkstra("A", "B")[0] == ["A", "B"]
    assert graph.dijkstra("B", "A")[0] == []


def test_edge_count_tracks_additions_and_removals(graph):
    assert graph.edge_count() == 8
    graph.remove_edge("A", "B", bidirectional=True)
    assert graph.edge_count() == 6
    graph.remove_node("C")
    assert graph.edge_count() == 0 and "C" not in graph


def test_invalid_input_is_rejected(graph):
    with pytest.raises(ValueError):
        graph.add_edge("A", "B", -1)
    with pytest.raises(ValueError):
        graph.add_edge("A", "B", "far")
    with pytest.raises(KeyError):
        graph.dijkstra("A", "Missing")
    with pytest.raises(KeyError):
        graph.get_weight("A", "D")


def test_priority_queue_orders_by_priority_then_insertion():
    queue = MinPriorityQueue()
    queue.push("late", 5)
    queue.push("first", 1)
    queue.push("second", 1)
    assert [queue.pop_min()[0] for _ in range(3)] == ["first", "second", "late"]
    with pytest.raises(IndexError):
        queue.pop_min()
