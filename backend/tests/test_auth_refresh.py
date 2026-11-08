"""Refresh token 7 ngày: đổi access mới, rotate refresh, token cũ bị từ chối."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.seed import seed_admin

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


async def test_refresh_flow_rotates_tokens() -> None:
    await seed_admin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
        )
        assert login.status_code == 200
        first = login.json()["data"]

        refreshed = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first["refresh_token"]},
        )
        assert refreshed.status_code == 200, refreshed.text
        second = refreshed.json()["data"]
        # Access token có thể trùng nếu phát trong cùng giây (iat/exp theo giây),
        # nhưng refresh token phải rotate.
        assert second["refresh_token"] != first["refresh_token"]

        # Access mới dùng được cho API cần đăng nhập.
        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {second['access_token']}"},
        )
        assert me.status_code == 200

        # Refresh cũ đã bị thu hồi (rotation).
        reused = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first["refresh_token"]},
        )
        assert reused.status_code == 401

        # Access rác trả 401 (không phải 500) để frontend biết mà refresh.
        bad = await client.get(
            "/api/v1/traders",
            headers={"Authorization": "Bearer expired.token.value"},
        )
        assert bad.status_code == 401
        assert bad.json()["error"]["code"] in {"UNAUTHORIZED", "INVALID_TOKEN"}
