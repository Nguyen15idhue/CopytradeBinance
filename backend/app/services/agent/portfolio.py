"""Phân tích trader với vốn cụ thể (không đưa lời khuyên đầu tư)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent.db_tools import _ev, _has_slot
from app.services.agent.schema import ToolResult, utcnow_iso
from app.services.agent.tools import register_tool


def evaluate_fit(
    constraints: dict[str, Any],
    metrics: dict[str, Any],
    capital_usd: float,
) -> dict[str, Any]:
    """Hàm thuần: tính can_copy/capital_ok/loss/missing từ dữ liệu đã có."""
    modes: dict[str, float] = {}
    for key, label in (
        ("fixed_radio_min_copy_usd", "fixed_ratio"),
        ("fixed_amount_min_copy_usd", "fixed_amount"),
    ):
        value = constraints.get(key)
        if value is not None:
            try:
                modes[label] = float(value)
            except (TypeError, ValueError):
                pass
    missing: list[str] = []
    warnings: list[str] = []
    if not modes:
        missing.append("min_copy_usd")
    min_copy = min(modes.values()) if modes else None
    if min_copy is None:
        capital_ok: bool | None = None
        can_copy: bool | str = "unknown"
        warnings.append("Thiếu min copy — không kết luận được vốn có đủ không")
    else:
        capital_ok = capital_usd >= min_copy
        can_copy = bool(capital_ok)

    def pct_loss(rate: Any) -> float | None:
        if rate is None:
            return None
        try:
            return round(capital_usd * float(rate) / 100, 2)
        except (TypeError, ValueError):
            return None

    mdd = metrics.get("mdd_90d")
    max_loss = pct_loss(mdd)
    if max_loss is None:
        missing.append("max_loss_at_mdd_usd")
    worst = pct_loss(metrics.get("worst_position_roi"))
    if worst is None:
        missing.append("worst_position_loss_usd")
    if metrics.get("risk_level") is None and metrics.get("risk_score") is None:
        missing.append("risk")
    return {
        "capital_usd": capital_usd,
        "can_copy": can_copy,
        "min_copy_usd": min_copy,
        "modes": modes,
        "capital_ok": capital_ok,
        "max_loss_at_mdd_usd": max_loss,
        "worst_position_loss_usd": worst,
        "missing_fields": missing,
        "warnings": warnings,
    }


@register_tool(
    "analyze_portfolio_fit",
    "Kiểm tra vốn có đủ min copy/slot và ước tính lỗ tối đa theo MDD.",
    {"type": "object",
     "properties": {"trader_id": {"type": "string"},
                    "capital_usd": {"type": "number"},
                    "risk_policy": {"type": "string"}},
     "required": ["trader_id", "capital_usd"]},
)
async def analyze_portfolio_fit(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    from sqlalchemy import select
    from sqlalchemy import text as sql_text

    from app.models.trader_metric import TraderMetric

    trader_id = str(args.get("trader_id") or "")
    if not trader_id:
        return ToolResult.fail("Thiếu trader_id")
    try:
        capital = float(args.get("capital_usd"))
    except (TypeError, ValueError):
        return ToolResult.fail("capital_usd không hợp lệ")
    if capital <= 0:
        return ToolResult.fail("capital_usd phải > 0")

    row = (
        await db.execute(
            sql_text(
                "SELECT fixed_radio_min_copy_usd, fixed_amount_min_copy_usd,"
                " profit_sharing_rate, current_copy_count, max_copy_count,"
                " margin_balance, aum_amount, copy_aum, as_of"
                " FROM agent_trader_copy_constraints WHERE lead_portfolio_id = :tid"
            ),
            {"tid": trader_id},
        )
    ).mappings().first()
    if row is None:
        return ToolResult.fail(f"Không có dữ liệu copy constraints cho {trader_id}")
    metric = (
        await db.execute(
            select(TraderMetric).where(TraderMetric.lead_portfolio_id == trader_id)
        )
    ).scalars().first()
    derived = ((metric.metrics or {}).get("derived") or {}) if metric else {}
    def num(value: object) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    metrics = {
        "mdd_90d": num(metric.mdd_90d) if metric else None,
        "worst_position_roi": derived.get("worst_position_roi"),
        "max_leverage": num(metric.max_leverage) if metric else None,
        "fee_drag_pct": num(metric.fee_drag_pct) if metric else None,
        "risk_level": metric.risk_level if metric else None,
        "risk_score": num(metric.risk_score) if metric else None,
        "veto": metric.risk_veto if metric else None,
    }
    fit = evaluate_fit(dict(row), metrics, capital)
    slot = await _has_slot(db, trader_id)
    as_of = row.get("as_of")
    as_of_iso = as_of.isoformat() if hasattr(as_of, "isoformat") else (as_of or utcnow_iso())
    flags = list((metric.metrics or {}).get("flags") or []) if metric else []
    mdd_value = metrics["mdd_90d"]
    mdd_suspect = mdd_value is not None and 0 < mdd_value < 0.01
    warnings = list(fit.get("warnings") or [])
    if mdd_suspect:
        warnings.append(
            "MDD published gần 0 (<0.01%) dù ROI dương; không dùng để kết luận rủi ro thấp."
        )
    if metrics["veto"] or metrics["risk_level"] in ("high", "critical"):
        warnings.append(
            f"Risk {metrics['risk_level']} / veto {metrics['veto']}; can_copy chỉ là "
            "điều kiện kỹ thuật, không phải khuyến nghị."
        )
    data = {
        **fit,
        "warnings": warnings,
        "trader_id": trader_id,
        "profit_sharing_rate": row.get("profit_sharing_rate"),
        "fee_drag_pct": metrics["fee_drag_pct"],
        "max_leverage": metrics["max_leverage"],
        "slot_available": slot,
        "risk": {"level": metrics["risk_level"], "score": metrics["risk_score"],
                 "veto": metrics["veto"]},
        "data_quality": {
            "flags": flags,
            "missing_trades": "missing_trades" in flags,
            "mdd_published": mdd_value,
            "mdd_suspect": mdd_suspect,
        },
        "risk_policy": args.get("risk_policy"),
        "as_of": as_of_iso,
    }
    evidence = [
        _ev(trader_id, "capital_usd", capital, "USDT", as_of_iso),
        _ev(trader_id, "min_copy_usd", fit["min_copy_usd"], "USDT", as_of_iso),
        _ev(trader_id, "mdd_90d", metrics["mdd_90d"], "%", as_of_iso),
        _ev(trader_id, "profit_sharing_rate", row.get("profit_sharing_rate"), "%", as_of_iso),
        _ev(trader_id, "max_leverage", metrics["max_leverage"], "x", as_of_iso),
    ]
    evidence = [item for item in evidence if item.value is not None]
    return ToolResult(
        data=data,
        meta={"source": "database", "as_of": as_of_iso, "row_ids": [trader_id]},
        evidence=evidence,
    )
