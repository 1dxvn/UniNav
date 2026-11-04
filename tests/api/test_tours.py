import pytest

from tests.conftest import register_and_login


@pytest.fixture()
def tour(client, campus, admin_headers):
    response = client.post(
        "/tours",
        headers=admin_headers,
        json={
            "name": "Highlights",
            "description": "A short walk",
            "building_ids": [campus["A"], campus["B"], campus["C"]],
        },
    )
    assert response.status_code == 201
    return response.json()


def stop_name(response):
    return response.json()["current_stop"]["building_name"]


def test_tour_keeps_the_order_of_its_stops(client, tour):
    assert [stop["building_name"] for stop in tour["stops"]] == ["A", "B", "C"]
    assert [stop["position"] for stop in tour["stops"]] == [1, 2, 3]
    assert client.get(f"/tours/{tour['id']}").json() == tour
    assert client.get("/tours").json()[0]["stop_count"] == 3


def test_walking_the_tour_wraps_around_in_both_directions(client, tour, user_headers):
    started = client.post(f"/tours/{tour['id']}/start", headers=user_headers)
    assert stop_name(started) == "A" and started.json()["total_stops"] == 3

    names = [stop_name(client.post("/tours/session/next", headers=user_headers)) for _ in range(4)]
    assert names == ["B", "C", "A", "B"]

    names = [stop_name(client.post("/tours/session/previous", headers=user_headers)) for _ in range(3)]
    assert names == ["A", "C", "B"]
    assert stop_name(client.get("/tours/session", headers=user_headers)) == "B"


def test_each_user_has_their_own_position(client, tour, user_headers):
    other = register_and_login(client, "other_visitor")
    for headers in (user_headers, other):
        client.post(f"/tours/{tour['id']}/start", headers=headers)
    client.post("/tours/session/next", headers=user_headers)
    assert stop_name(client.get("/tours/session", headers=user_headers)) == "B"
    assert stop_name(client.get("/tours/session", headers=other)) == "A"


def test_ending_the_tour(client, tour, user_headers):
    assert client.get("/tours/session", headers=user_headers).status_code == 404
    assert client.post("/tours/session/next", headers=user_headers).status_code == 404
    client.post(f"/tours/{tour['id']}/start", headers=user_headers)
    assert client.delete("/tours/session", headers=user_headers).status_code == 204
    assert client.get("/tours/session", headers=user_headers).status_code == 404


def test_restarting_goes_back_to_the_first_stop(client, tour, user_headers):
    client.post(f"/tours/{tour['id']}/start", headers=user_headers)
    client.post("/tours/session/next", headers=user_headers)
    assert stop_name(client.post(f"/tours/{tour['id']}/start", headers=user_headers)) == "A"


def test_only_admins_manage_tours(client, campus, tour, user_headers):
    body = {"name": "Mine", "building_ids": [campus["A"], campus["B"]]}
    assert client.post("/tours", headers=user_headers, json=body).status_code == 403
    assert client.delete(f"/tours/{tour['id']}", headers=user_headers).status_code == 403
    assert client.post(f"/tours/{tour['id']}/start").status_code == 401


def test_invalid_tours(client, campus, tour, admin_headers):
    def create(**changes):
        body = {"name": "New", "building_ids": [campus["A"], campus["B"]], **changes}
        return client.post("/tours", headers=admin_headers, json=body).status_code

    assert create(name="Highlights") == 409
    assert create(building_ids=[campus["A"]]) == 422
    assert create(building_ids=[campus["A"], campus["A"]]) == 400
    assert create(building_ids=[campus["A"], 9999]) == 404
    assert client.get("/tours/9999").status_code == 404


def test_deleting_a_tour_ends_its_sessions(client, tour, user_headers, admin_headers):
    client.post(f"/tours/{tour['id']}/start", headers=user_headers)
    assert client.delete(f"/tours/{tour['id']}", headers=admin_headers).status_code == 204
    assert client.get("/tours/session", headers=user_headers).status_code == 404
    assert client.get(f"/tours/{tour['id']}").status_code == 404


def test_deleting_a_place_removes_it_from_tours(client, campus, tour, admin_headers):
    client.delete(f"/buildings/{campus['B']}", headers=admin_headers)
    names = [stop["building_name"] for stop in client.get(f"/tours/{tour['id']}").json()["stops"]]
    assert names == ["A", "C"]
