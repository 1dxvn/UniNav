import os
import secrets

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional; real environment variables still work
    pass

API_TITLE: str = "UniNav API"
API_VERSION: str = "1.1.0"
API_DESCRIPTION: str = (
    "Backend for UniNav, an interactive campus navigation system. "
    "It manages users and buildings, calculates the shortest routes between "
    "buildings with A* or Dijkstra over a weighted directed graph, and ranks the most "
    "popular routes with an AVL tree."
)

ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

POPULAR_ROUTES_LIMIT: int = 10
NEAREST_BUILDINGS_LIMIT: int = 5
MAX_MULTI_STOP_BUILDINGS: int = 20

FLOORS: dict[int, str] = {
    0: "Ground floor",
    1: "First floor",
    2: "Second floor",
    3: "Third floor",
    4: "Fourth floor",
    5: "Fifth floor",
    6: "Terraces",
    7: "Roof",
}
MAX_FLOOR: int = max(FLOORS)
FLOOR_HEIGHT: float = 3.5

# Without UNINAV_SECRET_KEY a random key is used, so tokens stop working on every restart.
SECRET_KEY: str = os.getenv("UNINAV_SECRET_KEY") or secrets.token_urlsafe(48)
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
TOKEN_URL: str = "/auth/token"
BCRYPT_MAX_PASSWORD_BYTES: int = 72

ROLE_USER: str = "user"
ROLE_ADMIN: str = "admin"

LOGIN_MAX_FAILURES: int = 5
LOGIN_WINDOW_SECONDS: int = 300
