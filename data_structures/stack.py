from __future__ import annotations

from typing import Generic, Iterator, Optional, TypeVar

from data_structures.list_nodes import SinglyNode

T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self) -> None:
        self._top: Optional[SinglyNode[T]] = None
        self._size: int = 0

    def push(self, value: T) -> None:
        self._top = SinglyNode(value, self._top)
        self._size += 1

    def pop(self) -> T:
        if self._top is None:
            raise IndexError("Cannot pop from an empty stack.")
        removed = self._top
        self._top = removed.next
        self._size -= 1
        return removed.value

    def peek(self) -> T:
        if self._top is None:
            raise IndexError("Cannot peek an empty stack.")
        return self._top.value

    def is_empty(self) -> bool:
        return self._top is None

    def size(self) -> int:
        return self._size

    def contains(self, value: T) -> bool:
        return any(item == value for item in self)

    def clear(self) -> None:
        self._top = None
        self._size = 0

    def to_list(self) -> list[T]:
        return list(self)

    def __iter__(self) -> Iterator[T]:
        current = self._top
        while current is not None:
            yield current.value
            current = current.next

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return f"Stack(top -> {self.to_list()})"
