import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.services.agent.nl_search import parse_nl_filters

CASES = [
    ("tìm trader an toàn, ít rủi ro, lợi nhuận tốt",
     {"risk_level": ["low", "none"], "no_veto": True, "min_sharpe": 0.5}),
    ("top 10 trader an toàn", {"risk_level": ["low", "none"]}),
    ("trader còn slot, vốn tối thiểu dưới 100$",
     {"has_slot": True, "min_copy_usd_max": 100.0}),
    ("mdd dưới 20, sharpe từ 0.8", {"max_mdd_90d": 20.0, "min_sharpe": 0.8}),
    ("score từ 70, runtime tối thiểu 90", {"min_score": 70.0, "min_runtime_days": 90.0}),
    ("đòn bẩy tối đa 5", {"max_leverage": 5.0}),
    ("vốn 100$", {"min_copy_usd_max": 100.0}),
    ("low risk, còn chỗ", {"risk_level": ["low", "none"], "has_slot": True}),
    ("lợi nhuận tốt", {"min_sharpe": 0.5}),
    ("abc xyz không rõ nghĩa", {"risk_level": ["low", "none"]}),
]


def test_parse_ten_cases() -> None:
    for text, expected in CASES:
        result = parse_nl_filters(text)
        for key, value in expected.items():
            assert result["filters"].get(key) == value, f"{text}: {key}"
        assert result["chips"]
        assert result["filters"]["sort"] == [{"field": "score", "dir": "desc"}]
        assert result["filters"]["limit"] == 50


def test_vague_uses_safe_default_with_assumption() -> None:
    result = parse_nl_filters("tìm trader ngon")
    assert result["assumptions"] == ["Câu hỏi mơ hồ — dùng mặc định an toàn"]
    assert result["filters"]["min_runtime_days"] == 90


needs_db = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


async def _login(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@needs_db
@pytest.mark.asyncio
async def test_nl_search_endpoint_and_apply() -> None:
    from app.main import app
    from app.seed import seed_admin

    await seed_admin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client)
        response = await client.post(
            "/api/v1/agent/search",
            json={"query": "trader an toàn, còn slot, vốn dưới 100$"},
            headers=admin,
        )
        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        assert payload["filters"]["has_slot"] is True
        assert payload["filters"]["min_copy_usd_max"] == 100.0
        assert payload["chips"]

        applied = await client.get(
            "/api/v1/traders",
            params={"max_min_copy_usd": 100, "page_size": 5},
            headers=admin,
        )
        assert applied.status_code == 200, applied.text
        for item in applied.json()["data"]["items"]:
            assert item["id"]
