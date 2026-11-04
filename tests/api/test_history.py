from tests.conftest import register_and_login


def visit(client, campus, headers, destination):
    client.post(
        "/routes/calculate",
        headers=headers,
        json={"origin_id": campus["A"], "destination_id": campus[destination]},
    )


def test_history_is_newest_first(client, campus, user_headers):
    visit(client, campus, user_headers, "B")
    visit(client, campus, user_headers, "C")
    history = client.get("/routes/history", headers=user_headers).json()
    assert [item["destination_name"] for item in history] == ["C", "B"]
    assert client.get("/routes/history/last", headers=user_headers).json()["destination_name"] == "C"
    assert len(client.get("/routes/history", headers=user_headers, params={"limit": 1}).json()) == 1


def test_history_is_private_per_user(client, campus, user_headers):
    visit(client, campus, user_headers, "B")
    other = register_and_login(client, "someone_else")
    assert client.get("/routes/history", headers=other).json() == []
    visit_id = client.get("/routes/history", headers=user_headers).json()[0]["id"]
    assert client.get(f"/routes/history/{visit_id}", headers=other).status_code == 404
    assert client.delete(f"/routes/history/{visit_id}", headers=other).status_code == 404


def test_delete_one_or_all(client, campus, user_headers):
    for destination in ("B", "C"):
        visit(client, campus, user_headers, destination)
    first = client.get("/routes/history", headers=user_headers).json()[0]["id"]
    assert client.delete(f"/routes/history/{first}", headers=user_headers).status_code == 204
    assert len(client.get("/routes/history", headers=user_headers).json()) == 1
    assert client.delete("/routes/history", headers=user_headers).status_code == 204
    assert client.get("/routes/history/last", headers=user_headers).status_code == 404
