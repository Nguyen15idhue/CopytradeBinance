"""Đọc/ghi app_settings và kill switch."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.app_setting import AppSetting

KILL_SWITCH_KEY = "collector.enabled"


async def get_setting(db: AsyncSession, key: str) -> Any:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = result.scalar_one_or_none()
    return None if row is None else row.value.get("value")


async def set_setting(db: AsyncSession, key: str, value: Any) -> AppSetting:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        row = AppSetting(key=key, value={"value": value}, version=1)
        db.add(row)
    else:
        row.value = {"value": value}
        row.version += 1
    await db.commit()
    return row


async def collector_enabled(db: AsyncSession) -> bool:
    """Env kill switch thắng; nếu không có thì đọc DB, mặc định bật."""
    if get_settings().collector_kill_switch:
        return False
    value = await get_setting(db, KILL_SWITCH_KEY)
    return True if value is None else bool(value)
