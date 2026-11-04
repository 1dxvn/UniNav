def building(name="Lab", **extra):
    return {"name": name, "x": 1.5, "y": 2.5, **extra}


def test_only_admins_can_modify_buildings(client, admin_headers, user_headers):
    assert client.post("/buildings", json=building()).status_code == 401
    assert client.post("/buildings", headers=user_headers, json=building()).status_code == 403
    assert client.post("/buildings", headers=admin_headers, json=building()).status_code == 201


def test_crud_roundtrip(client, admin_headers):
    created = client.post("/buildings", headers=admin_headers, json=building(faculty="Eng")).json()
    building_id = created["id"]
    assert created["floor"] == 0

    assert client.get(f"/buildings/{building_id}").json()["name"] == "Lab"
    updated = client.put(
        f"/buildings/{building_id}", headers=admin_headers, json={"floor": 3, "name": "Lab 2"}
    ).json()
    assert updated["floor"] == 3 and updated["name"] == "Lab 2" and updated["faculty"] == "Eng"

    assert client.delete(f"/buildings/{building_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/buildings/{building_id}").status_code == 404


def test_validation_and_conflicts(client, admin_headers):
    client.post("/buildings", headers=admin_headers, json=building())
    assert client.post("/buildings", headers=admin_headers, json=building()).status_code == 409
    assert client.post("/buildings", headers=admin_headers, json=building("X", floor=99)).status_code == 422
    other = client.post("/buildings", headers=admin_headers, json=building("Other")).json()
    clash = client.put(f"/buildings/{other['id']}", headers=admin_headers, json={"name": "Lab"})
    assert clash.status_code == 409


def test_filters_and_catalogs(client, admin_headers):
    client.post("/buildings/import", headers=admin_headers, json=[
        building("Library", faculty="Humanities", building_type="library", floor=1),
        building("Lab One", faculty="Engineering", building_type="laboratory", floor=2),
        building("Lab Two", faculty="Engineering", building_type="laboratory", floor=2),
    ])
    assert len(client.get("/buildings", params={"search": "lab"}).json()) == 2
    assert len(client.get("/buildings", params={"faculty": "Engineering"}).json()) == 2
    assert len(client.get("/buildings", params={"floor": 1}).json()) == 1
    assert client.get("/buildings/faculties").json() == ["Engineering", "Humanities"]
    assert client.get("/buildings/types").json() == ["laboratory", "library"]


def test_import_rejects_duplicates(client, admin_headers):
    assert client.post("/buildings/import", headers=admin_headers, json=[]).status_code == 400
    repeated = [building("Same"), building("Same")]
    assert client.post("/buildings/import", headers=admin_headers, json=repeated).status_code == 409
    client.post("/buildings", headers=admin_headers, json=building("Taken"))
    assert client.post("/buildings/import", headers=admin_headers, json=[building("Taken")]).status_code == 409


def test_nearest_and_neighbors(client, campus):
    nearest = client.get("/buildings/nearest", params={"x": 1, "y": 0, "limit": 2}).json()
    assert [item["building"]["name"] for item in nearest] == ["A", "B"]

    neighbors = client.get(f"/buildings/{campus['B']}/neighbors").json()
    assert {item["building"]["name"] for item in neighbors} == {"A", "C"}
    assert client.get(f"/buildings/{campus['D']}/neighbors").json() == []


def test_floors_catalog_counts_places(client, admin_headers):
    client.post("/buildings", headers=admin_headers, json=building("Roof", floor=7))
    floors = {item["level"]: item for item in client.get("/floors").json()}
    assert len(floors) == 8
    assert floors[7]["name"] == "Roof" and floors[7]["building_count"] == 1
