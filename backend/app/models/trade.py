from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint("lead_portfolio_id", "trade_hash", name="uq_trades_lead_hash"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_portfolio_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traders.lead_portfolio_id", ondelete="CASCADE"), nullable=False
    )
    trade_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    symbol: Mapped[str | None] = mapped_column(String(32))
    side: Mapped[str | None] = mapped_column(String(16))
    price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    fee: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    fee_asset: Mapped[str | None] = mapped_column(String(16))
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    qty: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    realized_profit: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    position_side: Mapped[str | None] = mapped_column(String(16))
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
