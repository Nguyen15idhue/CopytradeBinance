"""Smoke test live 6 endpoint BAPI (opt-in, chỉ chạy khi cần kiểm tra mạng)."""

import asyncio
import sys

from app.services.collector.binance import BinanceBapiAdapter

DEFAULT_ID = "4520644381136785152"


async def main(portfolio_id: str) -> int:
    async with BinanceBapiAdapter() as adapter:
        page = await adapter.list_traders("90D", 1, "PUBLIC")
        print(f"list PUBLIC: {len(page.items)} item, total={page.total}")

        detail = await adapter.get_detail(portfolio_id)
        print(f"detail {portfolio_id}: status={detail.get('status')} paused={detail.get('isPaused')}")

        perf = await adapter.get_performance(portfolio_id, "90D")
        print(f"performance 90D: roi={perf.get('roi')} mdd={perf.get('mdd')}")

        positions = await adapter.get_positions(portfolio_id, 1)
        trades = await adapter.get_trades(portfolio_id, 1)
        transfers = await adapter.get_transfers(portfolio_id, 1)
        print(
            f"positions total={positions.total} | trades total={trades.total} "
            f"| transfers total={transfers.total}"
        )
    print("Smoke BAPI: PASS")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ID
    raise SystemExit(asyncio.run(main(target)))
