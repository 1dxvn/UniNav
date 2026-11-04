import pytest

from data_structures.circular_doubly_linked_list import CircularDoublyLinkedList
from data_structures.doubly_linked_list import DoublyLinkedList


def make_list(*values):
    linked = DoublyLinkedList()
    for value in values:
        linked.append(value)
    return linked


def test_forward_and_backward_traversal():
    linked = make_list(1, 2, 3)
    linked.prepend(0)
    assert linked.to_list_forward() == [0, 1, 2, 3]
    assert linked.to_list_backward() == [3, 2, 1, 0]


@pytest.mark.parametrize("value, expected", [(1, [2, 3]), (2, [1, 3]), (3, [1, 2])])
def test_remove_head_middle_and_tail(value, expected):
    linked = make_list(1, 2, 3)
    assert linked.remove(value) is True
    assert linked.to_list_forward() == expected
    assert linked.to_list_backward() == expected[::-1]
    assert len(linked) == 2


def test_remove_missing_value_returns_false():
    assert make_list(1).remove(9) is False


def make_circle(*values):
    circle = CircularDoublyLinkedList()
    for value in values:
        circle.append(value)
    return circle


def test_circular_navigation_wraps_around():
    circle = make_circle("a", "b", "c")
    assert circle.current == "a"
    assert [circle.next(), circle.next(), circle.next()] == ["b", "c", "a"]
    assert circle.previous() == "c"


def test_circular_backward_listing():
    assert make_circle(1, 2, 3).to_list_backward() == [3, 2, 1]


def test_circular_remove_moves_cursor_forward():
    circle = make_circle("a", "b", "c")
    assert circle.remove("a") is True
    assert circle.current == "b"
    assert circle.to_list() == ["b", "c"]


def test_circular_remove_last_element_empties_the_list():
    circle = make_circle("only")
    circle.remove("only")
    assert circle.is_empty()
    with pytest.raises(IndexError):
        circle.next()


def test_circular_move_to():
    circle = make_circle(1, 2, 3)
    assert circle.move_to(3) is True and circle.current == 3
    assert circle.move_to(99) is False


def test_pop_front_returns_values_in_order():
    linked = make_list(1, 2, 3)
    assert [linked.pop_front(), linked.pop_front()] == [1, 2]
    assert linked.to_list_forward() == [3] and linked.to_list_backward() == [3]
    linked.pop_front()
    with pytest.raises(IndexError):
        linked.pop_front()


def test_truncate_after_drops_the_tail():
    linked = make_list(1, 2, 3, 4)
    assert linked.truncate_after(linked.find(2)) == 2
    assert linked.to_list_forward() == [1, 2]
    assert linked.tail.value == 2 and len(linked) == 2
    linked.append(9)
    assert linked.to_list_backward() == [9, 2, 1]


def test_truncate_after_the_last_node_removes_nothing():
    linked = make_list(1, 2)
    assert linked.truncate_after(linked.tail) == 0
    assert linked.to_list_forward() == [1, 2]
