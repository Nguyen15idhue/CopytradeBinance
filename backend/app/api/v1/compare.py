from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.models.user import User
from app.services.compare import build_compare

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("")
async def compare(
    request: Request,
    ids: str = Query(description="Danh sách id, phân tách bằng dấu phẩy (2–4)"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    parsed = [item.strip() for item in ids.split(",") if item.strip()]
    if len(parsed) < 2 or len(parsed) > 4:
        raise ApiError(422, "INVALID_COMPARE", "Cần 2–4 trader để so sánh")
    result = await build_compare(db, parsed)
    return ok(result, request)
