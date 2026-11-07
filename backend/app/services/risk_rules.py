"""Risk rules R01–R11. Không tự loại trader; chỉ tạo event + evidence."""

from typing import Any

SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low_sample": 1,
    "confidence_penalty": 1,
    "insufficient": 1,
    "unknown": 0,
}

LEVEL_ALIAS = {
    "low_sample": "low",
    "confidence_penalty": "low",
    "insufficient": "low",
}

RULES = {
    "R01": ("runtime_days", "insufficient", 30, "lt", "Runtime < 30 ngày"),
    "R02": ("mdd_90d", "high", 20, "gt", "MDD > 20%"),
    "R03": ("mdd_90d", "critical", 30, "gt", "MDD > 30%"),
    "R04": ("max_leverage", "high", 10, "gt", "Max leverage > 10x"),
    "R05": ("max_leverage", "critical", 20, "gt", "Max leverage > 20x"),
    "R06": ("worst_position_roi", "critical", -80, "le", "Position ROI ≤ −80%"),
    "R07": ("total_orders_90d", "low_sample", 20, "lt", "totalOrder < 20"),
    "R08": ("sharpe_90d", "confidence_penalty", None, "null", "Sharpe null"),
    "R09": ("freshness_minutes", "medium", 150, "gt", "Dữ liệu cũ > 150 phút"),
    "R10": ("copier_vs_lead", "high", 0, "copier_negative", "Copier PnL âm, lead dương"),
    "R11": ("copy_aum_ratio", "medium", 5, "lt", "Copy AUM < 5% AUM"),
}


def _value(metrics: dict[str, Any], field: str) -> Any:
    published = (metrics.get("published") or {}).get("90D", {})
    derived = metrics.get("derived") or {}
    if field == "mdd_90d":
        return published.get("mdd")
    if field == "total_orders_90d":
        return published.get("total_orders")
    if field == "sharpe_90d":
        return published.get("sharpe")
    if field == "copier_vs_lead":
        return {"copier_pnl": published.get("copier_pnl"), "pnl": published.get("pnl")}
    if field == "copy_aum_ratio":
        return derived.get("copy_aum_ratio")
    if field == "worst_position_roi":
        return derived.get("worst_position_roi")
    if field == "max_leverage":
        return derived.get("max_leverage")
    return metrics.get(field)


def _triggered(
    rule_id: str, field: str, severity: str, threshold: Any, op: str, value: Any
) -> bool | None:
    if op == "null":
        return value is None
    if field == "copier_vs_lead":
        if (
            not isinstance(value, dict)
            or value.get("copier_pnl") is None
            or value.get("pnl") is None
        ):
            return None
        return value["copier_pnl"] < 0 < value["pnl"]
    if value is None:
        return None
    value = float(value)
    if op == "gt":
        return value > float(threshold)
    if op == "lt":
        return value < float(threshold)
    if op == "le":
        return value <= float(threshold)
    return None


def evaluate_rules(metrics: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    unknown: list[str] = []
    for rule_id, (field, severity, threshold, op, label) in RULES.items():
        value = _value(metrics, field)
        result = _triggered(rule_id, field, severity, threshold, op, value)
        if result is None:
            unknown.append(rule_id)
            continue
        if not result:
            continue
        evidence = {"field": field, "value": value, "threshold": threshold, "rule": rule_id}
        if field == "copier_vs_lead":
            evidence = {"field": "copier_pnl/pnl", "value": value, "threshold": 0, "rule": rule_id}
        events.append(
            {"code": rule_id, "severity": severity, "label": label, "evidence": evidence}
        )
    return {"events": events, "unknown": unknown, "risk_level": risk_level(events, unknown)}


def risk_level(events: list[dict[str, Any]], unknown: list[str]) -> str:
    if not events:
        return "unknown" if unknown else "none"
    top = max(
        (event["severity"] for event in events),
        key=lambda item: SEVERITY_ORDER.get(item, 0),
    )
    return LEVEL_ALIAS.get(top, top)
