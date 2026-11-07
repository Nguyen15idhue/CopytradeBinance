from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TierHistory(Base):
    __tablename__ = "tier_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_portfolio_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traders.lead_portfolio_id", ondelete="CASCADE"), nullable=False
    )
    old_tier: Mapped[str | None] = mapped_column(String(16))
    new_tier: Mapped[str] = mapped_column(String(16), nullable=False)
    pre_score: Mapped[float | None] = mapped_column(Numeric(10, 4))
    reasons: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
