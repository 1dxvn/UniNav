from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import TOKEN_URL
from database import get_db
from models import User
from security.passwords import verify_password
from security.tokens import decode_access_token

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)


def get_user_by_username(database_session: Session, username: str) -> Optional[User]:
    return database_session.scalar(select(User).where(User.username == username))


def authenticate_user(database_session: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(database_session, username)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    database_session: Annotated[Session, Depends(get_db)],
) -> User:
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise invalid_credentials

    username = payload.get("sub")
    if not isinstance(username, str) or not username:
        raise invalid_credentials

    user = get_user_by_username(database_session, username)
    if user is None:
        raise invalid_credentials

    return user
