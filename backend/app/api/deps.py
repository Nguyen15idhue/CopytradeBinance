from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import ApiError
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise ApiError(401, "UNAUTHORIZED", "Thiếu access token")
    payload = decode_token(credentials.credentials, expected_type="access")
    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise ApiError(401, "INVALID_TOKEN", "Access token không hợp lệ") from exc
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise ApiError(401, "INACTIVE_USER", "Tài khoản không hoạt động")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise ApiError(403, "FORBIDDEN", "Chỉ admin được phép thực hiện")
    return user
