from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("lead_portfolio_id", "position_id", name="uq_positions_lead_position"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_portfolio_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traders.lead_portfolio_id", ondelete="CASCADE"), nullable=False
    )
    position_id: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(32))
    side: Mapped[str | None] = mapped_column(String(16))
    leverage: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    isolated: Mapped[str | None] = mapped_column(String(32))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    avg_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    avg_close_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    closing_pnl: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    max_open_interest: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    roi: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    status: Mapped[str | None] = mapped_column(String(32))
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
