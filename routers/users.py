from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from dependencies import CurrentUser, DatabaseSession
from schemas.auth import PasswordChange, UserStatsResponse
from security.passwords import hash_password, verify_password
from services.user_stats import compute_user_stats

router = APIRouter(prefix="/users/me", tags=["users"])


@router.get("/stats", response_model=UserStatsResponse)
def read_my_stats(
    database_session: DatabaseSession, current_user: CurrentUser
) -> UserStatsResponse:
    return compute_user_stats(database_session, current_user.id)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    password_data: PasswordChange,
    database_session: DatabaseSession,
    current_user: CurrentUser,
) -> Response:
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.password_hash = hash_password(password_data.new_password)
    database_session.add(current_user)
    database_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(database_session: DatabaseSession, current_user: CurrentUser) -> Response:
    database_session.delete(current_user)
    database_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
