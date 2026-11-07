"""Xóa session agent quá hạn retention (mặc định 90 ngày)."""

import argparse
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.agent import AgentSession


async def cleanup_agent_sessions(retention_days: int | None = None) -> dict:
    days = retention_days if retention_days is not None else get_settings().agent_retention_days
    cutoff = datetime.now().astimezone() - timedelta(days=days)
    async with SessionLocal() as db:
        old_ids = (
            await db.execute(
                select(AgentSession.id).where(AgentSession.created_at < cutoff)
            )
        ).scalars().all()
        if old_ids:
            await db.execute(delete(AgentSession).where(AgentSession.id.in_(old_ids)))
            await db.commit()
        return {"deleted_sessions": len(old_ids), "retention_days": days}


def main() -> int:
    parser = argparse.ArgumentParser(description="Xóa session agent quá hạn")
    parser.add_argument("--days", type=int, default=None)
    args = parser.parse_args()
    print(asyncio.run(cleanup_agent_sessions(args.days)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
