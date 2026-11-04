def test_paths_require_admin(client, campus, user_headers):
    body = {"source_id": campus["C"], "target_id": campus["D"]}
    assert client.post("/paths", headers=user_headers, json=body).status_code == 403
    assert client.delete("/paths/1", headers=user_headers).status_code == 403


def test_default_weight_is_straight_line_distance(client, campus, admin_headers):
    created = client.post(
        "/paths", headers=admin_headers, json={"source_id": campus["C"], "target_id": campus["D"]}
    ).json()
    assert round(created["weight"], 2) == round((440**2 + 500**2) ** 0.5, 2)
    assert created["kind"] == "corridor" and created["bidirectional"] is True


def test_weight_cannot_beat_the_straight_line(client, campus, admin_headers):
    created = client.post(
        "/paths",
        headers=admin_headers,
        json={"source_id": campus["C"], "target_id": campus["D"], "weight": 1},
    ).json()
    assert created["weight"] > 1


def test_invalid_paths(client, campus, admin_headers):
    same = {"source_id": campus["A"], "target_id": campus["A"]}
    assert client.post("/paths", headers=admin_headers, json=same).status_code == 400
    missing = {"source_id": campus["A"], "target_id": 9999}
    assert client.post("/paths", headers=admin_headers, json=missing).status_code == 404
    reverse = {"source_id": campus["B"], "target_id": campus["A"]}
    assert client.post("/paths", headers=admin_headers, json=reverse).status_code == 409
    negative = {"source_id": campus["C"], "target_id": campus["D"], "weight": -5}
    assert client.post("/paths", headers=admin_headers, json=negative).status_code == 422


def test_update_and_delete_rebuild_the_graph(client, campus, admin_headers):
    paths = client.get("/paths").json()
    a_to_c = next(p for p in paths if p["source_id"] == campus["A"] and p["target_id"] == campus["C"])
    b_to_c = next(p for p in paths if p["source_id"] == campus["B"] and p["target_id"] == campus["C"])
    assert a_to_c["weight"] == 200

    route = {"origin_id": campus["A"], "destination_id": campus["C"]}

    def shortest():
        return client.post("/routes/compare", json=route).json()["results"][0]["path"]

    assert shortest() == ["A", "B", "C"]

    client.put(f"/paths/{b_to_c['id']}", headers=admin_headers, json={"weight": 500})
    assert shortest() == ["A", "C"]

    client.delete(f"/paths/{a_to_c['id']}", headers=admin_headers)
    assert client.get(f"/paths/{a_to_c['id']}").status_code == 404
    assert shortest() == ["A", "B", "C"]


def test_deleting_a_building_removes_its_paths(client, campus, admin_headers):
    client.delete(f"/buildings/{campus['B']}", headers=admin_headers)
    remaining = client.get("/paths").json()
    assert all(campus["B"] not in (p["source_id"], p["target_id"]) for p in remaining)
    assert len(remaining) == 1


def test_filter_paths_by_building(client, campus):
    assert len(client.get("/paths", params={"building_id": campus["B"]}).json()) == 2
