"""Công thức quant thuần: published (T1) + derived (T2). Không truy cập DB."""

import math
from statistics import mean, median
from typing import Any

WINDOWS = ("7D", "30D", "90D", "180D")
MIN_ORDERS_FOR_RATE = 20
MIN_POSITIONS_FOR_RATIO = 5


def _f(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _i(value: Any) -> int | None:
    number = _f(value)
    return None if number is None else int(number)


def _hours_between(opened: Any, closed: Any) -> float | None:
    if not opened or not closed:
        return None
    delta = (closed - opened).total_seconds()
    return delta / 3600 if delta >= 0 else None


def published_metrics(performance: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """4 window; giữ nguyên số published, chỉ suy ra win_rate_order khi cần."""
    result: dict[str, Any] = {}
    for window in WINDOWS:
        row = performance.get(window) or {}
        total_orders = _i(row.get("total_orders", row.get("totalOrder")))
        win_orders = _i(row.get("win_orders", row.get("winOrders")))
        if total_orders and win_orders is not None:
            win_rate = win_orders / total_orders * 100
        else:
            win_rate = _f(row.get("win_rate", row.get("winRate")))
        result[window] = {
            "roi": _f(row.get("roi")),
            "pnl": _f(row.get("pnl")),
            "mdd": _f(row.get("mdd")),
            "sharpe": _f(row.get("sharpe", row.get("sharpRatio"))),
            "copier_pnl": _f(row.get("copier_pnl", row.get("copierPnl"))),
            "win_orders": win_orders,
            "total_orders": total_orders,
            "win_rate_order": win_rate,
        }
    return result


def positive_days_pct(chart_items: list[dict] | None) -> float | None:
    values = [
        _f(item.get("value"))
        for item in (chart_items or [])
        if isinstance(item, dict)
    ]
    values = [value for value in values if value is not None]
    if len(values) < 3:
        return None
    diffs = [values[index] - values[index - 1] for index in range(1, len(values))]
    if not diffs:
        return None
    return round(sum(1 for diff in diffs if diff > 0) / len(diffs) * 100, 4)


def roi_stability(published: dict[str, dict[str, Any]]) -> float | None:
    values = [
        published[window]["roi"]
        for window in WINDOWS
        if published.get(window, {}).get("roi") is not None
    ]
    if len(values) < 2:
        return None
    return round(statistics_stdev(values), 4)


def statistics_stdev(values: list[float]) -> float:
    average = sum(values) / len(values)
    variance = sum((value - average) ** 2 for value in values) / (len(values) - 1)
    return variance ** 0.5


def position_metrics(positions: list[dict[str, Any]]) -> dict[str, Any]:
    if not positions:
        return {
            "positions_count": 0,
            "max_leverage": None,
            "avg_leverage": None,
            "margin_mode": None,
            "avg_holding_hours": None,
            "median_holding_hours": None,
            "max_holding_hours": None,
            "position_win_rate": None,
            "profit_factor": None,
            "payoff_ratio": None,
            "best_position_pnl": None,
            "worst_position_pnl": None,
            "worst_position_roi": None,
            "near_liquidation_count": 0,
            "long_short_ratio": None,
            "top_symbol": None,
            "top_symbol_share": None,
            "hhi": None,
            "symbols_top3": [],
        }

    leverages = [value for value in (_f(row.get("leverage")) for row in positions) if value]
    holdings = [
        value
        for value in (
            _hours_between(row.get("opened_at"), row.get("closed_at")) for row in positions
        )
        if value is not None
    ]
    pnls = [
        value for value in (_f(row.get("closing_pnl")) for row in positions) if value is not None
    ]
    rois = [value for value in (_f(row.get("roi")) for row in positions) if value is not None]
    wins = [value for value in pnls if value > 0]
    losses = [value for value in pnls if value < 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    modes: dict[str, int] = {}
    for row in positions:
        mode = row.get("isolated")
        if mode:
            modes[mode] = modes.get(mode, 0) + 1
    longs = sum(1 for row in positions if str(row.get("side", "")).lower().startswith("long"))
    shorts = sum(1 for row in positions if str(row.get("side", "")).lower().startswith("short"))

    notionals: dict[str, float] = {}
    for row in positions:
        symbol = row.get("symbol") or "?"
        size = abs(_f(row.get("max_open_interest")) or 0.0)
        notionals[symbol] = notionals.get(symbol, 0.0) + size
    total_notional = sum(notionals.values())
    shares = sorted(
        (value / total_notional for value in notionals.values()), reverse=True
    ) if total_notional else []
    top_symbols = sorted(notionals.items(), key=lambda item: item[1], reverse=True)[:3]

    return {
        "positions_count": len(positions),
        "max_leverage": max(leverages) if leverages else None,
        "avg_leverage": round(mean(leverages), 4) if leverages else None,
        "margin_mode": max(modes, key=modes.get) if modes else None,
        "avg_holding_hours": round(mean(holdings), 4) if holdings else None,
        "median_holding_hours": round(median(holdings), 4) if holdings else None,
        "max_holding_hours": round(max(holdings), 4) if holdings else None,
        "position_win_rate": round(len(wins) / len(pnls) * 100, 4) if pnls else None,
        "profit_factor": round(gross_win / gross_loss, 4)
        if gross_loss > 0 and len(positions) >= MIN_POSITIONS_FOR_RATIO
        else None,
        "payoff_ratio": round(mean(wins) / abs(mean(losses)), 4)
        if wins and losses and len(positions) >= MIN_POSITIONS_FOR_RATIO
        else None,
        "best_position_pnl": max(pnls) if pnls else None,
        "worst_position_pnl": min(pnls) if pnls else None,
        "worst_position_roi": round(min(rois) * 100, 4) if rois else None,
        "near_liquidation_count": sum(1 for value in rois if -0.8 < value <= -0.5),
        "long_short_ratio": round(longs / shorts, 4) if shorts else None,
        "top_symbol": top_symbols[0][0] if top_symbols else None,
        "top_symbol_share": round(shares[0] * 100, 4) if shares else None,
        "hhi": round(sum(share * share for share in shares), 6) if shares else None,
        "symbols_top3": [
            {
                "symbol": symbol,
                "notional": round(value, 2),
                "share_pct": round(value / total_notional * 100, 4) if total_notional else None,
            }
            for symbol, value in top_symbols
        ],
    }


def trade_metrics(trades: list[dict[str, Any]], pnl_90d: float | None = None) -> dict[str, Any]:
    if not trades:
        return {
            "total_fills": 0,
            "fills_per_day": None,
            "avg_fill_notional": None,
            "max_fill_notional": None,
            "total_fees": None,
            "fee_drag_pct": None,
            "realized_pnl_fills": None,
            "active_days": 0,
        }

    notionals = [abs(_f(row.get("quantity")) or 0.0) for row in trades]
    fees = [_f(row.get("fee")) or 0.0 for row in trades]
    realized = [_f(row.get("realized_profit")) or 0.0 for row in trades]
    times = [row.get("trade_time") for row in trades if row.get("trade_time")]
    active_days = len({moment.date() for moment in times}) or 1
    total_fees = sum(fees)
    gross_pnl = sum(realized) or (pnl_90d or 0.0)
    return {
        "total_fills": len(trades),
        "fills_per_day": round(len(trades) / active_days, 4),
        "avg_fill_notional": round(mean(notionals), 4) if notionals else None,
        "max_fill_notional": round(max(notionals), 4) if notionals else None,
        "total_fees": round(total_fees, 8),
        "fee_drag_pct": round(total_fees / abs(gross_pnl) * 100, 4) if gross_pnl else None,
        "realized_pnl_fills": round(sum(realized), 4),
        "active_days": active_days,
    }


def transfer_metrics(transfers: list[dict[str, Any]]) -> dict[str, Any]:
    deposits = sum(
        _f(row.get("amount")) or 0.0
        for row in transfers
        if str(row.get("trans_type") or "").upper()
        in {"LEAD_DEPOSIT", "LEAD_INVEST"}
    )
    withdrawals = sum(
        _f(row.get("amount")) or 0.0
        for row in transfers
        if str(row.get("trans_type") or "").upper() == "LEAD_WITHDRAW"
    )
    return {
        "transfers_count": len(transfers),
        "deposits": round(deposits, 4),
        "withdrawals": round(withdrawals, 4),
        "net_flow": round(deposits - withdrawals, 4),
    }


def ratio_metrics(
    published: dict[str, Any],
    positions: dict[str, Any],
    aum: float | None,
    copy_aum: float | None,
    current_copiers: int | None,
    copier_pnl_90d: float | None,
) -> dict[str, Any]:
    roi_90 = published["90D"]["roi"]
    mdd_90 = published["90D"]["mdd"]
    calmar = (
        round(roi_90 / mdd_90, 4)
        if roi_90 is not None and mdd_90 is not None and 0 < mdd_90 <= 100
        else None
    )
    return {
        "calmar": calmar,
        "copy_aum_ratio": round(copy_aum / aum * 100, 4)
        if aum and copy_aum is not None
        else None,
        "copier_pnl_per_copier": round(copier_pnl_90d / max(current_copiers or 1, 1), 4)
        if copier_pnl_90d is not None
        else None,
        "low_sample": (published["90D"]["total_orders"] or 0) < MIN_ORDERS_FOR_RATE,
        "insufficient_positions": (positions.get("positions_count") or 0)
        < MIN_POSITIONS_FOR_RATIO,
    }


def missing_flags(metrics: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    published = metrics["published"]["90D"]
    if published["mdd"] is None:
        flags.append("missing_mdd")
    if published["sharpe"] is None:
        flags.append("missing_sharpe")
    if metrics.get("benchmark_return") is None:
        flags.append("missing_benchmark")
    if metrics["derived"].get("low_sample"):
        flags.append("low_sample")
    if metrics["derived"].get("insufficient_positions"):
        flags.append("insufficient_positions")
    if not metrics.get("trades", {}).get("total_fills"):
        flags.append("missing_trades")
    return flags
