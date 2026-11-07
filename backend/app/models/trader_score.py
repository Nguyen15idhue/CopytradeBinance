from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TraderScore(Base):
    __tablename__ = "trader_scores"
    __table_args__ = (
        UniqueConstraint("lead_portfolio_id", "config_version", name="uq_scores_lead_config"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_portfolio_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traders.lead_portfolio_id", ondelete="CASCADE"), nullable=False
    )
    config_version: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    band: Mapped[str | None] = mapped_column(String(16))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    rankable: Mapped[bool] = mapped_column(nullable=False, default=False)
    hard_flags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
