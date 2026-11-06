from datetime import UTC, datetime, timedelta
from hashlib import sha256

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings
from app.core.errors import ApiError

settings = get_settings()
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_token(
    subject: str,
    role: str,
    token_type: str,
    expires_delta: timedelta,
    jti: str | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if jti:
        payload["jti"] = jti
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ApiError(401, "INVALID_TOKEN", "Token không hợp lệ hoặc đã hết hạn") from exc
    if expected_type and payload.get("type") != expected_type:
        raise ApiError(401, "INVALID_TOKEN_TYPE", "Loại token không hợp lệ")
    return payload
