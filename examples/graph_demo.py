from data_structures.graph import WeightedDirectedGraph


def run() -> None:
        campus = WeightedDirectedGraph()

        campus.add_node("Entrance", (0, 0))
        campus.add_node("Library", (100, 0))
        campus.add_node("Building A", (100, 100))
        campus.add_node("Cafeteria", (200, 50))
        campus.add_node("Auditorium", (300, 100))

        campus.add_edge("Entrance", "Library", 100, bidirectional=True)
        campus.add_edge("Entrance", "Building A", 150, bidirectional=True)
        campus.add_edge("Library", "Cafeteria", 120, bidirectional=True)
        campus.add_edge("Building A", "Cafeteria", 115, bidirectional=True)
        campus.add_edge("Cafeteria", "Auditorium", 115, bidirectional=True)
        campus.add_edge("Building A", "Auditorium", 260)

        print(campus, end="\n\n")
        print("Dijkstra:", campus.dijkstra("Entrance", "Auditorium"))
        print("A*:      ", campus.a_star("Entrance", "Auditorium"))


if __name__ == "__main__":
    run()
