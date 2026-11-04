from data_structures.circular_doubly_linked_list import CircularDoublyLinkedList
from data_structures.doubly_linked_list import DoublyLinkedList
from data_structures.queue import Queue
from data_structures.stack import Stack


def run() -> None:
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


if __name__ == "__main__":
    run()
