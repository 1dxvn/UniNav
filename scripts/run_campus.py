"""Start a reviewed UCC profile without replacing the sample campus database.

Usage: python -m scripts.run_campus --port 8001
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket

from scripts.campus_profiles import profile_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--profile", choices=profile_ids(), default="base")
    parser.add_argument("--database", type=Path, help="Dedicated SQLite file; defaults to uninav-campus.db.")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("Port must be between 0 and 65535 (0 reserves a free rehearsal port).")
    with socket.socket() as listener:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            listener.bind(("127.0.0.1", args.port))
        except OSError as error:
            parser.error(f"Cannot reserve port {args.port}; existing services were left unchanged: {error}")
        from scripts.seed_campus import seed_database
        try:
            report = seed_database(args.profile, args.database)
        except ValueError as error:
            parser.error(str(error))
        import uvicorn

        url = f"http://127.0.0.1:{listener.getsockname()[1]}"
        print("UNINAV_CAMPUS_READY=" + json.dumps({**report, "url": url}), flush=True)
        server = uvicorn.Server(uvicorn.Config("main:app", host="127.0.0.1", log_level="info"))
        server.run(sockets=[listener])


if __name__ == "__main__":
    main()
