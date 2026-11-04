from __future__ import annotations

from typing import Generic, Iterator, Optional, TypeVar

from data_structures.list_nodes import SinglyNode

T = TypeVar("T")


class Queue(Generic[T]):
    def __init__(self) -> None:
        self._front: Optional[SinglyNode[T]] = None
        self._rear: Optional[SinglyNode[T]] = None
        self._size: int = 0

    def enqueue(self, value: T) -> None:
        new_node = SinglyNode(value)
        if self._rear is None:
            self._front = new_node
        else:
            self._rear.next = new_node
        self._rear = new_node
        self._size += 1

    def dequeue(self) -> T:
        if self._front is None:
            raise IndexError("Cannot dequeue from an empty queue.")
        removed = self._front
        self._front = removed.next
        if self._front is None:
            self._rear = None
        self._size -= 1
        return removed.value

    def remove(self, value: T) -> bool:
        previous: Optional[SinglyNode[T]] = None
        current = self._front
        while current is not None:
            if current.value == value:
                if previous is None:
                    self._front = current.next
                else:
                    previous.next = current.next
                if current is self._rear:
                    self._rear = previous
                self._size -= 1
                return True
            previous, current = current, current.next
        return False

    def peek(self) -> T:
        if self._front is None:
            raise IndexError("Cannot peek an empty queue.")
        return self._front.value

    def is_empty(self) -> bool:
        return self._front is None

    def size(self) -> int:
        return self._size

    def contains(self, value: T) -> bool:
        return any(item == value for item in self)

    def position_of(self, value: T) -> int:
        for position, item in enumerate(self):
            if item == value:
                return position
        return -1

    def to_list(self) -> list[T]:
        return list(self)

    def __iter__(self) -> Iterator[T]:
        current = self._front
        while current is not None:
            yield current.value
            current = current.next

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return f"Queue(front -> {self.to_list()})"
