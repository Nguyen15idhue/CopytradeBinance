"""Job collector lưu DB: restart không mất, RBAC, kill switch."""

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.collector_job import CollectorJob
from app.seed import seed_admin, seed_viewer

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + Redis trong compose",
)


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.fixture(autouse=True)
async def _cleanup():
    yield
    async with SessionLocal() as db:
        await db.execute(delete(CollectorJob))
        await db.commit()


async def test_job_persists_in_db_and_listed() -> None:
    await seed_admin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        response = await client.post("/api/v1/collector/run-deep", headers=admin)
        assert response.status_code == 202, response.text
        job_id = response.json()["data"]["job_id"]

        async with SessionLocal() as db:
            row = (
                await db.execute(
                    select(CollectorJob).where(CollectorJob.id == job_id)
                )
            ).scalars().first()
            assert row is not None
            assert row.status in {"queued", "running", "success", "failed", "skipped"}

        detail = await client.get(f"/api/v1/collector/jobs/{job_id}", headers=admin)
        assert detail.status_code == 200
        assert detail.json()["data"]["kind"] == "deep"

        listed = await client.get("/api/v1/collector/jobs", headers=admin)
        assert listed.status_code == 200
        assert any(item["id"] == job_id for item in listed.json()["data"]["items"])

        missing = await client.get(
            f"/api/v1/collector/jobs/{uuid4()}", headers=admin
        )
        assert missing.status_code == 404


async def test_job_rbac_and_kill_switch() -> None:
    await seed_admin()
    await seed_viewer()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        viewer = await _login(client, "viewer@example.com", "Viewer123!ChangeMe")

        forbidden = await client.post("/api/v1/collector/run-scan", headers=viewer)
        assert forbidden.status_code == 403

        switched = await client.post(
            "/api/v1/collector/kill-switch", json={"active": True}, headers=admin
        )
        assert switched.status_code == 200
        try:
            blocked = await client.post("/api/v1/collector/run-scan", headers=admin)
            assert blocked.status_code == 409
            assert blocked.json()["error"]["code"] == "COLLECTOR_DISABLED"
        finally:
            await client.post(
                "/api/v1/collector/kill-switch", json={"active": False}, headers=admin
            )
