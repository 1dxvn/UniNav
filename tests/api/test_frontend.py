from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from frontend import mount_frontend


def build_app(dist_directory: Path) -> TestClient:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    mount_frontend(app, dist_directory)
    return TestClient(app)


def test_root_redirects_to_app(tmp_path: Path) -> None:
    response = build_app(tmp_path).get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/app/"


def test_serves_build_and_assets(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<div id='scene'></div>", encoding="utf-8")
    (tmp_path / "assets" / "index.js").write_text("console.log('ok');", encoding="utf-8")
    client = build_app(tmp_path)

    page = client.get("/app/")
    assert page.status_code == 200
    assert "scene" in page.text
    assert client.get("/app/assets/index.js").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


def test_missing_build_keeps_api_running(tmp_path: Path) -> None:
    client = build_app(tmp_path / "missing")
    assert client.get("/app/").status_code == 503
    assert client.get("/health").json() == {"status": "ok"}


def test_main_app_keeps_docs_and_redirect(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/", follow_redirects=False).headers["location"] == "/app/"
