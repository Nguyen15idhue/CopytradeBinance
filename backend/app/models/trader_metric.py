from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TraderMetric(Base):
    """Bản mới nhất của chỉ số quant cho từng trader (upsert theo lead)."""

    __tablename__ = "trader_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_portfolio_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("traders.lead_portfolio_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    roi_90d: Mapped[float | None] = mapped_column(Numeric(18, 8))
    mdd_90d: Mapped[float | None] = mapped_column(Numeric(18, 8))
    sharpe_90d: Mapped[float | None] = mapped_column(Numeric(18, 8))
    win_rate_order_90d: Mapped[float | None] = mapped_column(Numeric(9, 4))
    total_orders_90d: Mapped[int | None] = mapped_column(Integer)
    copier_pnl_90d: Mapped[float | None] = mapped_column(Numeric(24, 8))
    aum: Mapped[float | None] = mapped_column(Numeric(24, 8))
    copy_aum: Mapped[float | None] = mapped_column(Numeric(24, 8))
    current_copiers: Mapped[int | None] = mapped_column(Integer)
    runtime_days: Mapped[float | None] = mapped_column(Numeric(10, 2))
    max_leverage: Mapped[float | None] = mapped_column(Numeric(10, 4))
    avg_leverage: Mapped[float | None] = mapped_column(Numeric(10, 4))
    position_win_rate: Mapped[float | None] = mapped_column(Numeric(9, 4))
    profit_factor: Mapped[float | None] = mapped_column(Numeric(12, 4))
    fee_drag_pct: Mapped[float | None] = mapped_column(Numeric(12, 4))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    risk_level: Mapped[str | None] = mapped_column(String(24))
    low_sample: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
