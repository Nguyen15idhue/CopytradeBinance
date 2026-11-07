from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.models.ai_report import AIReport
from app.models.user import User
from app.services.ai.service import analyze_trader, list_reports
from app.services.settings_service import get_ai_api_key

router = APIRouter(prefix="/ai", tags=["ai"])


def _serialize(report: AIReport) -> dict:
    return {
        "id": report.id,
        "trader_id": report.lead_portfolio_id,
        "model_role": report.model_role,
        "model_used": report.model_used,
        "prompt_version": report.prompt_version,
        "summary": report.summary,
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "risk_flags": report.risk_flags,
        "missing_data": report.missing_data,
        "evidence_ids": report.evidence_ids,
        "prompt_tokens": report.prompt_tokens,
        "completion_tokens": report.completion_tokens,
        "cost_usd": float(report.cost_usd or 0),
        "latency_ms": report.latency_ms,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
    }


@router.post("/analyze/{portfolio_id}")
async def analyze(
    portfolio_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    report, cached, errors = await analyze_trader(db, portfolio_id)
    api_key = await get_ai_api_key(db)
    return ok(
        {
            "report": _serialize(report),
            "cached": cached,
            "errors": errors[:3],
            "ai_configured": bool(api_key),
        },
        request,
    )


@router.get("/reports/{portfolio_id}")
async def reports(
    portfolio_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    rows = await list_reports(db, portfolio_id)
    return ok({"items": [_serialize(row) for row in rows], "total": len(rows)}, request)


@router.get("/reports/{portfolio_id}/{report_id}")
async def report_detail(
    portfolio_id: str,
    report_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = await db.get(AIReport, report_id)
    if row is None or row.lead_portfolio_id != portfolio_id:
        raise ApiError(404, "AI_REPORT_NOT_FOUND", "Không tìm thấy AI report")
    return ok(_serialize(row), request)
