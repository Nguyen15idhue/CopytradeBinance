import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.seed import seed_admin, seed_traders, seed_viewer

QUALIFIED_ID = "4520644381136785152"

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Đặt RUN_INTEGRATION=1 và dùng PostgreSQL đã migrate để chạy integration test",
)


@pytest.mark.asyncio
async def test_login_detail_rbac_integration() -> None:
    await seed_admin()
    await seed_viewer()
    await seed_traders()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["data"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        trader = await client.get(f"/api/v1/traders/{QUALIFIED_ID}", headers=admin_headers)
        assert trader.status_code == 200
        data = trader.json()["data"]
        assert len(data["metrics"]) == 10
        assert data["provenance"]["source"] in {"demo", "detail", "list"}
        assert isinstance(data["reasons"], list)
        assert data["confidence"] >= 0

        missing = await client.get("/api/v1/traders/khong-ton-tai", headers=admin_headers)
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "TRADER_NOT_FOUND"

        viewer_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@example.com", "password": "Viewer123!ChangeMe"},
        )
        assert viewer_login.status_code == 200
        viewer_token = viewer_login.json()["data"]["access_token"]
        forbidden = await client.get(
            "/api/v1/admin/ping",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["error"]["code"] == "FORBIDDEN"
