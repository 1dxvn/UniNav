from __future__ import annotations

from typing import Generic, Iterator, Optional, TypeVar

from data_structures.list_nodes import DoublyNode

T = TypeVar("T")


class DoublyLinkedList(Generic[T]):
    def __init__(self) -> None:
        self._head: Optional[DoublyNode[T]] = None
        self._tail: Optional[DoublyNode[T]] = None
        self._size: int = 0

    @property
    def head(self) -> Optional[DoublyNode[T]]:
        return self._head

    @property
    def tail(self) -> Optional[DoublyNode[T]]:
        return self._tail

    def append(self, value: T) -> DoublyNode[T]:
        new_node = DoublyNode(value)
        if self._tail is None:
            self._head = new_node
        else:
            new_node.previous = self._tail
            self._tail.next = new_node
        self._tail = new_node
        self._size += 1
        return new_node

    def prepend(self, value: T) -> DoublyNode[T]:
        new_node = DoublyNode(value)
        if self._head is None:
            self._tail = new_node
        else:
            new_node.next = self._head
            self._head.previous = new_node
        self._head = new_node
        self._size += 1
        return new_node

    def pop_front(self) -> T:
        if self._head is None:
            raise IndexError("Cannot pop from an empty list.")
        node = self._head
        value = node.value
        self._unlink(node)
        return value

    def truncate_after(self, node: DoublyNode[T]) -> int:
        """Removes every node that comes after `node`. Returns how many were removed."""
        removed = 0
        current = node.next
        while current is not None:
            following = current.next
            self._unlink(current)
            current = following
            removed += 1
        return removed

    def remove(self, value: T) -> bool:
        node = self.find(value)
        if node is None:
            return False
        self._unlink(node)
        return True

    def find(self, value: T) -> Optional[DoublyNode[T]]:
        current = self._head
        while current is not None:
            if current.value == value:
                return current
            current = current.next
        return None

    def to_list_forward(self) -> list[T]:
        values: list[T] = []
        current = self._head
        while current is not None:
            values.append(current.value)
            current = current.next
        return values

    def to_list_backward(self) -> list[T]:
        values: list[T] = []
        current = self._tail
        while current is not None:
            values.append(current.value)
            current = current.previous
        return values

    def is_empty(self) -> bool:
        return self._head is None

    def size(self) -> int:
        return self._size

    def _unlink(self, node: DoublyNode[T]) -> None:
        if node.previous is None:
            self._head = node.next
        else:
            node.previous.next = node.next

        if node.next is None:
            self._tail = node.previous
        else:
            node.next.previous = node.previous

        node.next = None
        node.previous = None
        self._size -= 1

    def __iter__(self) -> Iterator[T]:
        return iter(self.to_list_forward())

    def __reversed__(self) -> Iterator[T]:
        return iter(self.to_list_backward())

    def __contains__(self, value: object) -> bool:
        return any(item == value for item in self)

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return f"DoublyLinkedList({' <-> '.join(repr(value) for value in self)})"
