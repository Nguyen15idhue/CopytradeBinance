import os
import time
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.seed import seed_admin

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + Redis trong compose",
)


async def _login(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


async def test_status_status_shape_and_no_filesystem_scan(monkeypatch) -> None:
    await seed_admin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)

        def boom(*args, **kwargs):
            raise AssertionError("/collector/status không được quét filesystem")

        monkeypatch.setattr(Path, "rglob", boom)
        response = await client.get("/api/v1/collector/status", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        archive = data["raw_archive"]
        assert set(archive) >= {"mode", "files", "bytes", "records", "source"}
        assert archive["source"] in {"manifest", "empty", "stale"}
        assert data["tiers"]
        monkeypatch.undo()


async def test_status_p95_under_300ms() -> None:
    await seed_admin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)
        # Warm cache rồi đo 20 request.
        await client.get("/api/v1/collector/status", headers=headers)
        durations = []
        for _ in range(20):
            started = time.perf_counter()
            response = await client.get("/api/v1/collector/status", headers=headers)
            durations.append((time.perf_counter() - started) * 1000)
            assert response.status_code == 200
        durations.sort()
        p95 = durations[int(len(durations) * 0.95) - 1]
        assert p95 < 300, f"p95 {p95:.1f}ms vượt 300ms"


async def test_archive_stats_shape() -> None:
    await seed_admin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)
        response = await client.get("/api/v1/collector/archive-stats", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert {"items", "totals", "by_day"} <= set(data)
        assert {"files", "bytes", "records"} <= set(data["totals"])
        for item in data["items"]:
            assert {"scan_id", "endpoint", "status", "files", "bytes", "records"} <= set(item)


async def test_status_manifest_error_returns_stale(monkeypatch) -> None:
    from app.api.v1 import collector as collector_api

    await seed_admin()
    transport = ASGITransport(app=app)

    async def broken(_db):
        raise RuntimeError("manifest lỗi")

    # Bỏ qua cache bằng cách xoá Redis key, rồi ép manifest_stats lỗi.
    from redis.asyncio import Redis

    from app.core.config import get_settings

    client_redis = Redis.from_url(get_settings().redis_url)
    try:
        await client_redis.delete(collector_api.ARCHIVE_CACHE_KEY)
    finally:
        await client_redis.aclose()

    monkeypatch.setattr(
        "app.services.storage.raw.RawArchive.manifest_stats", broken, raising=True
    )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)
        response = await client.get("/api/v1/collector/status", headers=headers)
        assert response.status_code == 200
        assert response.json()["data"]["raw_archive"]["source"] == "stale"
