from __future__ import annotations

from typing import Any, Optional, Union


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
