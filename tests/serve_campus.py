"""Disposable real-API browser fixture. Never opens either development database.

The frontend creates an empty temporary directory and owns process/file cleanup.
Run with venv/Scripts/python.exe -m tests.serve_campus --directory <empty-temp-dir>.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--dataset", type=Path, action="append", default=[], help="Reviewed navigation fixture; repeat to import revisions in order into the temporary database.")
    parser.add_argument("--snapshot-json", action="store_true", help="Print the actual API data contract and exit without opening a port.")
    args = parser.parse_args()
    directory = args.directory.resolve(strict=True)
    if not directory.name.startswith("uninav-e2e-") or any(directory.iterdir()):
        parser.error("Use a new, empty uninav-e2e-* temporary directory.")
    os.environ["UNINAV_DATABASE_URL"] = f"sqlite:///{(directory / 'campus-test.db').as_posix()}"

    from database import SessionLocal, init_db
    from models import Building, User
    from scripts.seed_ucc_floor1 import seed_campus
    from security.passwords import hash_password
    from schemas.datasets import CampusDataset
    from services.datasets import import_dataset
    import uvicorn

    init_db()
    with SessionLocal() as session:
        seed_campus(session)
        for dataset_path in args.dataset:
            import_dataset(session, CampusDataset.model_validate_json(dataset_path.read_text(encoding="utf-8")))
        session.add(Building(name="Isolated test destination", x=70, y=0, floor=1))
        session.add(User(username="student", password_hash=hash_password("demo1234")))
        session.commit()

    if args.snapshot_json:
        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            buildings, paths = client.get("/buildings"), client.get("/paths")
            buildings.raise_for_status()
            paths.raise_for_status()
            print("UNINAV_E2E_SNAPSHOT=" + json.dumps({"buildings": buildings.json(), "paths": paths.json()}), flush=True)
        return

    # Let the OS reserve a free port instead of racing an existing user service.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        print("UNINAV_E2E_URL=" + json.dumps(f"http://127.0.0.1:{listener.getsockname()[1]}"), flush=True)
        server = uvicorn.Server(uvicorn.Config("main:app", host="127.0.0.1", log_level="warning"))
        server.run(sockets=[listener])


if __name__ == "__main__":
    main()
