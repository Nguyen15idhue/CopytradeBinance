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
                print(json.dumps(result.as_dict(), ensure_ascii=False))
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
    parser.add_argument("command", choices=["scan", "recompute", "deep"])
    args = parser.parse_args()
    if args.command == "scan":
        return asyncio.run(cmd_scan())
    if args.command == "recompute":
        return asyncio.run(cmd_recompute())
    return asyncio.run(cmd_deep())


if __name__ == "__main__":
    raise SystemExit(main())
