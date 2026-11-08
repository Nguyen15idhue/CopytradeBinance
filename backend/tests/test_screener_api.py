import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.seed import seed_admin

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + dữ liệu Phase 2/3 trong compose",
)


async def _client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _login(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.mark.asyncio
async def test_screener_default_sort_and_filter() -> None:
    await seed_admin()
    async with await _client() as client:
        headers = await _login(client)

        default = await client.get("/api/v1/traders", headers=headers)
        assert default.status_code == 200
        payload = default.json()["data"]
        assert payload["sort_by"] == "score"
        assert payload["sort_dir"] == "desc"
        assert payload["items"]
        scores = [item["score"] for item in payload["items"] if item["score"] is not None]
        assert scores == sorted(scores, reverse=True)

        filtered = await client.get(
            "/api/v1/traders", params={"max_mdd_90d": 15, "page_size": 100}, headers=headers
        )
        assert filtered.status_code == 200
        items = filtered.json()["data"]["items"]
        assert items
        assert all(item["mdd_90d"] is not None and item["mdd_90d"] <= 15 for item in items)


@pytest.mark.asyncio
async def test_screener_excludes_excluded_by_default() -> None:
    async with await _client() as client:
        headers = await _login(client)
        default = await client.get("/api/v1/traders", params={"page_size": 100}, headers=headers)
        tiers = {item["potential_tier"] for item in default.json()["data"]["items"]}
        assert "excluded" not in tiers

        included = await client.get(
            "/api/v1/traders",
            params={"include_excluded": True, "potential_tier": "excluded", "page_size": 5},
            headers=headers,
        )
        items = included.json()["data"]["items"]
        assert items
        assert all(item["potential_tier"] == "excluded" for item in items)
        assert all(item["filter_reasons"] for item in items)


@pytest.mark.asyncio
async def test_funnel_summary_matches_tiers() -> None:
    async with await _client() as client:
        headers = await _login(client)
        response = await client.get("/api/v1/traders/funnel-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["universe"] > 10_000
        assert data["watch"] + data["qualified"] + data["high"] > 400


@pytest.mark.asyncio
async def test_saved_views_crud_and_csv() -> None:
    async with await _client() as client:
        headers = await _login(client)
        created = await client.post(
            "/api/v1/saved-views",
            json={"name": "Test view", "filters": {"max_mdd_90d": 20}},
            headers=headers,
        )
        assert created.status_code == 200
        view_id = created.json()["data"]["id"]

        listed = await client.get("/api/v1/saved-views", headers=headers)
        assert any(view["id"] == view_id for view in listed.json()["data"])

        csv_response = await client.get(
            "/api/v1/traders/export.csv", params={"max_mdd_90d": 15}, headers=headers
        )
        assert csv_response.status_code == 200
        assert "text/csv" in csv_response.headers["content-type"]
        assert "Mã trader" in csv_response.text.splitlines()[0]

        deleted = await client.delete(f"/api/v1/saved-views/{view_id}", headers=headers)
        assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_screener_multi_window_sort_and_filters() -> None:
    await seed_admin()
    async with await _client() as client:
        headers = await _login(client)

        windowed = await client.get(
            "/api/v1/traders",
            params={"window": "7D", "sort_by": "roi", "sort_dir": "desc", "page_size": 20},
            headers=headers,
        )
        assert windowed.status_code == 200, windowed.text
        data = windowed.json()["data"]
        assert data["window"] == "7D"
        assert data["window_missing"] is False
        rois = [
            item["windows"]["7D"]["roi"]
            for item in data["items"]
            if item["windows"].get("7D", {}).get("roi") is not None
        ]
        assert rois and rois == sorted(rois, reverse=True)

        copiers = await client.get(
            "/api/v1/traders",
            params={"min_copiers": 10, "page_size": 50},
            headers=headers,
        )
        assert copiers.status_code == 200
        assert all(
            (item["current_copiers"] or 0) >= 10 for item in copiers.json()["data"]["items"]
        )

        pnl = await client.get(
            "/api/v1/traders",
            params={"window": "90D", "min_copier_pnl": 1000, "page_size": 50},
            headers=headers,
        )
        assert pnl.status_code == 200
        assert all(
            item["windows"]["90D"]["copier_pnl"] >= 1000
            for item in pnl.json()["data"]["items"]
        )

        aum = await client.get(
            "/api/v1/traders", params={"min_aum": 50000, "page_size": 50}, headers=headers
        )
        assert aum.status_code == 200
        assert all((item["aum"] or 0) >= 50000 for item in aum.json()["data"]["items"])

        missing_window = await client.get(
            "/api/v1/traders", params={"window": "180D", "page_size": 5}, headers=headers
        )
        assert missing_window.status_code == 200
        assert missing_window.json()["data"]["window_missing"] is False


@pytest.mark.asyncio
async def test_screener_null_window_not_zero() -> None:
    await seed_admin()
    async with await _client() as client:
        headers = await _login(client)
        response = await client.get(
            "/api/v1/traders",
            params={"window": "180D", "sort_by": "roi_180d", "page_size": 100},
            headers=headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert items
        from sqlalchemy import select

        from app.core.database import SessionLocal
        from app.models.trader_metric import TraderMetric

        async with SessionLocal() as db:
            rows = (
                await db.execute(
                    select(TraderMetric.lead_portfolio_id, TraderMetric.roi_180d).where(
                        TraderMetric.lead_portfolio_id.in_(
                            [item["id"] for item in items]
                        )
                    )
                )
            ).all()
        db_values = {
            lead: (float(roi) if roi is not None else None) for lead, roi in rows
        }
        # API phải khớp DB tuyệt đối: null giữ null, không bị đổi thành 0.
        for item in items:
            assert item["windows"]["180D"]["roi"] == db_values[item["id"]]


@pytest.mark.asyncio
async def test_search_by_name_and_id() -> None:
    await seed_admin()
    async with await _client() as client:
        headers = await _login(client)

        by_id = await client.get(
            "/api/v1/traders", params={"q": "4954939000240529664"}, headers=headers
        )
        assert by_id.status_code == 200
        items = by_id.json()["data"]["items"]
        assert items
        assert any(item["id"] == "4954939000240529664" for item in items)

        partial = await client.get(
            "/api/v1/traders", params={"q": "4954939000"}, headers=headers
        )
        assert partial.status_code == 200
        assert any(item["id"] == "4954939000240529664" for item in partial.json()["data"]["items"])

        nickname = await client.get(
            "/api/v1/traders", params={"q": "CIC"}, headers=headers
        )
        assert nickname.status_code == 200
        for item in nickname.json()["data"]["items"]:
            assert "cic" in (item["nickname"] or "").lower() or "cic" in item["id"].lower()
