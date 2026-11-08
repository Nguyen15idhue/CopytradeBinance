"""Tool build_copy_plan: cấu hình copy tham chiếu cho một trader + vốn."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.agent.db_tools import _ev
from app.services.agent.schema import ToolResult
from app.services.agent.tools import register_tool
from app.services.copy_plan.data import load_copy_context
from app.services.copy_plan.limits import limits_from_settings
from app.services.copy_plan.planner import build_copy_plan

INPUT_KEYS = (
    "available_usd",
    "risk_policy",
    "preferred_mode",
    "symbol_scope",
    "symbols",
    "allow_tradfi",
    "max_cost_order_pct",
    "total_stop_loss_usd",
    "take_profit_pct",
    "stop_loss_pct",
    "close_all_at_take_profit",
    "copy_existing_positions",
    "better_entry_price",
    "auto_invest",
    "max_slippage_pct",
)


@register_tool(
    "build_copy_plan",
    "Tạo cấu hình copy tham chiếu cho trader theo vốn; trả đủ trường form Binance, "
    "thiếu dữ liệu thì null + lý do, không bịa số.",
    {
        "type": "object",
        "properties": {
            "trader_id": {"type": "string"},
            "capital_usd": {"type": "number"},
            "available_usd": {"type": "number"},
            "risk_policy": {
                "type": "string",
                "enum": ["safe", "balanced", "aggressive", "custom"],
            },
            "preferred_mode": {
                "type": "string",
                "enum": ["fixed_ratio", "fixed_amount"],
            },
            "symbol_scope": {
                "type": "string",
                "enum": ["all", "exclude_low_liquidity", "custom"],
            },
            "symbols": {"type": "array", "items": {"type": "string"}},
            "allow_tradfi": {"type": "boolean"},
            "max_cost_order_pct": {"type": "number"},
            "total_stop_loss_usd": {"type": "number"},
            "take_profit_pct": {"type": "number"},
            "stop_loss_pct": {"type": "number"},
            "close_all_at_take_profit": {"type": "boolean"},
            "copy_existing_positions": {"type": "boolean"},
            "better_entry_price": {"type": "boolean"},
            "auto_invest": {"type": "boolean"},
            "max_slippage_pct": {"type": "number"},
        },
        "required": ["trader_id", "capital_usd"],
    },
)
async def build_copy_plan_tool(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    trader_id = str(args.get("trader_id") or "")
    if not trader_id:
        return ToolResult.fail("Thiếu trader_id")
    try:
        capital = float(args.get("capital_usd"))
    except (TypeError, ValueError):
        return ToolResult.fail("capital_usd không hợp lệ")
    if capital <= 0:
        return ToolResult.fail("capital_usd phải > 0")

    context = await load_copy_context(db, trader_id)
    if context is None:
        return ToolResult.fail(f"Không có dữ liệu cho trader {trader_id}")
    constraints = context["constraints"]
    if not constraints:
        return ToolResult.fail(f"Không có copy constraints cho {trader_id}")

    inputs: dict[str, Any] = {"trader_id": trader_id, "capital_usd": capital}
    for key in INPUT_KEYS:
        if args.get(key) is not None:
            inputs[key] = args[key]
    try:
        plan = build_copy_plan(
            inputs,
            constraints,
            context["metrics"],
            symbol_stats=context["symbol_stats"],
            margin_mode=context["margin_mode"],
            limits=limits_from_settings(get_settings()),
        )
    except ValueError as exc:
        return ToolResult.fail(str(exc))

    as_of = context["as_of"]
    metrics = context["metrics"]
    symbol_stats = context["symbol_stats"]
    evidence = [
        _ev(trader_id, "fixed_ratio_min_copy_usd",
            constraints.get("fixed_radio_min_copy_usd"), "USDT", as_of),
        _ev(trader_id, "fixed_amount_min_copy_usd",
            constraints.get("fixed_amount_min_copy_usd"), "USDT", as_of),
        _ev(trader_id, "mdd_90d", metrics.get("mdd_90d"), "%", as_of),
        _ev(trader_id, "worst_position_roi", metrics.get("worst_position_roi"), "%", as_of),
        _ev(trader_id, "max_leverage", metrics.get("max_leverage"), "x", as_of),
        _ev(trader_id, "avg_leverage", metrics.get("avg_leverage"), "x", as_of),
        _ev(trader_id, "profit_sharing_rate",
            constraints.get("profit_sharing_rate"), "%", as_of),
    ]
    margin_mode = context["margin_mode"]
    if margin_mode and margin_mode.get("mode"):
        evidence.append(
            _ev(trader_id, "margin_mode", margin_mode["mode"], None, as_of)
        )
    for item in symbol_stats.get("top", [])[:5]:
        evidence.append(
            _ev(
                trader_id,
                f"symbol_share_{item['symbol']}",
                item.get("share_pct"),
                "%",
                as_of,
            )
        )
    evidence = [item for item in evidence if item.value is not None]
    plan["evidence_ids"] = [item.id for item in evidence]
    return ToolResult(
        data=plan,
        meta={
            "source": "database",
            "as_of": as_of,
            "row_ids": [trader_id],
            "config_version": None,
            "limits_version": plan["limits_version"],
        },
        evidence=evidence,
    )
