from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.mkdtemp(prefix="uninav-tests-")) / "test.db"
os.environ["UNINAV_DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH.as_posix()}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from config import ROLE_ADMIN  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402
from security.authentication import get_user_by_username  # noqa: E402
from services.navigation_history import navigation_histories  # noqa: E402
from services.rate_limiter import login_rate_limiter  # noqa: E402
from services.tour_sessions import tour_sessions  # noqa: E402
from services.waiting_lines import waiting_lines  # noqa: E402

PASSWORD = "secret123"


@pytest.fixture()
def client() -> Iterator[TestClient]:
    Base.metadata.drop_all(bind=engine)
    login_rate_limiter._failures.clear()
    waiting_lines.clear_all()
    navigation_histories.clear_all()
    tour_sessions.clear_all()
    with TestClient(app) as test_client:
        yield test_client


def register_and_login(client: TestClient, username: str, admin: bool = False) -> dict[str, str]:
    client.post("/auth/register", json={"username": username, "password": PASSWORD})
    if admin:
        with SessionLocal() as database_session:
            user = get_user_by_username(database_session, username)
            user.role = ROLE_ADMIN
            database_session.commit()
    token = client.post(
        "/auth/login", json={"username": username, "password": PASSWORD}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    return register_and_login(client, "admin_user", admin=True)


@pytest.fixture()
def user_headers(client: TestClient) -> dict[str, str]:
    return register_and_login(client, "regular_user")


@pytest.fixture()
def campus(client: TestClient, admin_headers: dict[str, str]) -> dict[str, int]:
    """Three places on floor 0 in a line (A - B - C) plus an isolated one (D)."""
    places = [("A", 0, 0), ("B", 30, 0), ("C", 60, 0), ("D", 500, 500)]
    response = client.post(
        "/buildings/import",
        headers=admin_headers,
        json=[{"name": name, "x": x, "y": y} for name, x, y in places],
    )
    ids = {building["name"]: building["id"] for building in response.json()}
    client.post(
        "/paths/import",
        headers=admin_headers,
        json=[
            {"source_id": ids["A"], "target_id": ids["B"]},
            {"source_id": ids["B"], "target_id": ids["C"]},
            {"source_id": ids["A"], "target_id": ids["C"], "weight": 200},
        ],
    )
    return ids
