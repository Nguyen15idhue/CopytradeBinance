"""Adapter DB cho copy plan: constraints, metrics, margin mode, symbol stats."""

from datetime import datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trader_metric import TraderMetric
from app.services.agent.schema import utcnow_iso

TRADFI_PREFIXES = (
    "XAU", "XAG", "XPT", "XPD",
    "EUR", "GBP", "JPY", "AUD", "CHF", "CAD", "NZD", "CNH", "HKD", "SGD",
)
TRADFI_CONFIDENCE = "estimated"


def _num(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def normalize_margin_mode(value: Any) -> str | None:
    """Chuẩn hoá positions.isolated về isolated/cross."""
    if value is None:
        return None
    raw = str(value).strip().lower()
    if raw in ("true", "isolated", "1"):
        return "isolated"
    if raw in ("false", "cross", "crossed", "0"):
        return "cross"
    return None


def is_tradfi(symbol: str) -> bool:
    upper = symbol.upper()
    return any(upper.startswith(prefix) for prefix in TRADFI_PREFIXES)


def summarize_symbols(
    position_rows: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Gộp vị thế + giao dịch thành top symbol và cờ TradFi (estimated)."""
    stats: dict[str, dict[str, float]] = {}
    for row in position_rows:
        symbol = row.get("symbol")
        if not symbol:
            continue
        item = stats.setdefault(str(symbol), {"pos_count": 0.0, "pos_notional": 0.0})
        item["pos_count"] += float(row.get("cnt") or 0)
        item["pos_notional"] += float(row.get("notional") or 0)
    for row in trade_rows:
        symbol = row.get("symbol")
        if not symbol:
            continue
        item = stats.setdefault(str(symbol), {"pos_count": 0.0, "pos_notional": 0.0})
        item["trade_count"] = float(row.get("cnt") or 0)
        item["trade_notional"] = float(row.get("notional") or 0)

    enriched: list[dict[str, Any]] = []
    for symbol, item in stats.items():
        pos_notional = float(item.get("pos_notional") or 0)
        trade_notional = float(item.get("trade_notional") or 0)
        notional = max(pos_notional, trade_notional)
        enriched.append(
            {
                "symbol": symbol,
                "trade_count": int(item.get("trade_count") or 0),
                "position_count": int(item.get("pos_count") or 0),
                "notional_usdt": round(notional, 2),
            }
        )
    total_notional = sum(item["notional_usdt"] for item in enriched)
    total_count = sum(item["trade_count"] + item["position_count"] for item in enriched)
    for item in enriched:
        if total_notional > 0:
            item["share_pct"] = round(item["notional_usdt"] / total_notional * 100, 2)
        elif total_count > 0:
            count = item["trade_count"] + item["position_count"]
            item["share_pct"] = round(count / total_count * 100, 2)
        else:
            item["share_pct"] = 0.0
    enriched.sort(key=lambda item: (-item["share_pct"], item["symbol"]))
    top = enriched[:10]
    tradfi = sorted(item["symbol"] for item in enriched if is_tradfi(item["symbol"]))
    return {
        "top": top,
        "tradfi": tradfi,
        "tradfi_confidence": TRADFI_CONFIDENCE,
        "symbol_count": len(enriched),
        "low_liquidity": None,
    }


async def load_copy_context(db: AsyncSession, trader_id: str) -> dict[str, Any] | None:
    """Nạp dữ liệu cần cho build_copy_plan; None nếu không có trader."""
    constraints = (
        await db.execute(
            text(
                "SELECT lead_portfolio_id, fixed_radio_min_copy_usd,"
                " fixed_amount_min_copy_usd, profit_sharing_rate,"
                " current_copy_count, max_copy_count, margin_balance,"
                " aum_amount, copy_aum, as_of"
                " FROM agent_trader_copy_constraints WHERE lead_portfolio_id = :tid"
            ),
            {"tid": trader_id},
        )
    ).mappings().first()
    metric = (
        await db.execute(
            select(TraderMetric).where(TraderMetric.lead_portfolio_id == trader_id)
        )
    ).scalars().first()
    if constraints is None and metric is None:
        return None
    derived = ((metric.metrics or {}).get("derived") or {}) if metric else {}
    metrics = {
        "mdd_90d": _num(metric.mdd_90d) if metric else None,
        "worst_position_roi": derived.get("worst_position_roi"),
        "max_leverage": _num(metric.max_leverage) if metric else None,
        "avg_leverage": _num(metric.avg_leverage) if metric else None,
        "risk_level": metric.risk_level if metric else None,
        "risk_score": _num(metric.risk_score) if metric else None,
        "risk_veto": metric.risk_veto if metric else None,
    }

    margin_rows = (
        await db.execute(
            text(
                "SELECT isolated, count(*) AS cnt FROM positions"
                " WHERE lead_portfolio_id = :tid GROUP BY isolated"
            ),
            {"tid": trader_id},
        )
    ).mappings().all()
    margin_counts: dict[str, int] = {}
    for row in margin_rows:
        mode = normalize_margin_mode(row.get("isolated"))
        if mode:
            margin_counts[mode] = margin_counts.get(mode, 0) + int(row.get("cnt") or 0)
    margin_mode: dict[str, Any] | None = None
    total_margin = sum(margin_counts.values())
    if total_margin > 0:
        mode, count = max(margin_counts.items(), key=lambda item: item[1])
        margin_mode = {"mode": mode, "confidence": round(count / total_margin, 3)}

    position_rows = (
        await db.execute(
            text(
                "SELECT symbol, count(*) AS cnt,"
                " coalesce(sum(max_open_interest), 0) AS notional"
                " FROM positions WHERE lead_portfolio_id = :tid"
                " AND symbol IS NOT NULL GROUP BY symbol"
            ),
            {"tid": trader_id},
        )
    ).mappings().all()
    trade_rows = (
        await db.execute(
            text(
                "SELECT symbol, count(*) AS cnt,"
                " coalesce(sum(price * quantity), 0) AS notional"
                " FROM trades WHERE lead_portfolio_id = :tid"
                " AND symbol IS NOT NULL GROUP BY symbol"
            ),
            {"tid": trader_id},
        )
    ).mappings().all()
    symbol_stats = summarize_symbols([dict(row) for row in position_rows],
                                     [dict(row) for row in trade_rows])

    as_of: datetime | str | None = constraints.get("as_of") if constraints else None
    if as_of is None and metric is not None:
        as_of = metric.computed_at
    as_of_iso = as_of.isoformat() if hasattr(as_of, "isoformat") else (as_of or utcnow_iso())
    return {
        "trader_id": trader_id,
        "constraints": dict(constraints) if constraints else {},
        "metrics": metrics,
        "margin_mode": margin_mode,
        "symbol_stats": symbol_stats,
        "as_of": as_of_iso,
    }
