"""Khóa collector: Redis là chính, fallback PostgreSQL advisory lock."""

import logging
import uuid
from typing import Any

from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 1800

_RELEASE_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
end
return 0
"""


class LockUnavailable(Exception):
    pass


class CollectorLock:
    """`async with CollectorLock('lock:collector:scan'):` — raise LockUnavailable nếu bận."""

    def __init__(self, key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.key = key
        self.ttl_seconds = ttl_seconds
        self.token = uuid.uuid4().hex
        self._redis: Any = None
        self._conn: Any = None
        self._pg_key: int | None = None

    async def __aenter__(self) -> "CollectorLock":
        await self.acquire()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.release()

    async def acquire(self) -> None:
        if await self._acquire_redis():
            return
        if await self._acquire_pg():
            return
        raise LockUnavailable(f"Không lấy được khóa {self.key}")

    async def _acquire_redis(self) -> bool:
        try:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(get_settings().redis_url)
            acquired = await self._redis.set(self.key, self.token, nx=True, ex=self.ttl_seconds)
            if acquired:
                return True
            raise LockUnavailable(f"Khóa {self.key} đang được giữ (Redis)")
        except LockUnavailable:
            raise
        except Exception as exc:  # Redis không sẵn sàng → fallback
            logger.warning("Redis không dùng được (%s), chuyển sang advisory lock", exc)
            self._redis = None
            return False

    async def _acquire_pg(self) -> bool:
        self._pg_key = abs(hash(self.key)) % (2**31 - 1)
        self._conn = await engine.connect()
        result = await self._conn.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": self._pg_key}
        )
        acquired = bool(result.scalar())
        if not acquired:
            await self._conn.close()
            self._conn = None
            raise LockUnavailable(f"Khóa {self.key} đang được giữ (Postgres)")
        return True

    async def release(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.eval(_RELEASE_LUA, 1, self.key, self.token)
                await self._redis.aclose()
            finally:
                self._redis = None
        if self._conn is not None:
            try:
                await self._conn.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": self._pg_key}
                )
                await self._conn.commit()
            finally:
                await self._conn.close()
                self._conn = None
