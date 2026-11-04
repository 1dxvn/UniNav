from tests.conftest import register_and_login


def go(client, headers, campus, origin, destination, times=1):
    for _ in range(times):
        client.post(
            "/routes/calculate",
            headers=headers,
            json={"origin_id": campus[origin], "destination_id": campus[destination]},
        )


def test_ranking_is_empty_without_visits(client, campus):
    assert client.get("/rankings/places").json() == []


def test_places_are_ranked_by_visits_across_all_users(client, campus, user_headers):
    other = register_and_login(client, "other_visitor")
    go(client, user_headers, campus, "A", "B", times=2)
    go(client, other, campus, "A", "B", times=1)
    go(client, user_headers, campus, "A", "C", times=2)
    go(client, other, campus, "B", "A", times=1)

    ranking = client.get("/rankings/places").json()
    assert [(r["rank"], r["building_name"], r["visits"]) for r in ranking] == [
        (1, "B", 3),
        (2, "C", 2),
        (3, "A", 1),
    ]
    assert ranking[0]["floor"] == 0


def test_ties_are_listed_alphabetically(client, campus, user_headers):
    go(client, user_headers, campus, "A", "C")
    go(client, user_headers, campus, "A", "B")
    assert [r["building_name"] for r in client.get("/rankings/places").json()] == ["B", "C"]


def test_limit(client, campus, user_headers):
    go(client, user_headers, campus, "A", "B", times=3)
    go(client, user_headers, campus, "A", "C", times=2)
    assert [r["building_name"] for r in client.get("/rankings/places", params={"limit": 1}).json()] == ["B"]
    assert client.get("/rankings/places", params={"limit": 0}).status_code == 422


def test_ranking_forgets_deleted_places(client, campus, user_headers, admin_headers):
    go(client, user_headers, campus, "A", "B", times=2)
    client.delete(f"/buildings/{campus['B']}", headers=admin_headers)
    assert client.get("/rankings/places").json() == []
