from services.navigation_history import MAX_TRAIL_LENGTH
from tests.conftest import register_and_login


def visit(client, headers, building_id):
    return client.post("/navigation/visit", headers=headers, json={"building_id": building_id})


def names(client, headers):
    return [entry["building_name"] for entry in client.get("/navigation", headers=headers).json()["trail"]]


def current(response):
    return response.json()["current"]["building_name"]


def test_visiting_builds_a_trail(client, campus, user_headers):
    assert client.get("/navigation", headers=user_headers).json()["current"] is None
    for place in ("A", "B", "C"):
        state = visit(client, user_headers, campus[place])
    assert current(state) == "C"
    assert state.json()["can_go_back"] and not state.json()["can_go_forward"]
    assert names(client, user_headers) == ["A", "B", "C"]


def test_back_and_forward_move_along_the_trail(client, campus, user_headers):
    for place in ("A", "B", "C"):
        visit(client, user_headers, campus[place])

    assert current(client.post("/navigation/back", headers=user_headers)) == "B"
    assert current(client.post("/navigation/back", headers=user_headers)) == "A"
    assert client.post("/navigation/back", headers=user_headers).status_code == 409

    assert current(client.post("/navigation/forward", headers=user_headers)) == "B"
    trail = client.get("/navigation", headers=user_headers).json()["trail"]
    assert [(e["building_name"], e["is_current"]) for e in trail] == [("A", False), ("B", True), ("C", False)]


def test_visiting_after_going_back_discards_the_forward_places(client, campus, user_headers):
    for place in ("A", "B", "C"):
        visit(client, user_headers, campus[place])
    client.post("/navigation/back", headers=user_headers)
    client.post("/navigation/back", headers=user_headers)

    state = visit(client, user_headers, campus["D"])
    assert names(client, user_headers) == ["A", "D"]
    assert not state.json()["can_go_forward"]
    assert client.post("/navigation/forward", headers=user_headers).status_code == 409


def test_visiting_the_current_place_again_changes_nothing(client, campus, user_headers):
    visit(client, user_headers, campus["A"])
    visit(client, user_headers, campus["A"])
    assert names(client, user_headers) == ["A"]


def test_trail_is_private_and_can_be_cleared(client, campus, user_headers):
    other = register_and_login(client, "other_visitor")
    visit(client, user_headers, campus["A"])
    assert names(client, other) == []

    assert client.delete("/navigation", headers=user_headers).status_code == 204
    assert names(client, user_headers) == []


def test_errors(client, campus):
    assert client.get("/navigation").status_code == 401


def test_unknown_place(client, user_headers):
    assert visit(client, user_headers, 9999).status_code == 404
    assert client.post("/navigation/visit", headers=user_headers, json={"building_id": 0}).status_code == 422


def test_trail_keeps_only_the_latest_places(client, campus, user_headers):
    for index in range(MAX_TRAIL_LENGTH + 5):
        visit(client, user_headers, campus["A" if index % 2 == 0 else "B"])
    trail = client.get("/navigation", headers=user_headers).json()["trail"]
    assert len(trail) == MAX_TRAIL_LENGTH
    assert trail[-1]["is_current"]
