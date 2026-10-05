from __future__ import annotations

import math
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, selectinload

from database import (
    Building,
    RouteVisit,
    SessionLocal,
    User,
    get_db,
    hash_password,
    init_db,
)
from estructuras.arboles import AVLTree
from estructuras.grafo import WeightedDirectedGraph
from estructuras.listas import Stack
from schemas import (
    BuildingCreate,
    BuildingResponse,
    PopularRouteResponse,
    RouteRequest,
    RouteResponse,
    RouteVisitResponse,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)
from security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_user_by_username,
)

API_TITLE: str = "UniNav API"
API_VERSION: str = "1.0.0"
API_DESCRIPTION: str = (
    "Backend for UniNav, an interactive campus navigation system. "
    "It manages users and buildings, calculates the shortest routes between "
    "buildings with A* over a weighted directed graph, and ranks the most "
    "popular routes with an AVL tree."
)
ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
POPULAR_ROUTES_LIMIT: int = 10

campus_graph: WeightedDirectedGraph = WeightedDirectedGraph()
campus_graph_lock: threading.Lock = threading.Lock()

DatabaseSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def add_building_to_graph(graph: WeightedDirectedGraph, name: str, x: float, y: float) -> None:
    existing_buildings = [
        (other_name, graph.get_coordinates(other_name)) for other_name in graph.get_nodes()
    ]
    graph.add_node(name, (x, y))
    for other_name, other_coordinates in existing_buildings:
        if other_name == name or other_coordinates is None:
            continue
        distance = math.hypot(other_coordinates[0] - x, other_coordinates[1] - y)
        graph.add_edge(name, other_name, distance, bidirectional=True)


def build_complete_graph(buildings: list[Building]) -> WeightedDirectedGraph:
    graph = WeightedDirectedGraph()
    for building in buildings:
        add_building_to_graph(graph, building.name, building.x, building.y)
    return graph


def load_graph_from_database() -> None:
    global campus_graph
    with SessionLocal() as database_session:
        buildings = list(database_session.scalars(select(Building).order_by(Building.id)))
    rebuilt_graph = build_complete_graph(buildings)
    with campus_graph_lock:
        campus_graph = rebuilt_graph


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    load_graph_from_database()
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


def issue_token_for_credentials(database_session: Session, username: str, password: str) -> Token:
    user = authenticate_user(database_session, username, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token({"sub": user.username}))


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
def register_user(user_data: UserRegister, database_session: DatabaseSession) -> User:
    if get_user_by_username(database_session, user_data.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )

    try:
        password_hash = hash_password(user_data.password)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    new_user = User(username=user_data.username, password_hash=password_hash)
    database_session.add(new_user)
    try:
        database_session.commit()
    except IntegrityError as error:
        database_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        ) from error

    database_session.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(credentials: UserLogin, database_session: DatabaseSession) -> Token:
    return issue_token_for_credentials(database_session, credentials.username, credentials.password)


@app.post("/auth/token", response_model=Token, tags=["auth"])
def login_with_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    database_session: DatabaseSession,
) -> Token:
    return issue_token_for_credentials(database_session, form_data.username, form_data.password)


@app.get("/auth/me", response_model=UserResponse, tags=["auth"])
def read_current_user(current_user: CurrentUser) -> User:
    return current_user


@app.get("/buildings", response_model=list[BuildingResponse], tags=["buildings"])
def list_buildings(database_session: DatabaseSession) -> list[Building]:
    return list(database_session.scalars(select(Building).order_by(Building.name)))


@app.post(
    "/buildings",
    response_model=BuildingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["buildings"],
)
def create_building(
    building_data: BuildingCreate,
    database_session: DatabaseSession,
    _current_user: CurrentUser,
) -> Building:
    name_taken = database_session.scalar(
        select(Building.id).where(Building.name == building_data.name)
    )
    if name_taken is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Building '{building_data.name}' already exists.",
        )

    new_building = Building(**building_data.model_dump())
    database_session.add(new_building)
    try:
        database_session.commit()
    except IntegrityError as error:
        database_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Building '{building_data.name}' already exists.",
        ) from error
    database_session.refresh(new_building)

    with campus_graph_lock:
        add_building_to_graph(campus_graph, new_building.name, new_building.x, new_building.y)

    return new_building


@app.post(
    "/buildings/import",
    response_model=list[BuildingResponse],
    status_code=status.HTTP_201_CREATED,
    tags=["buildings"],
)
def import_buildings(
    buildings_data: list[BuildingCreate],
    database_session: DatabaseSession,
    _current_user: CurrentUser,
) -> list[Building]:
    if not buildings_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The import list is empty.",
        )

    incoming_names = [building.name for building in buildings_data]
    repeated_in_request = sorted(
        {name for name in incoming_names if incoming_names.count(name) > 1}
    )
    if repeated_in_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicated names in the request: {', '.join(repeated_in_request)}.",
        )

    already_stored = sorted(
        database_session.scalars(select(Building.name).where(Building.name.in_(incoming_names)))
    )
    if already_stored:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Buildings already exist: {', '.join(already_stored)}.",
        )

    new_buildings = [Building(**building.model_dump()) for building in buildings_data]
    database_session.add_all(new_buildings)
    try:
        database_session.commit()
    except IntegrityError as error:
        database_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more buildings already exist.",
        ) from error

    for building in new_buildings:
        database_session.refresh(building)

    load_graph_from_database()
    return new_buildings


@app.post("/routes/calculate", response_model=RouteResponse, tags=["routes"])
def calculate_route(
    route_request: RouteRequest,
    database_session: DatabaseSession,
    current_user: CurrentUser,
) -> RouteResponse:
    origin = database_session.get(Building, route_request.origin_id)
    if origin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Origin building {route_request.origin_id} not found.",
        )

    destination = database_session.get(Building, route_request.destination_id)
    if destination is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination building {route_request.destination_id} not found.",
        )

    with campus_graph_lock:
        if origin.name not in campus_graph or destination.name not in campus_graph:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The campus graph is out of sync with the database. Restart the server.",
            )
        path, distance = campus_graph.a_star(origin.name, destination.name)

    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"There is no route from '{origin.name}' to '{destination.name}'.",
        )

    database_session.add(
        RouteVisit(
            user_id=current_user.id,
            origin_id=origin.id,
            destination_id=destination.id,
            distance=distance,
        )
    )
    database_session.commit()

    return RouteResponse(
        path=path,
        distance=distance,
        origin_name=origin.name,
        destination_name=destination.name,
    )


@app.get("/routes/popular", response_model=list[PopularRouteResponse], tags=["routes"])
def list_popular_routes(database_session: DatabaseSession) -> list[PopularRouteResponse]:
    origin_building = aliased(Building)
    destination_building = aliased(Building)

    route_frequencies = database_session.execute(
        select(origin_building.name, destination_building.name, func.count())
        .select_from(RouteVisit)
        .join(origin_building, RouteVisit.origin_id == origin_building.id)
        .join(destination_building, RouteVisit.destination_id == destination_building.id)
        .group_by(
            RouteVisit.origin_id,
            RouteVisit.destination_id,
            origin_building.name,
            destination_building.name,
        )
    ).all()

    ranking: AVLTree[int, tuple[str, str]] = AVLTree()
    for origin_name, destination_name, frequency in route_frequencies:
        ranking.insert(frequency, (origin_name, destination_name))

    top_routes = ranking.reverse_in_order()[:POPULAR_ROUTES_LIMIT]
    return [
        PopularRouteResponse(
            origin_name=origin_name,
            destination_name=destination_name,
            frequency=frequency,
        )
        for frequency, (origin_name, destination_name) in top_routes
    ]


@app.get("/routes/history", response_model=list[RouteVisitResponse], tags=["routes"])
def read_route_history(
    database_session: DatabaseSession,
    current_user: CurrentUser,
) -> list[RouteVisitResponse]:
    visits_oldest_first = database_session.scalars(
        select(RouteVisit)
        .where(RouteVisit.user_id == current_user.id)
        .options(selectinload(RouteVisit.origin), selectinload(RouteVisit.destination))
        .order_by(RouteVisit.visited_at, RouteVisit.id)
    ).all()

    history: Stack[RouteVisit] = Stack()
    for visit in visits_oldest_first:
        history.push(visit)

    visits_newest_first: list[RouteVisitResponse] = []
    while not history.is_empty():
        visit = history.pop()
        visits_newest_first.append(
            RouteVisitResponse(
                id=visit.id,
                origin_name=visit.origin.name,
                destination_name=visit.destination.name,
                distance=visit.distance,
                visited_at=visit.visited_at,
            )
        )
    return visits_newest_first


@app.get("/health", tags=["status"])
def health_check() -> dict[str, Any]:
    with campus_graph_lock:
        building_count = campus_graph.node_count()
        edge_count = campus_graph.edge_count()
    return {"status": "ok", "buildings": building_count, "edges": edge_count}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)