def test_health_counts_places_and_edges(client, campus):
    health = client.get("/health").json()
    assert health == {"status": "ok", "buildings": 4, "edges": 6}


def test_graph_snapshot_lists_each_two_way_path_once(client, campus):
    graph = client.get("/graph").json()
    assert {node["name"] for node in graph["nodes"]} == {"A", "B", "C", "D"}
    assert len(graph["edges"]) == 3
    assert all(edge["bidirectional"] for edge in graph["edges"])


def test_graph_reload_is_admin_only(client, campus, user_headers, admin_headers):
    assert client.post("/graph/reload", headers=user_headers).status_code == 403
    assert client.post("/graph/reload", headers=admin_headers).json()["buildings"] == 4


def test_hierarchy_groups_buildings_by_faculty(client, admin_headers):
    client.post("/buildings/import", headers=admin_headers, json=[
        {"name": "Lab", "x": 0, "y": 0, "faculty": "Engineering"},
        {"name": "Hall", "x": 1, "y": 1, "faculty": "Engineering"},
        {"name": "Gate", "x": 2, "y": 2},
    ])
    tree = client.get("/campus/hierarchy").json()
    faculties = {child["name"]: child for child in tree["root"]["children"]}
    assert set(faculties) == {"Engineering", "Unassigned"}
    assert [c["name"] for c in faculties["Engineering"]["children"]] == ["Hall", "Lab"]
    assert tree["height"] == 3 and tree["total_nodes"] == 6
