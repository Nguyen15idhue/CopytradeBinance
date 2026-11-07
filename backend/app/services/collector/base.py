from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class Page:
    items: list[dict[str, Any]]
    total: int
    page: int


class DataSourceAdapter(Protocol):
    async def list_traders(
        self, time_range: str, page: int, portfolio_type: str = "PUBLIC"
    ) -> Page: ...

    async def get_detail(self, portfolio_id: str) -> dict[str, Any]: ...

    async def get_performance(self, portfolio_id: str, time_range: str) -> dict[str, Any]: ...

    async def get_positions(self, portfolio_id: str, page: int) -> Page: ...

    async def get_trades(self, portfolio_id: str, page: int) -> Page: ...

    async def get_transfers(self, portfolio_id: str, page: int) -> Page: ...
