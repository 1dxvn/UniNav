from __future__ import annotations

from typing import Generic, Iterator, Optional, TypeVar

T = TypeVar("T")


class _SinglyNode(Generic[T]):
    def __init__(self, value: T, next_node: Optional[_SinglyNode[T]] = None) -> None:
        self.value: T = value
        self.next: Optional[_SinglyNode[T]] = next_node


class DoublyNode(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value: T = value
        self.next: Optional[DoublyNode[T]] = None
        self.previous: Optional[DoublyNode[T]] = None

    def __repr__(self) -> str:
        return f"DoublyNode({self.value!r})"


class Stack(Generic[T]):
    def __init__(self) -> None:
        self._top: Optional[_SinglyNode[T]] = None
        self._size: int = 0

    def push(self, value: T) -> None:
        self._top = _SinglyNode(value, self._top)
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


class Queue(Generic[T]):
    def __init__(self) -> None:
        self._front: Optional[_SinglyNode[T]] = None
        self._rear: Optional[_SinglyNode[T]] = None
        self._size: int = 0

    def enqueue(self, value: T) -> None:
        new_node = _SinglyNode(value)
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


if __name__ == "__main__":
    print("=== Stack: avatar navigation history ===")
    history: Stack[str] = Stack()
    for location in ["Entrance", "Library", "Cafeteria", "Building A"]:
        history.push(location)
        print(f"  Visit {location:<11} history: {history.to_list()}")
    print(f"  Current location: {history.peek()}")
    for _ in range(2):
        left_location = history.pop()
        print(f"  Back from {left_location:<11} now at: {history.peek()}")
    print(f"  Size: {history.size()} | Was 'Library' visited? {history.contains('Library')}")

    print("\n=== Queue: cafeteria turns ===")
    cafeteria: Queue[str] = Queue()
    for student in ["Ana", "Luis", "Sofia", "Mateo"]:
        cafeteria.enqueue(student)
    print(f"  Waiting line: {cafeteria.to_list()}")
    print(f"  Sofia's position: {cafeteria.position_of('Sofia') + 1}")
    print(f"  Next to be served: {cafeteria.peek()}")
    while not cafeteria.is_empty():
        print(f"  Serving {cafeteria.dequeue():<6} remaining: {cafeteria.size()}")

    print("\n=== DoublyLinkedList: options menu ===")
    menu: DoublyLinkedList[str] = DoublyLinkedList()
    for option in ["Map", "Ranking", "Settings"]:
        menu.append(option)
    menu.prepend("Home")
    menu.append("Exit")
    print(f"  Forward:  {menu.to_list_forward()}")
    print(f"  Backward: {menu.to_list_backward()}")

    selected = menu.find("Ranking")
    if selected is not None:
        print(f"  Selected: {selected.value}")
        if selected.next is not None:
            selected = selected.next
            print(f"  Right ->  {selected.value}")
        if selected.previous is not None and selected.previous.previous is not None:
            selected = selected.previous.previous
            print(f"  Left x2 -> {selected.value}")

    print(f"  Remove 'Settings': {menu.remove('Settings')}")
    print(f"  Remove 'Help':     {menu.remove('Help')}")
    print(f"  Menu now: {menu}")

    print("\n=== CircularDoublyLinkedList: day/night cycle ===")
    day_cycle: CircularDoublyLinkedList[str] = CircularDoublyLinkedList()
    for phase in ["Dawn", "Morning", "Afternoon", "Dusk", "Night"]:
        day_cycle.append(phase)
    print(f"  Cycle: {day_cycle}")
    phases_seen = [day_cycle.current] + [day_cycle.next() for _ in range(6)]
    print(f"  Advancing 6 steps: {' -> '.join(phases_seen)}")
    print(f"  One step back: {day_cycle.previous()}")

    print("\n=== CircularDoublyLinkedList: ambient playlist ===")
    playlist: CircularDoublyLinkedList[str] = CircularDoublyLinkedList()
    for track in ["Rain on Campus", "Library Lo-Fi", "Morning Birds", "Night Crickets"]:
        playlist.append(track)
    print(f"  Now playing: {playlist.current}")
    print(f"  Previous (wraps to the end): {playlist.previous()}")
    print(f"  Next (wraps to the start):   {playlist.next()}")
    print(f"  Remove 'Library Lo-Fi': {playlist.remove('Library Lo-Fi')}")
    print(f"  Playlist forward:  {playlist.to_list()}")
    print(f"  Playlist backward: {playlist.to_list_backward()}")