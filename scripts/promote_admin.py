"""Grants the admin role to an existing user.

Usage: python -m scripts.promote_admin <username>
"""
from __future__ import annotations

import sys

from config import ROLE_ADMIN
from database import SessionLocal, init_db
from security.authentication import get_user_by_username


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python -m scripts.promote_admin <username>")

    init_db()
    with SessionLocal() as database_session:
        user = get_user_by_username(database_session, sys.argv[1])
        if user is None:
            sys.exit(f"User '{sys.argv[1]}' does not exist.")
        user.role = ROLE_ADMIN
        database_session.commit()
    print(f"'{sys.argv[1]}' is now an administrator.")


if __name__ == "__main__":
    main()
