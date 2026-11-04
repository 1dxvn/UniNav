from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dependencies import CurrentUser, DatabaseSession
from models import User
from schemas.auth import Token, UserLogin, UserRegister, UserResponse
from security.authentication import authenticate_user, get_user_by_username
from security.passwords import hash_password
from security.tokens import create_access_token
from services.rate_limiter import login_rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])

USERNAME_TAKEN = HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken.")


def issue_token(request: Request, database_session: Session, username: str, password: str) -> Token:
    client = request.client.host if request.client else "unknown"
    limiter_key = f"{client}:{username.lower()}"
    login_rate_limiter.ensure_allowed(limiter_key)

    user = authenticate_user(database_session, username, password)
    if user is None:
        login_rate_limiter.register_failure(limiter_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    login_rate_limiter.reset(limiter_key)
    return Token(access_token=create_access_token({"sub": user.username}))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, database_session: DatabaseSession) -> User:
    if get_user_by_username(database_session, user_data.username) is not None:
        raise USERNAME_TAKEN

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
        raise USERNAME_TAKEN from error

    database_session.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(request: Request, credentials: UserLogin, database_session: DatabaseSession) -> Token:
    return issue_token(request, database_session, credentials.username, credentials.password)


@router.post("/token", response_model=Token)
def login_with_form(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    database_session: DatabaseSession,
) -> Token:
    return issue_token(request, database_session, form_data.username, form_data.password)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser) -> User:
    return current_user
