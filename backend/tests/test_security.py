from datetime import timedelta

import pytest

from app.core.errors import ApiError
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    hashed = hash_password("MatKhau123!")
    assert hashed != "MatKhau123!"
    assert verify_password("MatKhau123!", hashed)
    assert not verify_password("sai-mat-khau", hashed)


def test_access_token_roundtrip() -> None:
    token = create_token("user-1", "admin", "access", timedelta(minutes=15))
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_wrong_token_type_rejected() -> None:
    token = create_token("user-1", "viewer", "refresh", timedelta(days=7), jti="session-1")
    with pytest.raises(ApiError):
        decode_token(token, expected_type="access")


def test_token_hash_is_stable() -> None:
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("abd")
