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


class NaryNode:
    def __init__(self, name: str, data: Optional[dict[str, Any]] = None) -> None:
        if not name:
            raise ValueError("Node name cannot be empty.")
        self.name: str = name
        self.data: dict[str, Any] = data if data is not None else {}
        self.children: list[NaryNode] = []
        self.parent: Optional[NaryNode] = None

    def add_child(self, child: NaryNode) -> NaryNode:
        if child.parent is not None:
            raise ValueError(f"Node '{child.name}' already has a parent.")
        child.parent = self
        self.children.append(child)
        return child

    def is_leaf(self) -> bool:
        return not self.children

    def depth(self) -> int:
        levels = 0
        current = self.parent
        while current is not None:
            levels += 1
            current = current.parent
        return levels

    def __repr__(self) -> str:
        return f"NaryNode(name={self.name!r}, children={len(self.children)})"


class NaryTree:
    def __init__(self, root_name: str, root_data: Optional[dict[str, Any]] = None) -> None:
        self._root: NaryNode = NaryNode(root_name, root_data)
        self._size: int = 1

    @property
    def root(self) -> NaryNode:
        return self._root

    def add_child(
        self,
        parent: Union[str, NaryNode],
        child_name: str,
        data: Optional[dict[str, Any]] = None,
    ) -> NaryNode:
        parent_node = self._resolve_parent(parent)
        child = parent_node.add_child(NaryNode(child_name, data))
        self._size += 1
        return child

    def dfs(self) -> list[NaryNode]:
        visited: list[NaryNode] = []
        stack: list[NaryNode] = [self._root]

        while stack:
            node = stack.pop()
            visited.append(node)
            stack.extend(reversed(node.children))

        return visited

    def find(self, name: str) -> Optional[NaryNode]:
        stack: list[NaryNode] = [self._root]
        while stack:
            node = stack.pop()
            if node.name == name:
                return node
            stack.extend(reversed(node.children))
        return None

    def path_to_root(self, node: NaryNode) -> list[NaryNode]:
        path: list[NaryNode] = []
        current: Optional[NaryNode] = node
        while current is not None:
            path.append(current)
            current = current.parent
        path.reverse()
        return path

    def height(self) -> int:
        tallest = 0
        stack: list[tuple[NaryNode, int]] = [(self._root, 1)]
        while stack:
            node, level = stack.pop()
            tallest = max(tallest, level)
            stack.extend((child, level + 1) for child in node.children)
        return tallest

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return f"NaryTree(root={self._root.name!r}, size={self._size})"

    def to_text(self) -> str:
        lines: list[str] = []
        for node in self.dfs():
            lines.append(f"{'    ' * node.depth()}{node.name}")
        return "\n".join(lines)

    def _resolve_parent(self, parent: Union[str, NaryNode]) -> NaryNode:
        if isinstance(parent, NaryNode):
            if self.path_to_root(parent)[0] is not self._root:
                raise ValueError(f"Node '{parent.name}' does not belong to this tree.")
            return parent

        parent_node = self.find(parent)
        if parent_node is None:
            raise KeyError(f"Parent node '{parent}' does not exist.")
        return parent_node


if __name__ == "__main__":
    print("=== AVL Tree: student ranking ===")
    ranking: AVLTree[float, str] = AVLTree()
    students: list[tuple[str, float]] = [
        ("Ana", 88.5),
        ("Luis", 92.0),
        ("Sofia", 75.0),
        ("Carlos", 92.0),
        ("Valentina", 64.5),
        ("Mateo", 99.0),
        ("Isabella", 81.0),
        ("Santiago", 70.0),
    ]
    for student, score in students:
        ranking.insert(score, student)

    print(ranking)
    print(f"Root key: {ranking.root.key if ranking.root else None}")
    print(f"Root balance factor: {ranking.balance_factor(ranking.root)}")
    print("Ascending (in-order):", ranking.in_order())
    print("Leaderboard:")
    for position, (score, student) in enumerate(ranking.reverse_in_order(), start=1):
        print(f"  {position}. {student:<10} {score}")
    print("Search 92.0:", ranking.search(92.0))
    print("Search 50.0:", ranking.search(50.0))

    print("\n=== AVL Tree: rotation cases ===")
    rotation_cases: dict[str, list[int]] = {
        "Left-Left (single right)": [30, 20, 10],
        "Right-Right (single left)": [10, 20, 30],
        "Left-Right (double)": [30, 10, 20],
        "Right-Left (double)": [10, 30, 20],
    }
    for case, keys in rotation_cases.items():
        tree: AVLTree[int, str] = AVLTree()
        for key in keys:
            tree.insert(key, f"value-{key}")
        root_key = tree.root.key if tree.root else None
        print(f"  {case:<26} insert {keys} -> root {root_key}, height {tree.height()}")

    print("\n=== N-ary Tree: campus hierarchy ===")
    campus = NaryTree("University")
    campus.add_child("University", "Faculty of Engineering")
    campus.add_child("University", "Faculty of Health Sciences")
    campus.add_child("Faculty of Engineering", "Building A", {"floors": 4})
    campus.add_child("Faculty of Engineering", "Building B", {"floors": 3})
    campus.add_child("Faculty of Health Sciences", "Building C", {"floors": 5})
    campus.add_child("Building A", "Room A-101", {"capacity": 40})
    campus.add_child("Building A", "Room A-102", {"capacity": 35})
    campus.add_child("Building B", "Lab B-201", {"capacity": 25})
    campus.add_child("Building C", "Room C-301", {"capacity": 60})

    print(campus)
    print(f"Height: {campus.height()} levels")
    print(campus.to_text())
    print("DFS:", [node.name for node in campus.dfs()])

    room = campus.find("Lab B-201")
    if room is not None:
        location = " > ".join(node.name for node in campus.path_to_root(room))
        print(f"Found 'Lab B-201': {location} (capacity {room.data['capacity']})")
    print("Find 'Gym':", campus.find("Gym"))