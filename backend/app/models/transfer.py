from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Transfer(Base):
    __tablename__ = "transfers"
    __table_args__ = (
        UniqueConstraint("lead_portfolio_id", "transfer_hash", name="uq_transfers_lead_hash"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_portfolio_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traders.lead_portfolio_id", ondelete="CASCADE"), nullable=False
    )
    transfer_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    transfer_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    coin: Mapped[str | None] = mapped_column(String(16))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    from_account: Mapped[str | None] = mapped_column(String(64))
    to_account: Mapped[str | None] = mapped_column(String(64))
    trans_type: Mapped[str | None] = mapped_column(String(32))
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
