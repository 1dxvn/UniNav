from __future__ import annotations

from typing import Generic, Iterator, Optional, TypeVar

from data_structures.list_nodes import DoublyNode

T = TypeVar("T")


class CircularDoublyLinkedList(Generic[T]):
    def __init__(self) -> None:
        self._head: Optional[DoublyNode[T]] = None
        self._cursor: Optional[DoublyNode[T]] = None
        self._size: int = 0

    @property
    def current(self) -> T:
        if self._cursor is None:
            raise IndexError("The circular list is empty.")
        return self._cursor.value

    def append(self, value: T) -> DoublyNode[T]:
        new_node = DoublyNode(value)
        if self._head is None:
            new_node.next = new_node
            new_node.previous = new_node
            self._head = new_node
            self._cursor = new_node
        else:
            tail = self._head.previous
            assert tail is not None
            new_node.previous = tail
            new_node.next = self._head
            tail.next = new_node
            self._head.previous = new_node
        self._size += 1
        return new_node

    def remove(self, value: T) -> bool:
        node = self.find(value)
        if node is None:
            return False

        if self._size == 1:
            self._head = None
            self._cursor = None
        else:
            previous_node = node.previous
            next_node = node.next
            assert previous_node is not None and next_node is not None
            previous_node.next = next_node
            next_node.previous = previous_node
            if node is self._head:
                self._head = next_node
            if node is self._cursor:
                self._cursor = next_node

        node.next = None
        node.previous = None
        self._size -= 1
        return True

    def find(self, value: T) -> Optional[DoublyNode[T]]:
        current = self._head
        for _ in range(self._size):
            assert current is not None
            if current.value == value:
                return current
            current = current.next
        return None

    def next(self) -> T:
        if self._cursor is None:
            raise IndexError("Cannot move through an empty circular list.")
        assert self._cursor.next is not None
        self._cursor = self._cursor.next
        return self._cursor.value

    def previous(self) -> T:
        if self._cursor is None:
            raise IndexError("Cannot move through an empty circular list.")
        assert self._cursor.previous is not None
        self._cursor = self._cursor.previous
        return self._cursor.value

    def move_to(self, value: T) -> bool:
        node = self.find(value)
        if node is None:
            return False
        self._cursor = node
        return True

    def to_list(self) -> list[T]:
        values: list[T] = []
        current = self._head
        for _ in range(self._size):
            assert current is not None
            values.append(current.value)
            current = current.next
        return values

    def to_list_backward(self) -> list[T]:
        values: list[T] = []
        current = self._head.previous if self._head is not None else None
        for _ in range(self._size):
            assert current is not None
            values.append(current.value)
            current = current.previous
        return values

    def is_empty(self) -> bool:
        return self._head is None

    def size(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        return iter(self.to_list())

    def __contains__(self, value: object) -> bool:
        return any(item == value for item in self)

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        if self._head is None:
            return "CircularDoublyLinkedList()"
        return f"CircularDoublyLinkedList({' <-> '.join(repr(value) for value in self)} <-> ...)"
