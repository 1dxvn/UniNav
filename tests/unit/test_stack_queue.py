import pytest

from data_structures.queue import Queue
from data_structures.stack import Stack


def test_stack_is_last_in_first_out():
    stack = Stack()
    for value in (1, 2, 3):
        stack.push(value)
    assert [stack.pop(), stack.pop(), stack.pop()] == [3, 2, 1]


def test_stack_peek_size_contains_clear():
    stack = Stack()
    stack.push("a")
    stack.push("b")
    assert stack.peek() == "b" and stack.size() == 2 and stack.contains("a")
    assert stack.to_list() == ["b", "a"]
    stack.clear()
    assert stack.is_empty()


def test_empty_stack_raises():
    stack = Stack()
    with pytest.raises(IndexError):
        stack.pop()
    with pytest.raises(IndexError):
        stack.peek()


def test_queue_is_first_in_first_out():
    queue = Queue()
    for value in ("a", "b", "c"):
        queue.enqueue(value)
    assert [queue.dequeue(), queue.dequeue(), queue.dequeue()] == ["a", "b", "c"]
    assert queue.is_empty()


def test_queue_position_and_contains():
    queue = Queue()
    for value in ("a", "b", "c"):
        queue.enqueue(value)
    assert queue.position_of("c") == 2
    assert queue.position_of("z") == -1
    assert queue.contains("b") and queue.peek() == "a"


def test_queue_can_be_reused_after_emptying():
    queue = Queue()
    queue.enqueue(1)
    queue.dequeue()
    queue.enqueue(2)
    assert queue.to_list() == [2]
    with pytest.raises(IndexError):
        Queue().dequeue()
