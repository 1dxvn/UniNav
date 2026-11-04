from __future__ import annotations

from typing import Any, Generic, Optional, Protocol, TypeVar, Union


class SupportsLessThan(Protocol):
    def __lt__(self, other: Any) -> bool: ...


K = TypeVar("K", bound=SupportsLessThan)
V = TypeVar("V")


class AVLNode(Generic[K, V]):
    def __init__(self, key: K, value: V) -> None:
        self.key: K = key
        self.values: list[V] = [value]
        self.left: Optional[AVLNode[K, V]] = None
        self.right: Optional[AVLNode[K, V]] = None
        self.height: int = 1

    def __repr__(self) -> str:
        return f"AVLNode(key={self.key!r}, values={self.values!r}, height={self.height})"


class AVLTree(Generic[K, V]):
    def __init__(self) -> None:
        self._root: Optional[AVLNode[K, V]] = None
        self._size: int = 0

    @property
    def root(self) -> Optional[AVLNode[K, V]]:
        return self._root

    def insert(self, key: K, value: V) -> None:
        self._root = self._insert(self._root, key, value)
        self._size += 1

    def search(self, key: K) -> Optional[list[V]]:
        node = self._find_node(key)
        return list(node.values) if node is not None else None

    def contains(self, key: K) -> bool:
        return self._find_node(key) is not None

    def height(self) -> int:
        return self._height(self._root)

    def balance_factor(self, node: Optional[AVLNode[K, V]]) -> int:
        if node is None:
            return 0
        return self._height(node.left) - self._height(node.right)

    def in_order(self) -> list[tuple[K, V]]:
        result: list[tuple[K, V]] = []
        stack: list[AVLNode[K, V]] = []
        current = self._root

        while stack or current is not None:
            while current is not None:
                stack.append(current)
                current = current.left
            current = stack.pop()
            result.extend((current.key, value) for value in current.values)
            current = current.right

        return result

    def reverse_in_order(self) -> list[tuple[K, V]]:
        result: list[tuple[K, V]] = []
        stack: list[AVLNode[K, V]] = []
        current = self._root

        while stack or current is not None:
            while current is not None:
                stack.append(current)
                current = current.right
            current = stack.pop()
            result.extend((current.key, value) for value in current.values)
            current = current.left

        return result

    def is_empty(self) -> bool:
        return self._root is None

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        return self._find_node(key) is not None

    def __repr__(self) -> str:
        return f"AVLTree(size={self._size}, height={self.height()})"

    def _insert(self, node: Optional[AVLNode[K, V]], key: K, value: V) -> AVLNode[K, V]:
        if node is None:
            return AVLNode(key, value)

        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif node.key < key:
            node.right = self._insert(node.right, key, value)
        else:
            node.values.append(value)
            return node

        self._update_height(node)
        return self._rebalance(node)

    def _rebalance(self, node: AVLNode[K, V]) -> AVLNode[K, V]:
        balance = self.balance_factor(node)

        if balance > 1:
            if self.balance_factor(node.left) >= 0:
                return self._rotate_right(node)
            return self._rotate_left_right(node)

        if balance < -1:
            if self.balance_factor(node.right) <= 0:
                return self._rotate_left(node)
            return self._rotate_right_left(node)

        return node

    def _rotate_left(self, node: AVLNode[K, V]) -> AVLNode[K, V]:
        new_root = node.right
        assert new_root is not None
        node.right = new_root.left
        new_root.left = node

        self._update_height(node)
        self._update_height(new_root)
        return new_root

    def _rotate_right(self, node: AVLNode[K, V]) -> AVLNode[K, V]:
        new_root = node.left
        assert new_root is not None
        node.left = new_root.right
        new_root.right = node

        self._update_height(node)
        self._update_height(new_root)
        return new_root

    def _rotate_left_right(self, node: AVLNode[K, V]) -> AVLNode[K, V]:
        assert node.left is not None
        node.left = self._rotate_left(node.left)
        return self._rotate_right(node)

    def _rotate_right_left(self, node: AVLNode[K, V]) -> AVLNode[K, V]:
        assert node.right is not None
        node.right = self._rotate_right(node.right)
        return self._rotate_left(node)

    def _find_node(self, key: Any) -> Optional[AVLNode[K, V]]:
        current = self._root
        while current is not None:
            if key < current.key:
                current = current.left
            elif current.key < key:
                current = current.right
            else:
                return current
        return None

    @staticmethod
    def _height(node: Optional[AVLNode[K, V]]) -> int:
        return node.height if node is not None else 0

    def _update_height(self, node: AVLNode[K, V]) -> None:
        node.height = 1 + max(self._height(node.left), self._height(node.right))
