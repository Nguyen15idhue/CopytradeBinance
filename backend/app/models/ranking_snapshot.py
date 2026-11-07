from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RankingSnapshot(Base):
    __tablename__ = "ranking_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    board: Mapped[str] = mapped_column(String(24), nullable=False)
    config_version: Mapped[int] = mapped_column(Integer, nullable=False)
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
