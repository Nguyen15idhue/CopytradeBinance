from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.response import ok
from app.core.database import get_db
from app.models.risk_event import RiskEvent
from app.models.trader import Trader
from app.models.user import User

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/summary")
async def summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    rows = (
        await db.execute(
            select(RiskEvent.severity, func.count()).group_by(RiskEvent.severity)
        )
    ).all()
    by_severity = {severity: count for severity, count in rows}
    total = sum(by_severity.values())
    return ok({"total": total, "by_severity": by_severity}, request)


@router.get("/events")
async def events(
    request: Request,
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    trader: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    statement = select(RiskEvent, Trader.nickname).outerjoin(
        Trader, Trader.lead_portfolio_id == RiskEvent.lead_portfolio_id
    )
    if severity:
        statement = statement.where(RiskEvent.severity == severity)
    if status:
        statement = statement.where(RiskEvent.status == status)
    if trader:
        statement = statement.where(RiskEvent.lead_portfolio_id == trader)

    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(RiskEvent.severity, RiskEvent.code)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return ok(
        {
            "items": [
                {
                    "trader_id": event.lead_portfolio_id,
                    "nickname": nickname,
                    "code": event.code,
                    "severity": event.severity,
                    "label": event.label,
                    "evidence": event.evidence,
                    "status": event.status,
                    "created_at": event.created_at.isoformat(),
                }
                for event, nickname in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        },
        request,
    )
