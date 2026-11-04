from __future__ import annotations

from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class SinglyNode(Generic[T]):
    def __init__(self, value: T, next_node: Optional[SinglyNode[T]] = None) -> None:
        self.value: T = value
        self.next: Optional[SinglyNode[T]] = next_node


class DoublyNode(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value: T = value
        self.next: Optional[DoublyNode[T]] = None
        self.previous: Optional[DoublyNode[T]] = None

    def __repr__(self) -> str:
        return f"DoublyNode({self.value!r})"
