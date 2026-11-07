from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# Dev/test dùng NullPool để tránh connection bị buộc vào event loop cũ.
_engine_options: dict = {"pool_pre_ping": True}
if settings.app_env != "production":
    _engine_options["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **_engine_options)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
