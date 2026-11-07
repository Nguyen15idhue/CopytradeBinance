"""CLI vận hành collector Phase 2: scan universe, deep fetch."""

import argparse
import asyncio
import json

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.collector.binance import BinanceBapiAdapter
from app.services.collector.lock import CollectorLock, LockUnavailable
from app.services.universe import recompute_universe, scan_universe


async def cmd_scan() -> int:
    settings = get_settings()
    if settings.collector_kill_switch:
        print(json.dumps({"skipped": True, "reason": "COLLECTOR_KILL_SWITCH=true"}))
        return 0
    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock("lock:collector:scan"):
            async with SessionLocal() as db:
                result = await scan_universe(adapter, db)
                tiering = await recompute_universe(db)
                print(
                    json.dumps(
                        {"scan": result.as_dict(), "tiering": tiering}, ensure_ascii=False
                    )
                )
    except LockUnavailable as exc:
        print(json.dumps({"skipped": True, "reason": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        await adapter.aclose()
    return 0


async def cmd_recompute() -> int:
    async with SessionLocal() as db:
        print(json.dumps(await recompute_universe(db), ensure_ascii=False))
    return 0


async def cmd_perf() -> int:
    from app.services.deep_fetch import fetch_performance_for_watch

    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock("lock:collector:deep"):
            async with SessionLocal() as db:
                result = await fetch_performance_for_watch(adapter, db)
                print(json.dumps(result, ensure_ascii=False))
    except LockUnavailable as exc:
        print(json.dumps({"skipped": True, "reason": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        await adapter.aclose()
    return 0


async def cmd_detail() -> int:
    from app.services.deep_fetch import fetch_detail_and_history

    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock("lock:collector:deep"):
            async with SessionLocal() as db:
                result = await fetch_detail_and_history(adapter, db)
                print(json.dumps(result, ensure_ascii=False))
    except LockUnavailable as exc:
        print(json.dumps({"skipped": True, "reason": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        await adapter.aclose()
    return 0


async def cmd_trades() -> int:
    from app.services.deep_fetch import fetch_full_trades

    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock("lock:collector:deep"):
            async with SessionLocal() as db:
                result = await fetch_full_trades(adapter, db)
                print(json.dumps(result, ensure_ascii=False))
    except LockUnavailable as exc:
        print(json.dumps({"skipped": True, "reason": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        await adapter.aclose()
    return 0


async def cmd_deep() -> int:
    from app.services.deep_fetch import run_deep_fetch

    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock("lock:collector:deep"):
            async with SessionLocal() as db:
                result = await run_deep_fetch(adapter, db)
                print(json.dumps(result, ensure_ascii=False))
    except LockUnavailable as exc:
        print(json.dumps({"skipped": True, "reason": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        await adapter.aclose()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CLI collector Phase 2")
    parser.add_argument(
        "command", choices=["scan", "recompute", "perf", "detail", "trades", "deep"]
    )
    args = parser.parse_args()
    if args.command == "scan":
        return asyncio.run(cmd_scan())
    if args.command == "recompute":
        return asyncio.run(cmd_recompute())
    if args.command == "perf":
        return asyncio.run(cmd_perf())
    if args.command == "detail":
        return asyncio.run(cmd_detail())
    if args.command == "trades":
        return asyncio.run(cmd_trades())
    return asyncio.run(cmd_deep())


if __name__ == "__main__":
    raise SystemExit(main())
