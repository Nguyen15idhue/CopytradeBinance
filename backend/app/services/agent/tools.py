"""Tool registry cho agent. Tool DB đầy đủ ở B3, SQL ở B4, web ở B7."""

import time
from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_log import CollectionLog
from app.services.agent.schema import ToolResult, utcnow_iso

ToolHandler = Callable[[AsyncSession, dict[str, Any]], Awaitable[ToolResult]]

_REGISTRY: dict[str, dict[str, Any]] = {}


def register_tool(name: str, description: str, parameters: dict[str, Any]) -> Callable:
    def decorator(handler: ToolHandler) -> ToolHandler:
        _REGISTRY[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }
        return handler

    return decorator


def tool_specs() -> list[dict[str, Any]]:
    return [
        {"name": spec["name"], "description": spec["description"], "parameters": spec["parameters"]}
        for spec in _REGISTRY.values()
    ]


async def run_tool(db: AsyncSession, name: str, arguments: dict[str, Any]) -> ToolResult:
    spec = _REGISTRY.get(name)
    if spec is None:
        return ToolResult.fail(f"Tool không tồn tại: {name}")
    started = time.perf_counter()
    try:
        result = await spec["handler"](db, arguments or {})
        return result
    except Exception as exc:  # noqa: BLE001
        return ToolResult.fail(f"{name} lỗi: {exc}")
    finally:
        _ = round((time.perf_counter() - started) * 1000)


def _stub(tool_name: str) -> ToolHandler:
    async def handler(_db: AsyncSession, _args: dict[str, Any]) -> ToolResult:
        return ToolResult.fail(f"Tool {tool_name} chưa triển khai ở bước này")

    return handler


for _name in (
    "analyze_portfolio_fit",
    "sql_query",
    "search_knowledge",
    "web_search",
):
    register_tool(
        _name,
        f"Tool {_name} (triển khai ở bước sau).",
        {"type": "object", "properties": {}},
    )(_stub(_name))


async def check_agent_budget(db: AsyncSession, daily_usd: float, monthly_usd: float) -> None:
    """Ném AgentBudgetExceeded khi vượt budget ngày/tháng."""
    from app.core.errors import ApiError
    from app.models.ai_report import AIUsage

    today = date.today()
    day_total = (
        await db.execute(
            select(func.coalesce(func.sum(AIUsage.cost_usd), 0)).where(
                AIUsage.day == today, AIUsage.feature == "agent"
            )
        )
    ).scalar() or 0
    month_total = (
        await db.execute(
            select(func.coalesce(func.sum(AIUsage.cost_usd), 0)).where(
                AIUsage.feature == "agent",
                AIUsage.day >= today.replace(day=1),
            )
        )
    ).scalar() or 0
    if float(day_total) >= daily_usd:
        raise ApiError(429, "AGENT_BUDGET_EXCEEDED", "Đã vượt budget agent ngày")
    if float(month_total) >= monthly_usd:
        raise ApiError(429, "AGENT_BUDGET_EXCEEDED", "Đã vượt budget agent tháng")


async def record_agent_usage(
    db: AsyncSession,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    cost_usd: float,
) -> None:
    from app.models.ai_report import AIUsage

    db.add(
        AIUsage(
            day=date.today(),
            model=model or "unknown",
            prompt_tokens=prompt_tokens or 0,
            completion_tokens=completion_tokens or 0,
            cost_usd=cost_usd or 0,
            feature="agent",
        )
    )


@register_tool(
    "get_data_health",
    "Trạng thái collector: lần chạy gần nhất, freshness, lỗi.",
    {"type": "object", "properties": {}},
)
async def get_data_health(db: AsyncSession, _args: dict[str, Any]) -> ToolResult:
    rows = (
        await db.execute(
            select(CollectionLog).order_by(CollectionLog.started_at.desc()).limit(10)
        )
    ).scalars().all()
    latest = rows[0] if rows else None
    as_of = latest.started_at.isoformat() if latest and latest.started_at else None
    return ToolResult(
        data={
            "latest_run": as_of,
            "recent_runs": [
                {
                    "layer": row.layer,
                    "status": row.status,
                    "started_at": row.started_at.isoformat() if row.started_at else None,
                }
                for row in rows
            ],
        },
        meta={"source": "database", "as_of": as_of or utcnow_iso()},
    )
