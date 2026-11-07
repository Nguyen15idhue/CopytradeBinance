"""Điều phối AI report: context, budget, cooldown, lưu DB."""

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models.ai_report import AIReport, AIUsage
from app.models.risk_event import RiskEvent
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.universe import TraderUniverse
from app.services.ai.openrouter import generate_report
from app.services.ai.prompt import ALLOWED_EVIDENCE, PROMPT_VERSION


async def build_context(db: AsyncSession, portfolio_id: str) -> dict[str, Any]:
    trader = await db.get(Trader, portfolio_id)
    if trader is None:
        raise ApiError(404, "TRADER_NOT_FOUND", "Không tìm thấy trader")
    metric = (
        await db.execute(
            select(TraderMetric).where(TraderMetric.lead_portfolio_id == portfolio_id)
        )
    ).scalars().first()
    if metric is None:
        raise ApiError(409, "NO_METRICS", "Trader chưa có metrics; chạy quant trước")
    universe = await db.get(TraderUniverse, portfolio_id)
    events = (
        await db.execute(
            select(RiskEvent)
            .where(RiskEvent.lead_portfolio_id == portfolio_id)
            .order_by(RiskEvent.severity)
        )
    ).scalars().all()
    metrics = metric.metrics or {}
    published = (metrics.get("published") or {}).get("90D", {})
    derived = metrics.get("derived") or {}
    context = {
        "id": portfolio_id,
        "tier": universe.potential_tier if universe else "unknown",
        "confidence": float(metric.confidence or 0),
        "published": published,
        "derived": {
            key: derived.get(key)
            for key in (
                "max_leverage",
                "worst_position_roi",
                "profit_factor",
                "payoff_ratio",
                "copy_aum_ratio",
                "position_win_rate",
            )
        },
        "flags": (metrics.get("flags") or []),
        "risk_events": [{"code": event.code, "label": event.label} for event in events],
        "runtime_days": metrics.get("runtime_days"),
        "freshness_minutes": metrics.get("freshness_minutes"),
        "allowed_evidence_ids": ALLOWED_EVIDENCE,
    }
    return context


def input_hash(context: dict[str, Any]) -> str:
    payload = {
        "id": context["id"],
        "tier": context["tier"],
        "confidence": context["confidence"],
        "published": context["published"],
        "derived": context["derived"],
        "flags": context["flags"],
        "risk_events": context["risk_events"],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()


async def check_budget(db: AsyncSession) -> None:
    settings = get_settings()
    today = datetime.now(UTC).date()
    month_start = today.replace(day=1)
    month_cost = await db.scalar(
        select(func.coalesce(func.sum(AIUsage.cost_usd), 0)).where(AIUsage.day >= month_start)
    )
    day_cost = await db.scalar(
        select(func.coalesce(func.sum(AIUsage.cost_usd), 0)).where(AIUsage.day == today)
    )
    if float(month_cost or 0) >= settings.ai_monthly_budget_usd:
        raise ApiError(429, "AI_BUDGET_EXCEEDED", "Đã vượt budget AI tháng")
    if float(day_cost or 0) >= settings.ai_daily_budget_usd:
        raise ApiError(429, "AI_BUDGET_EXCEEDED", "Đã vượt budget AI ngày")


async def latest_report(db: AsyncSession, portfolio_id: str) -> AIReport | None:
    return (
        await db.execute(
            select(AIReport)
            .where(AIReport.lead_portfolio_id == portfolio_id)
            .order_by(AIReport.created_at.desc())
            .limit(1)
        )
    ).scalars().first()


async def analyze_trader(db: AsyncSession, portfolio_id: str) -> tuple[AIReport, bool, list[str]]:
    settings = get_settings()
    if not settings.ai_enabled:
        raise ApiError(409, "AI_DISABLED", "AI đang bị tắt")

    context = await build_context(db, portfolio_id)
    digest = input_hash(context)
    latest = await latest_report(db, portfolio_id)
    now = datetime.now(UTC)
    if latest is not None:
        age = now - latest.created_at
        if age < timedelta(hours=settings.ai_cooldown_hours) and latest.input_hash == digest:
            return latest, True, []
        if age < timedelta(hours=settings.ai_cooldown_hours):
            return latest, True, ["cooldown"]

    await check_budget(db)

    from app.services.settings_service import get_ai_api_key

    api_key = await get_ai_api_key(db)
    result, errors = await generate_report(context, api_key)

    report = AIReport(
        lead_portfolio_id=portfolio_id,
        model_role=result.role,
        model_used=result.model,
        prompt_version=PROMPT_VERSION,
        input_hash=digest,
        summary=result.payload.summary,
        strengths=result.payload.strengths,
        weaknesses=result.payload.weaknesses,
        risk_flags=result.payload.risk_flags,
        missing_data=result.payload.missing_data,
        evidence_ids=result.payload.evidence_ids,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        cost_usd=result.cost_usd,
        latency_ms=result.latency_ms,
        status="success" if result.role != "template" else "template",
    )
    db.add(report)
    if result.role != "template":
        db.add(
            AIUsage(
                day=date.today(),
                model=result.model,
                prompt_tokens=result.prompt_tokens or 0,
                completion_tokens=result.completion_tokens or 0,
                cost_usd=result.cost_usd,
            )
        )
    await db.commit()
    await db.refresh(report)
    return report, False, errors


async def list_reports(db: AsyncSession, portfolio_id: str, limit: int = 20) -> list[AIReport]:
    return (
        await db.execute(
            select(AIReport)
            .where(AIReport.lead_portfolio_id == portfolio_id)
            .order_by(AIReport.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
