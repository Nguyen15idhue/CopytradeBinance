from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TraderUniverse(Base):
    __tablename__ = "trader_universe"

    lead_portfolio_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("traders.lead_portfolio_id", ondelete="CASCADE"),
        primary_key=True,
    )
    potential_tier: Mapped[str] = mapped_column(String(16), nullable=False)
    pre_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    filter_reasons: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    deep_fetch_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
