"""Start the real UCC floor without replacing the original sample campus database.

Usage: python -m scripts.run_campus --port 8001
"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    from scripts.seed_ucc_floor1 import main as seed

    seed()  # Sets the dedicated DB URL before database or FastAPI is imported.
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
