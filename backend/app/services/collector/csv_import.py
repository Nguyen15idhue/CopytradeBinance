from app.services.collector.base import Page


class CsvImportAdapter:
    """Fallback CSV — stub cho Phase 1, hoàn thiện khi BAPI không khả dụng."""

    async def list_traders(
        self, time_range: str, page: int, portfolio_type: str = "PUBLIC"
    ) -> Page:
        raise NotImplementedError("CsvImportAdapter chưa triển khai trong Phase 1")

    async def get_detail(self, portfolio_id: str) -> dict:
        raise NotImplementedError("CsvImportAdapter chưa triển khai trong Phase 1")

    async def get_performance(self, portfolio_id: str, time_range: str) -> dict:
        raise NotImplementedError("CsvImportAdapter chưa triển khai trong Phase 1")

    async def get_positions(self, portfolio_id: str, page: int) -> Page:
        raise NotImplementedError("CsvImportAdapter chưa triển khai trong Phase 1")

    async def get_trades(self, portfolio_id: str, page: int) -> Page:
        raise NotImplementedError("CsvImportAdapter chưa triển khai trong Phase 1")

    async def get_transfers(self, portfolio_id: str, page: int) -> Page:
        raise NotImplementedError("CsvImportAdapter chưa triển khai trong Phase 1")
