from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.rate_limit import limiter
from app.models.user import User
from app.services.auth import (
    authenticate_user,
    issue_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=200)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


def _user_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
    }


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise ApiError(401, "INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng")
    user.last_login_at = datetime.now(UTC)
    access_token, refresh_token = await issue_tokens(db, user)
    return ok(
        {
            "user": _user_payload(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
        request,
    )


@router.post("/refresh")
async def refresh(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    access_token, refresh_token = await rotate_refresh_token(db, body.refresh_token)
    return ok(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
        request,
    )


@router.post("/logout")
async def logout(
    request: Request,
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await revoke_refresh_token(db, body.refresh_token)
    return ok({"logged_out": True}, request)


@router.get("/me")
async def me(request: Request, user: User = Depends(get_current_user)) -> dict:
    return ok(_user_payload(user), request)
