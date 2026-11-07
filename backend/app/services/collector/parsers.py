"""Chuẩn hóa payload BAPI → dict cho DB."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def ms_to_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


def _hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_position(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "position_id": str(item.get("positionId") or item.get("id") or ""),
        "symbol": item.get("symbol"),
        "side": item.get("side"),
        "leverage": item.get("leverage"),
        "isolated": item.get("isolated"),
        "opened_at": ms_to_dt(item.get("opened")),
        "closed_at": ms_to_dt(item.get("closed")),
        "avg_cost": item.get("avgCost"),
        "avg_close_price": item.get("avgClosePrice"),
        "closing_pnl": item.get("closingPnl"),
        "max_open_interest": item.get("maxOpenInterest"),
        "roi": item.get("roi"),
        "status": item.get("status"),
        "raw": item,
    }


def parse_trade(item: dict[str, Any]) -> dict[str, Any]:
    key = {
        "time": item.get("time"),
        "symbol": item.get("symbol"),
        "side": item.get("side"),
        "price": item.get("price"),
        "qty": item.get("qty"),
        "quantity": item.get("quantity"),
        "fee": item.get("fee"),
        "positionSide": item.get("positionSide"),
    }
    return {
        "trade_hash": _hash(key),
        "trade_time": ms_to_dt(item.get("time")),
        "symbol": item.get("symbol"),
        "side": item.get("side"),
        "price": item.get("price"),
        "fee": item.get("fee"),
        "fee_asset": item.get("feeAsset"),
        "quantity": item.get("quantity"),
        "qty": item.get("qty"),
        "realized_profit": item.get("realizedProfit"),
        "position_side": item.get("positionSide"),
        "raw": item,
    }


def parse_transfer(item: dict[str, Any]) -> dict[str, Any]:
    key = {
        "time": item.get("time"),
        "coin": item.get("coin"),
        "amount": item.get("amount"),
        "from": item.get("from"),
        "to": item.get("to"),
        "transType": item.get("transType"),
    }
    return {
        "transfer_hash": _hash(key),
        "transfer_time": ms_to_dt(item.get("time")),
        "coin": item.get("coin"),
        "amount": item.get("amount"),
        "from_account": item.get("from"),
        "to_account": item.get("to"),
        "trans_type": item.get("transType"),
        "raw": item,
    }
