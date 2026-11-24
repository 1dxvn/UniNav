from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.types import Receive, Scope, Send

from config import ALLOWED_ORIGINS, API_DESCRIPTION, API_TITLE, API_VERSION, FRONTEND_DIST
from database import SessionLocal, init_db
from frontend import mount_frontend
from routers import (
    auth,
    buildings,
    campus,
    floors,
    graph,
    health,
    history,
    imports,
    navigation,
    paths,
    queues,
    rankings,
    routes,
    tours,
    users,
)
from services import route_learning
from services.campus_graph import campus_graph_service
from services.runtime_state import attach_runtime_stores, detach_runtime_stores


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    campus_graph_service.load_from_database()
    with SessionLocal() as database_session:
        route_learning.startup(database_session)
    try:
        attach_runtime_stores()
        yield
    finally:
        detach_runtime_stores()


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

class ApiGZipMiddleware(GZipMiddleware):
    """Compresses API responses (/paths and /buildings weigh several MB) but not the /app build files."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and not scope["path"].startswith("/app"):
            await super().__call__(scope, receive, send)
        else:
            await self.app(scope, receive, send)


app.add_middleware(ApiGZipMiddleware, minimum_size=1024, compresslevel=6)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# `imports` must be registered before `buildings` so "/buildings/import" is not read as an id.
for router_module in (
    auth, users, imports, buildings, floors, paths, graph, routes, history, navigation, queues, rankings, tours, campus, health
):
    app.include_router(router_module.router)

# Registered after the API so its routes keep priority.
mount_frontend(app, FRONTEND_DIST)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
