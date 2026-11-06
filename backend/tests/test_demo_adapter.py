import pytest

from app.services.collector.demo import EXCLUDED_ID, QUALIFIED_ID, DemoAdapter


@pytest.mark.asyncio
async def test_demo_adapter_returns_two_traders() -> None:
    adapter = DemoAdapter()
    page = await adapter.list_traders("90D", 1)
    ids = {item["leadPortfolioId"] for item in page.items}
    assert ids == {EXCLUDED_ID, QUALIFIED_ID}


@pytest.mark.asyncio
async def test_demo_detail_marks_provenance() -> None:
    adapter = DemoAdapter()
    detail = await adapter.get_detail(QUALIFIED_ID)
    assert detail["source"] == "demo"
    assert detail["window"] == "90D"
    assert detail["aum"] > 0


@pytest.mark.asyncio
async def test_demo_performance_has_four_windows() -> None:
    adapter = DemoAdapter()
    for window in ("7D", "30D", "90D", "180D"):
        data = await adapter.get_performance(QUALIFIED_ID, window)
        assert data["window"] == window
        assert data["source"] == "demo"
