from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class MaxHeap(Generic[T]):
    """Binary max-heap. Equal priorities come out in insertion order."""

    def __init__(self) -> None:
        self._entries: list[tuple[float, int, T]] = []
        self._insertion_count: int = 0

    def __len__(self) -> int:
        return len(self._entries)

    def is_empty(self) -> bool:
        return not self._entries

    def push(self, item: T, priority: float) -> None:
        self._entries.append((priority, self._insertion_count, item))
        self._insertion_count += 1
        self._sift_up(len(self._entries) - 1)

    def peek_max(self) -> tuple[T, float]:
        if self.is_empty():
            raise IndexError("Cannot peek an empty heap.")
        priority, _, item = self._entries[0]
        return item, priority

    def pop_max(self) -> tuple[T, float]:
        if self.is_empty():
            raise IndexError("Cannot pop from an empty heap.")

        priority, _, item = self._entries[0]
        last = self._entries.pop()
        if self._entries:
            self._entries[0] = last
            self._sift_down(0)
        return item, priority

    def _outranks(self, first: int, second: int) -> bool:
        first_priority, first_order, _ = self._entries[first]
        second_priority, second_order, _ = self._entries[second]
        if first_priority != second_priority:
            return first_priority > second_priority
        return first_order < second_order

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if not self._outranks(index, parent):
                break
            self._swap(index, parent)
            index = parent

    def _sift_down(self, index: int) -> None:
        size = len(self._entries)
        while True:
            left = 2 * index + 1
            right = left + 1
            largest = index

            if left < size and self._outranks(left, largest):
                largest = left
            if right < size and self._outranks(right, largest):
                largest = right

            if largest == index:
                return
            self._swap(index, largest)
            index = largest

    def _swap(self, first: int, second: int) -> None:
        self._entries[first], self._entries[second] = self._entries[second], self._entries[first]

    def __repr__(self) -> str:
        return f"MaxHeap(size={len(self)})"
