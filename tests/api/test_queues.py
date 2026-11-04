from tests.conftest import register_and_login


def test_people_are_served_in_arrival_order(client, campus, admin_headers):
    place = campus["A"]
    ana = register_and_login(client, "ana")
    luis = register_and_login(client, "luis")

    first = client.post(f"/queues/{place}/join", headers=ana)
    second = client.post(f"/queues/{place}/join", headers=luis)
    assert (first.status_code, first.json()["position"]) == (201, 1)
    assert second.json()["position"] == 2 and second.json()["length"] == 2

    assert client.get(f"/queues/{place}").json()["length"] == 2
    assert client.post(f"/queues/{place}/serve", headers=admin_headers).json()["served_username"] == "ana"
    assert client.get(f"/queues/{place}/position", headers=luis).json()["position"] == 1
    assert client.post(f"/queues/{place}/serve", headers=admin_headers).json()["served_username"] == "luis"
    assert client.post(f"/queues/{place}/serve", headers=admin_headers).status_code == 404


def test_cannot_join_twice(client, campus, user_headers):
    client.post(f"/queues/{campus['A']}/join", headers=user_headers)
    assert client.post(f"/queues/{campus['A']}/join", headers=user_headers).status_code == 409


def test_leaving_keeps_the_order_of_the_others(client, campus):
    place = campus["B"]
    users = {name: register_and_login(client, name) for name in ("ana", "luis", "sofia")}
    for headers in users.values():
        client.post(f"/queues/{place}/join", headers=headers)

    assert client.delete(f"/queues/{place}/leave", headers=users["luis"]).status_code == 204
    assert client.get(f"/queues/{place}/position", headers=users["sofia"]).json()["position"] == 2
    assert client.get(f"/queues/{place}/position", headers=users["luis"]).status_code == 404
    assert client.delete(f"/queues/{place}/leave", headers=users["luis"]).status_code == 404


def test_access_rules_and_unknown_places(client, campus, user_headers):
    assert client.post(f"/queues/{campus['A']}/join").status_code == 401
    assert client.post(f"/queues/{campus['A']}/serve", headers=user_headers).status_code == 403
    assert client.get("/queues/9999").status_code == 404
    assert client.get(f"/queues/{campus['A']}").json()["length"] == 0


def test_deleting_a_place_discards_its_line(client, campus, user_headers, admin_headers):
    client.post(f"/queues/{campus['D']}/join", headers=user_headers)
    client.delete(f"/buildings/{campus['D']}", headers=admin_headers)
    assert client.get(f"/queues/{campus['D']}").status_code == 404
