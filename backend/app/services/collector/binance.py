"""Adapter BAPI thật cho 6 endpoint Phase 2."""

from typing import Any

from app.services.collector.base import Page
from app.services.collector.http import BapiHttpClient

BASE_F = "/bapi/futures/v1/friendly/future/copy-trade"
BASE_P = "/bapi/futures/v1/public/future/copy-trade"

PAGE_SIZE_LIST = 30
PAGE_SIZE_POSITIONS = 50
PAGE_SIZE_TRADES = 200
PAGE_SIZE_TRANSFERS = 50
TIME_RANGES = ("7D", "30D", "90D", "180D")


def _page(data: Any, page: int) -> Page:
    if not isinstance(data, dict):
        return Page(items=[], total=0, page=page)
    items = data.get("list") or []
    total = data.get("total")
    return Page(items=list(items), total=int(total or len(items)), page=page)


class BinanceBapiAdapter:
    """Nguồn chính. Mọi parser field để ở parsers.py, adapter chỉ trả raw."""

    def __init__(self, client: BapiHttpClient | None = None) -> None:
        self._client = client or BapiHttpClient()

    async def __aenter__(self) -> "BinanceBapiAdapter":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def list_traders(
        self, time_range: str = "90D", page: int = 1, portfolio_type: str = "PUBLIC"
    ) -> Page:
        data = await self._client.post(
            f"{BASE_F}/home-page/query-list",
            json={
                "pageNumber": page,
                "pageSize": PAGE_SIZE_LIST,
                "timeRange": time_range,
                "dataType": "ROI",
                "favoriteOnly": False,
                "hideFull": False,
                "nickname": "",
                "order": "DESC",
                "userAsset": 0,
                "portfolioType": portfolio_type,
            },
        )
        return _page(data, page)

    async def get_detail(self, portfolio_id: str) -> dict[str, Any]:
        data = await self._client.get(
            f"{BASE_F}/lead-portfolio/detail", params={"portfolioId": portfolio_id}
        )
        return data if isinstance(data, dict) else {}

    async def get_performance(self, portfolio_id: str, time_range: str = "90D") -> dict[str, Any]:
        data = await self._client.get(
            f"{BASE_P}/lead-portfolio/performance",
            params={"portfolioId": portfolio_id, "timeRange": time_range},
        )
        return data if isinstance(data, dict) else {}

    async def get_positions(self, portfolio_id: str, page: int = 1) -> Page:
        data = await self._client.post(
            f"{BASE_F}/lead-portfolio/position-history",
            json={"portfolioId": portfolio_id, "pageNumber": page, "pageSize": PAGE_SIZE_POSITIONS},
        )
        return _page(data, page)

    async def get_trades(self, portfolio_id: str, page: int = 1) -> Page:
        data = await self._client.post(
            f"{BASE_F}/lead-portfolio/trade-history",
            json={"portfolioId": portfolio_id, "pageNumber": page, "pageSize": PAGE_SIZE_TRADES},
        )
        return _page(data, page)

    async def get_transfers(self, portfolio_id: str, page: int = 1) -> Page:
        data = await self._client.post(
            f"{BASE_F}/lead-portfolio/transfer-history",
            json={"portfolioId": portfolio_id, "pageNumber": page, "pageSize": PAGE_SIZE_TRANSFERS},
        )
        return _page(data, page)
