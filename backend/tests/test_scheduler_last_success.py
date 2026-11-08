"""last_success phải bỏ qua log do test tạo."""

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.collection_log import CollectionLog
from app.worker.scheduler import load_last_success

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


@pytest.mark.asyncio
async def test_last_success_ignores_test_logs() -> None:
    now = datetime.now(UTC)
    async with SessionLocal() as db:
        before = (
            await db.execute(
                CollectionLog.__table__.select().with_only_columns(
                    CollectionLog.id
                ).order_by(CollectionLog.id.desc()).limit(1)
            )
        ).first()
        marker = before[0] if before else 0
        previous = await load_last_success(db)
        fake = CollectionLog(
            layer="L2", status="success", finished_at=now,
            detail={"test": True},
        )
        db.add(fake)
        await db.commit()
        try:
            current = await load_last_success(db)
            # Log test mới hơn hẳn nhưng không được đẩy last_success lên.
            assert current["perf"] == previous["perf"]
        finally:
            await db.execute(delete(CollectionLog).where(CollectionLog.id > marker))
            await db.commit()
