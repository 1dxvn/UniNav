from tests.conftest import PASSWORD


def test_change_password(client, user_headers):
    wrong = client.put(
        "/users/me/password",
        headers=user_headers,
        json={"current_password": "wrong", "new_password": "newsecret1"},
    )
    assert wrong.status_code == 400

    ok = client.put(
        "/users/me/password",
        headers=user_headers,
        json={"current_password": PASSWORD, "new_password": "newsecret1"},
    )
    assert ok.status_code == 204
    assert client.post(
        "/auth/login", json={"username": "regular_user", "password": "newsecret1"}
    ).status_code == 200


def test_delete_account_removes_the_user(client, user_headers):
    assert client.delete("/users/me", headers=user_headers).status_code == 204
    assert client.get("/auth/me", headers=user_headers).status_code == 401


def test_stats_reflect_calculated_routes(client, campus, user_headers):
    empty = client.get("/users/me/stats", headers=user_headers).json()
    assert empty["total_routes"] == 0 and empty["most_visited_destination"] is None

    for destination in ("B", "B", "C"):
        client.post(
            "/routes/calculate",
            headers=user_headers,
            json={"origin_id": campus["A"], "destination_id": campus[destination]},
        )
    stats = client.get("/users/me/stats", headers=user_headers).json()
    assert stats["total_routes"] == 3
    assert stats["most_visited_destination"] == "B"
    assert stats["total_distance"] > 0
