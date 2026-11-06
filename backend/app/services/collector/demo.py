from datetime import UTC, datetime
from typing import Any

from app.services.collector.base import Page

EXCLUDED_ID = "5296057151807357697"
QUALIFIED_ID = "4520644381136785152"

_FIXTURES: dict[str, dict[str, Any]] = {
    EXCLUDED_ID: {
        "leadPortfolioId": EXCLUDED_ID,
        "nickname": "Excluded Fixture",
        "portfolioType": "SIGNAL",
        "status": "ACTIVE",
        "description": "Fixture Phase 0: portfolio mới, runtime < 30 ngày.",
        "runtimeDays": 4.11,
        "aum": 1200.0,
        "copyAum": 0.0,
        "currentCopyCount": 0,
        "maxCopyCount": 200,
        "leverage": 5.0,
        "lastTradeTime": "2026-11-06T15:00:00Z",
        "source": "demo",
        "window": "90D",
    },
    QUALIFIED_ID: {
        "leadPortfolioId": QUALIFIED_ID,
        "nickname": "Qualified Fixture",
        "portfolioType": "PUBLIC",
        "status": "ACTIVE",
        "description": "Fixture Phase 0: trader B, dữ liệu đủ cho vertical slice.",
        "runtimeDays": 539.04,
        "aum": 68097.08972243,
        "copyAum": 60671.70367501,
        "currentCopyCount": 169,
        "maxCopyCount": 200,
        "leverage": 3.2,
        "lastTradeTime": "2026-11-06T16:00:00Z",
        "source": "demo",
        "window": "90D",
    },
}

_PERFORMANCE: dict[str, dict[str, dict[str, Any]]] = {
    EXCLUDED_ID: {
        "7D": {"roi": 12.5, "pnl": 50.0, "mdd": None, "copierPnl": 0.0, "winRate": 50.0,
               "winOrders": 2, "totalOrder": 4, "sharpRatio": None},
        "30D": {"roi": 12.5, "pnl": 50.0, "mdd": None, "copierPnl": 0.0, "winRate": 50.0,
                "winOrders": 2, "totalOrder": 4, "sharpRatio": None},
        "90D": {"roi": 12.5, "pnl": 50.0, "mdd": None, "copierPnl": 0.0, "winRate": 50.0,
                "winOrders": 2, "totalOrder": 4, "sharpRatio": None},
        "180D": {"roi": 12.5, "pnl": 50.0, "mdd": None, "copierPnl": 0.0, "winRate": 50.0,
                 "winOrders": 2, "totalOrder": 4, "sharpRatio": None},
    },
    QUALIFIED_ID: {
        "7D": {"roi": 3.2, "pnl": 320.5, "mdd": 4.1, "copierPnl": 120.0, "winRate": 62.5,
               "winOrders": 5, "totalOrder": 8, "sharpRatio": 1.8},
        "30D": {"roi": 8.4, "pnl": 840.2, "mdd": 7.2, "copierPnl": 310.0, "winRate": 58.3,
                "winOrders": 14, "totalOrder": 24, "sharpRatio": 2.1},
        "90D": {"roi": 19.18956789, "pnl": 1195.49568664, "mdd": 8.5435368,
                "copierPnl": 60671.70367501, "winRate": 99.8119, "winOrders": 527,
                "totalOrder": 528, "sharpRatio": 2.83745888},
        "180D": {"roi": 24.7, "pnl": 1600.0, "mdd": 11.4, "copierPnl": 900.0, "winRate": 61.2,
                 "winOrders": 90, "totalOrder": 147, "sharpRatio": 2.2},
    },
}


class DemoAdapter:
    """Fixture cố định cho dev/test, không gọi mạng."""

    async def list_traders(self, time_range: str, page: int) -> Page:
        items = [dict(value, window=time_range) for value in _FIXTURES.values()]
        return Page(items=items, total=len(items), page=page)

    async def get_detail(self, portfolio_id: str) -> dict[str, Any]:
        fixture = _FIXTURES.get(portfolio_id)
        if fixture is None:
            raise KeyError(portfolio_id)
        return dict(fixture)

    async def get_performance(self, portfolio_id: str, time_range: str) -> dict[str, Any]:
        fixture = _PERFORMANCE.get(portfolio_id)
        if fixture is None or time_range not in fixture:
            raise KeyError((portfolio_id, time_range))
        return {
            **fixture[time_range],
            "source": "demo",
            "window": time_range,
            "collectedAt": datetime.now(UTC).isoformat(),
        }

    async def get_positions(self, portfolio_id: str, page: int) -> Page:
        return Page(items=[], total=0, page=page)

    async def get_trades(self, portfolio_id: str, page: int) -> Page:
        return Page(items=[], total=0, page=page)

    async def get_transfers(self, portfolio_id: str, page: int) -> Page:
        return Page(items=[], total=0, page=page)
