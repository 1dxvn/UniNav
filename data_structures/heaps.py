from __future__ import annotations

Node = str


class MinPriorityQueue:
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
