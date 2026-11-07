from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.collector import router as collector_router
from app.api.v1.traders import router as traders_router
from app.api.v1.universe import router as universe_router
from app.core.database import get_db

router = APIRouter()

router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(collector_router)
router.include_router(traders_router)
router.include_router(universe_router)


@router.get("/ping")
async def ping() -> dict[str, bool]:
    return {"pong": True}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"database": "ok"}
