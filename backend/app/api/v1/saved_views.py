from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.models.saved_view import SavedView
from app.models.user import User

router = APIRouter(prefix="/saved-views", tags=["saved-views"])


class SavedViewRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    filters: dict


@router.get("")
async def list_views(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    rows = (
        await db.execute(
            select(SavedView)
            .where(SavedView.user_id == user.id)
            .order_by(SavedView.created_at.desc())
        )
    ).scalars().all()
    return ok(
        [
            {
                "id": str(row.id),
                "name": row.name,
                "filters": row.filters,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
        request,
    )


@router.post("")
async def create_view(
    request: Request,
    body: SavedViewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    existing = (
        await db.execute(
            select(SavedView).where(SavedView.user_id == user.id, SavedView.name == body.name)
        )
    ).scalars().first()
    if existing is not None:
        existing.filters = body.filters
        row = existing
    else:
        row = SavedView(user_id=user.id, name=body.name, filters=body.filters)
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return ok(
        {"id": str(row.id), "name": row.name, "filters": row.filters}, request
    )


@router.delete("/{view_id}")
async def delete_view(
    view_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        delete(SavedView).where(SavedView.id == view_id, SavedView.user_id == user.id)
    )
    await db.commit()
    if result.rowcount == 0:
        raise ApiError(404, "SAVED_VIEW_NOT_FOUND", "Không tìm thấy saved view")
    return ok({"deleted": True}, request)
