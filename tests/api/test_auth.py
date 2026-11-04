from tests.conftest import PASSWORD, register_and_login


def test_register_login_and_me(client):
    response = client.post("/auth/register", json={"username": "ana", "password": PASSWORD})
    assert response.status_code == 201
    assert response.json()["role"] == "user"
    assert "password" not in response.text

    headers = register_and_login(client, "ana")
    assert client.get("/auth/me", headers=headers).json()["username"] == "ana"


def test_duplicate_username_is_rejected(client):
    client.post("/auth/register", json={"username": "ana", "password": PASSWORD})
    response = client.post("/auth/register", json={"username": "ana", "password": PASSWORD})
    assert response.status_code == 409


def test_invalid_registration_data(client):
    assert client.post("/auth/register", json={"username": "a", "password": PASSWORD}).status_code == 422
    assert client.post("/auth/register", json={"username": "bob", "password": "123"}).status_code == 422
    assert client.post("/auth/register", json={"username": "b o b", "password": PASSWORD}).status_code == 422


def test_wrong_password_and_missing_token(client):
    client.post("/auth/register", json={"username": "ana", "password": PASSWORD})
    assert client.post("/auth/login", json={"username": "ana", "password": "nope"}).status_code == 401
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_form_login_for_swagger(client):
    client.post("/auth/register", json={"username": "ana", "password": PASSWORD})
    response = client.post("/auth/token", data={"username": "ana", "password": PASSWORD})
    assert response.status_code == 200 and response.json()["token_type"] == "bearer"


def test_login_is_rate_limited_after_repeated_failures(client):
    client.post("/auth/register", json={"username": "ana", "password": PASSWORD})
    codes = [
        client.post("/auth/login", json={"username": "ana", "password": "bad"}).status_code
        for _ in range(7)
    ]
    assert codes == [401] * 5 + [429] * 2
    blocked = client.post("/auth/login", json={"username": "ana", "password": PASSWORD})
    assert blocked.status_code == 429 and "retry-after" in blocked.headers
