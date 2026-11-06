from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    __table_args__ = (
        UniqueConstraint(
            "lead_portfolio_id",
            "time_range",
            "collected_at",
            name="uq_performance_range_collected",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_portfolio_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traders.lead_portfolio_id", ondelete="CASCADE"), nullable=False
    )
    time_range: Mapped[str] = mapped_column(String(8), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    roi: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    mdd: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    copier_pnl: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(9, 4))
    win_orders: Mapped[int | None] = mapped_column(Integer)
    total_orders: Mapped[int | None] = mapped_column(Integer)
    sharpe: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
