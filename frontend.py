"""Serves the compiled UniNav-Frontend build under /app/ next to the API."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

FRONTEND_PATH: str = "/app"
MISSING_BUILD_MESSAGE: str = (
    "The frontend build was not found. Run `npm install` and `npm run build` "
    "inside UniNav-Frontend, then restart the server. The API is still available at /docs."
)

logger = logging.getLogger(__name__)


def mount_frontend(app: FastAPI, dist_directory: Path) -> bool:
    """Redirects / to /app/ and serves the build there. Returns False when the build is missing."""

    @app.get("/", include_in_schema=False)
    def redirect_to_frontend() -> RedirectResponse:
        return RedirectResponse(url=f"{FRONTEND_PATH}/")

    if (dist_directory / "index.html").is_file():
        app.mount(FRONTEND_PATH, StaticFiles(directory=dist_directory, html=True), name="frontend")
        return True

    logger.warning("Frontend build not found at %s; serving the API only.", dist_directory)

    @app.get(FRONTEND_PATH, include_in_schema=False)
    @app.get(FRONTEND_PATH + "/{asset_path:path}", include_in_schema=False)
    def frontend_unavailable(asset_path: str = "") -> PlainTextResponse:
        return PlainTextResponse(MISSING_BUILD_MESSAGE, status_code=503)

    return False
