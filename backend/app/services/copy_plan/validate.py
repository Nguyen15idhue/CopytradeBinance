"""Kiểm tra copy_plan: biên, evidence, nhất quán (kế hoạch 06 §9)."""

from typing import Any

from app.services.copy_plan.limits import DEFAULT_LIMITS, CopyLimits

REQUIRED_KEYS = (
    "version",
    "trader_id",
    "copy_mode",
    "copy_amount_usd",
    "cost_per_order_usd",
    "max_cost_per_order_pct",
    "total_stop_loss_usd",
    "symbols",
    "copy_existing_positions",
    "better_entry_price",
    "margin_mode",
    "leverage",
    "max_slippage_pct",
    "take_profit_pct",
    "stop_loss_pct",
    "close_all_at_take_profit",
    "auto_invest",
    "can_copy",
    "warnings",
    "missing_fields",
)
EVIDENCE_SOURCES = {"computed", "derived", "published"}
MONEY_FIELDS = ("copy_amount_usd", "total_stop_loss_usd", "cost_per_order_usd")


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _walk_fields(node: Any) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if "value" in node and "source" in node and "status" in node:
            fields.append(node)
        for item in node.values():
            fields.extend(_walk_fields(item))
    elif isinstance(node, list):
        for item in node:
            fields.extend(_walk_fields(item))
    return fields


def validate_plan(
    plan: dict[str, Any] | None,
    fact_ids: set[str] | None = None,
    limits: CopyLimits | None = None,
) -> list[str]:
    """Trả danh sách warning; không tự sửa số."""
    limits = limits or DEFAULT_LIMITS
    warnings: list[str] = []
    if not plan:
        return ["copy_plan_missing"]
    for key in REQUIRED_KEYS:
        if key not in plan:
            warnings.append(f"copy_plan_missing_key:{key}")
    if warnings:
        return warnings

    capital = _number((plan.get("inputs") or {}).get("capital_usd"))
    mode = (plan.get("copy_mode") or {}).get("value")
    eligible = (plan.get("copy_mode") or {}).get("eligible_modes") or []

    copy_amount = _number((plan.get("copy_amount_usd") or {}).get("value"))
    if copy_amount is not None:
        if copy_amount <= 0:
            warnings.append("copy_amount_not_positive")
        if mode == "fixed_ratio" and copy_amount > limits.ratio_copy_max_usd:
            warnings.append("copy_amount_over_ratio_max")
        if mode == "fixed_amount" and copy_amount > limits.amount_copy_max_usd:
            warnings.append("copy_amount_over_amount_max")

    cost = _number((plan.get("cost_per_order_usd") or {}).get("value"))
    if cost is not None and not (
        limits.amount_order_min_usd <= cost <= limits.amount_order_max_usd
    ):
        warnings.append("cost_per_order_out_of_bounds")

    total_sl = _number((plan.get("total_stop_loss_usd") or {}).get("value"))
    if total_sl is not None:
        if total_sl < 0:
            warnings.append("total_stop_loss_negative")
        if capital is not None and total_sl > capital:
            warnings.append("total_stop_loss_over_capital")

    sl = _number((plan.get("stop_loss_pct") or {}).get("value"))
    if sl is not None and not (limits.sl_min_pct <= sl <= limits.sl_max_pct):
        warnings.append("stop_loss_pct_out_of_bounds")
    tp = _number((plan.get("take_profit_pct") or {}).get("value"))
    if tp is not None and not (limits.tp_min_pct <= tp <= limits.tp_max_pct):
        warnings.append("take_profit_pct_out_of_bounds")
    pct = _number((plan.get("max_cost_per_order_pct") or {}).get("value"))
    if pct is not None and not (
        limits.max_cost_order_pct_min <= pct <= limits.max_cost_order_pct_max
    ):
        warnings.append("max_cost_order_pct_out_of_bounds")

    can_copy = plan.get("can_copy")
    if can_copy is True:
        if mode is not None:
            field = plan.get("copy_amount_usd") or {}
            minimum = _number(field.get("min"))
            if minimum is not None and (copy_amount or 0) < minimum:
                warnings.append("can_copy_true_below_mode_min")
        elif not eligible:
            warnings.append("can_copy_true_without_eligible_mode")
        if plan.get("slot_available") is False:
            warnings.append("can_copy_true_without_slot")
        copy_field = plan.get("copy_amount_usd") or {}
        max_available = _number(copy_field.get("max_available"))
        if max_available is not None and (copy_amount or 0) > max_available:
            warnings.append("copy_amount_over_available")

    for field in _walk_fields(plan):
        source = field.get("source")
        status = field.get("status")
        if source in EVIDENCE_SOURCES and isinstance(field.get("value"), (int, float)):
            evidence_id = field.get("evidence_id")
            if not evidence_id:
                warnings.append("copy_plan_evidence_missing")
            elif fact_ids is not None and evidence_id not in fact_ids:
                warnings.append(f"copy_plan_evidence_unknown:{evidence_id}")
        if source == "default" and status == "defaulted" and not field.get("note"):
            warnings.append("copy_plan_default_without_note")
    return list(dict.fromkeys(warnings))
