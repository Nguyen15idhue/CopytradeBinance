from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.api.response import ok
from app.core.database import get_db
from app.models.ranking_snapshot import RankingSnapshot
from app.models.user import User
from app.services.ranking import build_rankings

router = APIRouter(prefix="/ranking", tags=["ranking"])

Board = Literal["overall", "low_risk", "consistency"]


@router.get("")
async def read_ranking(
    request: Request,
    board: Board = Query(default="overall"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = (
        await db.execute(
            select(RankingSnapshot)
            .where(RankingSnapshot.board == board)
            .order_by(RankingSnapshot.collected_at.desc())
            .limit(1)
        )
    ).scalars().first()
    items = row.items if row else []
    ranked = [{"rank": index + 1, **item} for index, item in enumerate(items)]
    return ok(
        {
            "board": board,
            "config_version": row.config_version if row else None,
            "collected_at": row.collected_at.isoformat() if row else None,
            "items": ranked,
            "total": len(ranked),
        },
        request,
    )


@router.post("/run")
async def run_ranking(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    summary = await build_rankings(db)
    response.status_code = 200
    return ok(summary, request)
