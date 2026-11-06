from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.security import (
    create_token,
    decode_token,
    hash_token,
    verify_password,
)
from app.models.session import UserSession
from app.models.user import User

settings = get_settings()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def issue_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    session_id = uuid4()
    access_token = create_token(
        str(user.id),
        user.role,
        "access",
        timedelta(minutes=settings.jwt_access_ttl_min),
    )
    refresh_token = create_token(
        str(user.id),
        user.role,
        "refresh",
        timedelta(days=settings.jwt_refresh_ttl_days),
        jti=str(session_id),
    )
    db.add(
        UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.jwt_refresh_ttl_days),
        )
    )
    await db.commit()
    return access_token, refresh_token


async def rotate_refresh_token(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    payload = decode_token(refresh_token, expected_type="refresh")
    session_id = payload.get("jti")
    if not session_id:
        raise ApiError(401, "INVALID_TOKEN", "Refresh token thiếu jti")
    session = await db.get(UserSession, UUID(session_id))
    now = datetime.now(UTC)
    if (
        not session
        or session.revoked_at is not None
        or session.expires_at <= now
        or session.refresh_token_hash != hash_token(refresh_token)
    ):
        raise ApiError(401, "INVALID_REFRESH_TOKEN", "Refresh token không hợp lệ hoặc đã thu hồi")
    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise ApiError(401, "INACTIVE_USER", "Tài khoản không hoạt động")
    session.revoked_at = now
    await db.flush()
    return await issue_tokens(db, user)


async def revoke_refresh_token(db: AsyncSession, refresh_token: str) -> None:
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        session = await db.get(UserSession, UUID(payload["jti"]))
    except (ApiError, KeyError, ValueError):
        return
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        await db.commit()
