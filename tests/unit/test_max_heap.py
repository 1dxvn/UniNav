import random

import pytest

from data_structures.max_heap import MaxHeap


def test_pops_from_highest_to_lowest_priority():
    heap = MaxHeap()
    for item, priority in (("low", 1), ("high", 9), ("mid", 5)):
        heap.push(item, priority)
    assert [heap.pop_max()[0] for _ in range(3)] == ["high", "mid", "low"]
    assert heap.is_empty()


def test_equal_priorities_keep_insertion_order():
    heap = MaxHeap()
    for item in ("first", "second", "third"):
        heap.push(item, 4)
    heap.push("winner", 5)
    assert [heap.pop_max()[0] for _ in range(4)] == ["winner", "first", "second", "third"]


def test_peek_does_not_remove():
    heap = MaxHeap()
    heap.push("a", 2)
    assert heap.peek_max() == ("a", 2) and len(heap) == 1


def test_empty_heap_raises():
    heap = MaxHeap()
    with pytest.raises(IndexError):
        heap.pop_max()
    with pytest.raises(IndexError):
        heap.peek_max()


def test_matches_sorting_on_random_data():
    generator = random.Random(7)
    priorities = [generator.randint(0, 50) for _ in range(300)]
    heap = MaxHeap()
    for index, priority in enumerate(priorities):
        heap.push(index, priority)

    popped = [heap.pop_max()[1] for _ in range(len(priorities))]
    assert popped == sorted(priorities, reverse=True)
