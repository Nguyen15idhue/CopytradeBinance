"""Settings service — phần AI key (mở rộng đầy đủ ở bước 5.2/5.3)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings


async def get_ai_api_key(db: AsyncSession | None = None) -> str:
    """Env là nguồn chính; bước 5.3 thêm override mã hoá trong app_settings."""
    return get_settings().openrouter_api_key
