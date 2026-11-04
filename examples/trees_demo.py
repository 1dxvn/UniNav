from data_structures.avl_tree import AVLTree
from data_structures.nary_tree import NaryTree


def run() -> None:
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


if __name__ == "__main__":
    run()
