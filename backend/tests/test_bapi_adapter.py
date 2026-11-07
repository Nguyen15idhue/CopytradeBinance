import json

import httpx
import pytest

from app.services.collector.binance import BinanceBapiAdapter
from app.services.collector.http import BapiError, BapiHttpClient, CircuitBreaker, CircuitOpenError

BASE = "https://api.test"


def make_adapter(handler, **kwargs) -> BinanceBapiAdapter:
    transport = httpx.MockTransport(handler)
    client = BapiHttpClient(
        base_url=BASE,
        concurrency=2,
        max_retries=kwargs.pop("max_retries", 2),
        transport=transport,
        sleep=kwargs.pop("sleep", _no_sleep),
        breaker=kwargs.pop("breaker", None),
    )
    return BinanceBapiAdapter(client=client)


async def _no_sleep(_delay: float) -> None:
    return None


def ok(data):
    return httpx.Response(
        200, json={"code": "000000", "message": None, "success": True, "data": data}
    )


@pytest.mark.asyncio
async def test_list_uses_page_size_30_and_portfolio_type() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return ok({"total": 8965, "list": [{"leadPortfolioId": "1"}, {"leadPortfolioId": "2"}]})

    adapter = make_adapter(handler)
    page = await adapter.list_traders("90D", 2, "SIGNAL")
    assert seen["path"].endswith("/friendly/future/copy-trade/home-page/query-list")
    assert seen["body"]["pageSize"] == 30
    assert seen["body"]["pageNumber"] == 2
    assert seen["body"]["portfolioType"] == "SIGNAL"
    assert page.total == 8965
    assert len(page.items) == 2


@pytest.mark.asyncio
async def test_detail_and_performance_use_correct_base() -> None:
    paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if "performance" in request.url.path:
            return ok({"timeRange": "90D", "roi": 1.5, "mdd": None, "sharpRatio": None})
        return ok({"status": "ACTIVE", "isPaused": False, "positionShow": False})

    adapter = make_adapter(handler)
    detail = await adapter.get_detail("42")
    perf = await adapter.get_performance("42", "90D")
    assert detail["status"] == "ACTIVE"
    assert perf["timeRange"] == "90D"
    assert paths[0].endswith("/friendly/future/copy-trade/lead-portfolio/detail")
    assert paths[1].endswith("/public/future/copy-trade/lead-portfolio/performance")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "page_size"),
    [
        ("get_positions", "position-history", 50),
        ("get_trades", "trade-history", 200),
        ("get_transfers", "transfer-history", 50),
    ],
)
async def test_paginated_endpoints_send_page_size(method, path, page_size) -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return ok({"total": 3, "list": [1, 2]})

    adapter = make_adapter(handler)
    page = await getattr(adapter, method)("42", 1)
    assert seen["path"].endswith(path)
    assert seen["body"]["pageSize"] == page_size
    assert page.total == 3


@pytest.mark.asyncio
async def test_retry_on_rate_limit_code_then_success() -> None:
    attempts = []
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) <= 2:
            return httpx.Response(200, json={"code": "11012005", "message": "limit", "data": None})
        return ok({"total": 1, "list": [{"leadPortfolioId": "1"}]})

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    adapter = make_adapter(handler, sleep=fake_sleep)
    page = await adapter.list_traders("90D", 1)
    assert len(attempts) == 3
    assert len(sleeps) >= 2
    assert sleeps[0] >= 30
    assert page.total == 1


@pytest.mark.asyncio
async def test_retry_on_500() -> None:
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        return httpx.Response(500, json={"code": "500", "message": "boom"})

    adapter = make_adapter(handler, max_retries=1)
    with pytest.raises(BapiError):
        await adapter.get_detail("42")
    assert len(attempts) == 2


@pytest.mark.asyncio
async def test_404_is_not_retried() -> None:
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        return httpx.Response(404, json={"code": "404", "message": "not found"})

    adapter = make_adapter(handler, max_retries=3)
    with pytest.raises(BapiError):
        await adapter.get_detail("42")
    assert len(attempts) == 1


@pytest.mark.asyncio
async def test_429_html_body_is_retried_with_long_delay() -> None:
    attempts = []
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) == 1:
            return httpx.Response(429, text="<html>Too Many Requests</html>")
        return ok({"total": 1, "list": [{"leadPortfolioId": "1"}]})

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    adapter = make_adapter(handler, sleep=fake_sleep)
    page = await adapter.list_traders("90D", 1)
    assert page.total == 1
    assert len(attempts) == 2
    assert sleeps[0] >= 30


@pytest.mark.asyncio
async def test_429_retry_after_is_honored() -> None:
    attempts = []
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) == 1:
            return httpx.Response(
                429, text="slow down", headers={"Retry-After": "45"}
            )
        return ok({"total": 0, "list": []})

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    adapter = make_adapter(handler, sleep=fake_sleep)
    await adapter.get_detail("42")
    assert sleeps[0] >= 45


@pytest.mark.asyncio
async def test_429_exhausted_raises_rate_limited() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="too many")

    async def fake_sleep(_delay: float) -> None:
        return None

    adapter = make_adapter(handler, max_retries=1, sleep=fake_sleep)
    with pytest.raises(BapiError) as excinfo:
        await adapter.get_detail("42")
    assert excinfo.value.status_code == 429
    assert excinfo.value.code == "RATE_LIMITED"


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_consecutive_failures() -> None:
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        return httpx.Response(500, json={"code": "500", "message": "boom"})

    adapter = make_adapter(handler, max_retries=0, breaker=CircuitBreaker(threshold=3))
    for _ in range(3):
        with pytest.raises(BapiError):
            await adapter.get_detail("42")
    with pytest.raises(CircuitOpenError):
        await adapter.get_detail("42")
    assert len(attempts) == 3
