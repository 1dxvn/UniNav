# UniNav API

Backend for UniNav, an interactive campus navigation simulator. It stores the campus
(places, floors and the paths between them), calculates the shortest route with
A\* or Dijkstra, and keeps each user's route history. A separate 3D frontend consumes
this API.

## Work plans

The three detailed plans are kept in the repository root, in Spanish:

1. [Complete the campus by blocks and floors](Plan_1_Campus_Completo_Por_Bloques.md).
2. [Integrate Block A](Plan_2_Bloque_A.md).
3. [Improve the campus appearance and refine the simple avatar](Plan_3_Mejora_Visual_Campus_y_Monito.md).

The visual plan prioritizes the university model. The avatar remains simple and
faceless, with improved proportions and basic movement.

For the local overnight worker, see [automatic continuity](CONTINUIDAD.md).
Its authorized project instructions live in [EJECUCION_AUTONOMA.md](EJECUCION_AUTONOMA.md).

## Quick start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then set UNINAV_SECRET_KEY
python -m scripts.seed        # optional: sample campus + users (admin / student)
python main.py                # http://127.0.0.1:8000  (docs at /docs)
```

Without `UNINAV_SECRET_KEY` a random key is generated at startup, so tokens stop
working every time the server restarts.

| Variable | Purpose |
|---|---|
| `UNINAV_SECRET_KEY` | Signs the JWT tokens. |
| `UNINAV_ADMIN_PASSWORD` | Password of the `admin` user created by the seed (default `demo1234`). |
| `UNINAV_DATABASE_URL` | Overrides the SQLite database (used by the tests). |
| `UNINAV_FRONTEND_DIST` | Folder of the compiled frontend (default `UniNav-Frontend/dist`). |

## Frontend

The web app lives in its own repository,
[1dxvn/UniNav-Frontend](https://github.com/1dxvn/UniNav-Frontend), cloned inside this folder
as `UniNav-Frontend/` (excluded from this repository's Git). FastAPI serves its build under
`/app/` and redirects `/` there, so the app and the API share one origin.

```bash
git clone https://github.com/1dxvn/UniNav-Frontend.git
cd UniNav-Frontend && npm install && npm run build && cd ..
python main.py                # open http://localhost:8000/
```

If `UniNav-Frontend/dist` is missing the API still starts; `/app/` answers 503 until the
frontend is built.

## Real UCC first-floor demo

The first floor of Bloque B is available as a separate, repeatable development demo.
It uses Claude's metre-scale `campus.glb` and keeps the original `uninav.db` sample
campus intact. Build the frontend first, then run from this backend directory:

```bash
python -m scripts.run_campus --port 8001
# Windows with the existing environment:
venv/Scripts/python.exe -m scripts.run_campus --port 8001
```

Open `http://127.0.0.1:8001/` and sign in with `student` / `demo1234`.
The runner seeds `uninav-campus.db` idempotently, then starts FastAPI. Its API and
Swagger remain available at the usual paths on port 8001. An explicitly configured
`UNINAV_DATABASE_URL` takes priority; the seed refuses to mix the real floor with
another campus. `python main.py` continues to use the original database.

Four destinations are connected: ICETEX, Morphology Laboratory, Elevator and
Restroom Hall, and Preclinic / Dentistry Coordination. Preclinic is reached through
the north circulation and storeroom, as documented in the model handoff. The floor
has 19 places and 16 bidirectional paths. Corridor waypoints were
checked against its walls. Plan `(x, y)` becomes scene `(x, floor * 3.5, -y)`.
The drawing's +y direction is not geographic north. Heights and plaza levels remain
the approximations documented by the model author.

See `UniNav-Frontend/docs/REHEARSAL.md` for the one-minute demonstration and
`UniNav-Frontend/docs/campus-review.md` for the model review and route screenshots.
The impossible-route regression uses an isolated synthetic destination in a
temporary test database; it is never added to either development campus.

`GET /campus/catalog` exposes the versioned source inventory in
`data/campus-catalog.json` when the connected database matches the integrated UCC
places and paths. An unrelated sample database receives `available: false`.
Block identities and per-block floor elevations retain their evidence status.
The current flat model remains at scene elevation 3.5 m; reading this catalogue
does not move places, add rooms or enable vertical routes. The route and building
contracts remain compatible. The new endpoint is loaded on the next normal server
start; browser error tests exercise it with a separate temporary FastAPI process.

## Project layout

```
main.py             app creation, CORS, router registration
config.py           constants (floors, limits, roles, token settings)
database.py         engine, session, small column migrations
models.py           User, Building, CampusPath, RouteVisit
dependencies.py     DatabaseSession, CurrentUser, AdminUser
routers/            one file per group of endpoints
services/           business logic used by the routers
schemas/            request and response models
security/           password hashing, JWT, authentication
data_structures/    hand-written structures (no stdlib containers doing the work)
scripts/            seed.py, promote_admin.py
examples/           runnable demos of each data structure
tests/              unit (data structures) and api (endpoints)
```

## Concepts

- **Place**: a building, room, stairwell or any point of interest. It has `x`, `y`,
  a `floor` (0-7: ground, first to fifth, terraces, roof), and an optional faculty and type.
- **Path**: a connection between two places. It has a `kind` (`corridor`, `stairs`,
  `elevator`, `ramp`, `outdoor`), may be one-way, and has an optional weight. The
  effective weight is never lower than the 3D straight-line distance (floors are 3.5 m
  apart), which keeps A\* optimal. Places are only reachable through paths.
- **Roles**: `user` can read and calculate routes. `admin` can also create, edit and
  delete places and paths. Promote someone with `python -m scripts.promote_admin <username>`.

## Endpoints

Routes marked **admin** need an administrator token, **auth** needs any logged-in user.

| Group | Endpoint | Access |
|---|---|---|
| auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/token`, `GET /auth/me` | public / auth |
| users | `GET /users/me/stats`, `PUT /users/me/password`, `DELETE /users/me` | auth |
| buildings | `GET /buildings` (filters: `search`, `faculty`, `building_type`, `floor`) | public |
| | `GET /buildings/{id}`, `/buildings/{id}/neighbors`, `/buildings/nearest`, `/buildings/faculties`, `/buildings/types` | public |
| | `POST /buildings`, `POST /buildings/import`, `PUT /buildings/{id}`, `DELETE /buildings/{id}` | admin |
| floors | `GET /floors` | public |
| paths | `GET /paths` (filter: `building_id`), `GET /paths/{id}` | public |
| | `POST /paths`, `POST /paths/import`, `PUT /paths/{id}`, `DELETE /paths/{id}` | admin |
| graph | `GET /graph` | public |
| | `POST /graph/reload` | admin |
| routes | `POST /routes/calculate` (saves to history) | auth |
| | `POST /routes/compare`, `POST /routes/multi-stop`, `GET /routes/popular` | public |
| history | `GET /routes/history`, `/routes/history/last`, `/routes/history/{id}`, `DELETE /routes/history`, `DELETE /routes/history/{id}` | auth |
| rankings | `GET /rankings/places` (`?limit=`) | public |
| navigation | `GET /navigation`, `POST /navigation/visit`, `POST /navigation/back`, `POST /navigation/forward`, `DELETE /navigation` | auth |
| tours | `GET /tours`, `GET /tours/{id}` | public |
| | `POST /tours/{id}/start`, `GET /tours/session`, `POST /tours/session/next`, `POST /tours/session/previous`, `DELETE /tours/session` | auth |
| | `POST /tours`, `DELETE /tours/{id}` | admin |
| queues | `GET /queues/{building_id}` | public |
| | `POST /queues/{building_id}/join`, `GET .../position`, `DELETE .../leave` | auth |
| | `POST /queues/{building_id}/serve` (calls the next person) | admin |
| campus | `GET /campus/hierarchy` | public |
| status | `GET /health` | public |

Route requests accept `algorithm` (`a_star` or `dijkstra`) and `avoid`, a list of path
kinds to skip, for example `{"avoid": ["stairs"]}` for an accessible route. Responses
include `steps` with the kind and distance of every hop.

The navigation trail works like a browser history: visiting a place after going back discards the places ahead, and the trail keeps the latest 50 places. Tours are stored in the database; the stop each user is on lives in memory. Waiting lines live in memory and are cleared when the server restarts.

Failed logins are limited to 5 per 5 minutes per client and username (HTTP 429).

## Where each data structure is used

| Structure | File | Used for |
|---|---|---|
| Weighted directed graph, A\*, Dijkstra | `data_structures/graph.py` | Campus map and route calculation |
| Min priority queue (binary heap) | `data_structures/heaps.py` | Frontier of A\* and Dijkstra |
| Max-heap | `data_structures/max_heap.py` | Most visited places (`/rankings/places`) |
| AVL tree | `data_structures/avl_tree.py` | Ranking of popular routes (`/routes/popular`) |
| Stack | `data_structures/stack.py` | User history, newest first |
| N-ary tree | `data_structures/nary_tree.py` | Campus hierarchy (`/campus/hierarchy`) |
| Queue | `data_structures/queue.py` | Waiting line of each place (`/queues`) |
| Circular doubly linked list | `data_structures/circular_doubly_linked_list.py` | Stops of a guided tour: next and previous wrap around (`/tours`) |
| Doubly linked list | `data_structures/doubly_linked_list.py` | Back and forward trail of the places a user visited (`/navigation`) |

Run a demo with, for example, `python -m examples.graph_demo`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The API tests run against a temporary SQLite database, so they never touch `uninav.db`.

## Notes

- The sample campus from `scripts/seed.py` is made up for development. Replace
  `scripts/seed_data.py` with the real campus when the floor plans are available.
- The graph is kept in memory and rebuilt from the database whenever a place or path changes.
- Schema changes are limited to the small column migrations in `database.py`. For
  anything bigger, move to Alembic.
