from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS, API_DESCRIPTION, API_TITLE, API_VERSION
from database import init_db
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
from services.campus_graph import campus_graph_service


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    campus_graph_service.load_from_database()
    yield


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
