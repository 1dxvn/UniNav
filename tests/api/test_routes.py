def route(campus, origin, destination, **extra):
    return {"origin_id": campus[origin], "destination_id": campus[destination], **extra}


def test_calculate_requires_login(client, campus):
    assert client.post("/routes/calculate", json=route(campus, "A", "C")).status_code == 401


def test_shortest_path_with_both_algorithms(client, campus, user_headers):
    for algorithm in ("a_star", "dijkstra"):
        body = route(campus, "A", "C", algorithm=algorithm)
        result = client.post("/routes/calculate", headers=user_headers, json=body).json()
        assert result["path"] == ["A", "B", "C"]
        assert result["distance"] == 60
        assert [step["origin_name"] for step in result["steps"]] == ["A", "B"]


def test_compare_returns_every_algorithm(client, campus):
    result = client.post("/routes/compare", json=route(campus, "A", "C")).json()
    assert {item["algorithm"] for item in result["results"]} == {"a_star", "dijkstra"}
    assert len({item["distance"] for item in result["results"]}) == 1


def test_errors(client, campus, user_headers):
    isolated = client.post("/routes/calculate", headers=user_headers, json=route(campus, "A", "D"))
    assert isolated.status_code == 404 and "no route" in isolated.json()["detail"].lower()
    missing = {"origin_id": 9999, "destination_id": campus["A"]}
    assert client.post("/routes/calculate", headers=user_headers, json=missing).status_code == 404
    assert client.post("/routes/calculate", headers=user_headers, json={"origin_id": 0, "destination_id": 1}).status_code == 422


def test_multi_stop_adds_up_the_legs(client, campus):
    body = {"building_ids": [campus["A"], campus["B"], campus["C"]]}
    result = client.post("/routes/multi-stop", json=body).json()
    assert len(result["legs"]) == 2 and result["total_distance"] == 60
    assert client.post("/routes/multi-stop", json={"building_ids": [campus["A"]]}).status_code == 422


def test_avoiding_a_kind_of_path(client, campus, admin_headers):
    stairs = client.post(
        "/buildings/import",
        headers=admin_headers,
        json=[{"name": "Up", "x": 0, "y": 0, "floor": 1}, {"name": "Down", "x": 0, "y": 0}],
    ).json()
    up, down = stairs[0]["id"], stairs[1]["id"]
    client.post("/paths", headers=admin_headers, json={"source_id": down, "target_id": up, "kind": "stairs"})

    body = {"origin_id": down, "destination_id": up}
    assert client.post("/routes/compare", json=body).status_code == 200
    avoided = client.post("/routes/compare", json={**body, "avoid": ["stairs"]})
    assert avoided.status_code == 404


def test_popular_routes_are_ranked_by_frequency(client, campus, user_headers):
    for destination, times in (("B", 1), ("C", 3)):
        for _ in range(times):
            client.post("/routes/calculate", headers=user_headers, json=route(campus, "A", destination))
    popular = client.get("/routes/popular").json()
    assert [(p["destination_name"], p["frequency"]) for p in popular] == [("C", 3), ("B", 1)]
