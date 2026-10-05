from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import User, get_db, verify_password

SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_uninav_development_secret_key"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
TOKEN_URL: str = "/auth/token"

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    lifetime = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = dict(data)
    claims["exp"] = datetime.now(timezone.utc) + lifetime
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


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