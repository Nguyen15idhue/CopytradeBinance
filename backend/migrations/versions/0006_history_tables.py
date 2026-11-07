"""Tạo bảng positions, trades, transfers.

Revision ID: 0006_history_tables
Revises: 0005_tier_history
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_history_tables"
down_revision: str | None = "0005_tier_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("position_id", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=True),
        sa.Column("side", sa.String(length=16), nullable=True),
        sa.Column("leverage", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("isolated", sa.String(length=32), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("avg_cost", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("avg_close_price", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("closing_pnl", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("max_open_interest", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("roi", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"], ["traders.lead_portfolio_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_portfolio_id", "position_id", name="uq_positions_lead_position"),
    )
    op.create_index("ix_positions_lead_closed", "positions", ["lead_portfolio_id", "closed_at"])

    op.create_table(
        "trades",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("trade_hash", sa.String(length=64), nullable=False),
        sa.Column("trade_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=True),
        sa.Column("side", sa.String(length=16), nullable=True),
        sa.Column("price", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("fee", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("fee_asset", sa.String(length=16), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("qty", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("realized_profit", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("position_side", sa.String(length=16), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"], ["traders.lead_portfolio_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_portfolio_id", "trade_hash", name="uq_trades_lead_hash"),
    )
    op.create_index("ix_trades_lead_time", "trades", ["lead_portfolio_id", "trade_time"])

    op.create_table(
        "transfers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("transfer_hash", sa.String(length=64), nullable=False),
        sa.Column("transfer_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("coin", sa.String(length=16), nullable=True),
        sa.Column("amount", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("from_account", sa.String(length=64), nullable=True),
        sa.Column("to_account", sa.String(length=64), nullable=True),
        sa.Column("trans_type", sa.String(length=32), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"], ["traders.lead_portfolio_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_portfolio_id", "transfer_hash", name="uq_transfers_lead_hash"),
    )
    op.create_index(
        "ix_transfers_lead_time", "transfers", ["lead_portfolio_id", "transfer_time"]
    )


def downgrade() -> None:
    op.drop_index("ix_transfers_lead_time", table_name="transfers")
    op.drop_table("transfers")
    op.drop_index("ix_trades_lead_time", table_name="trades")
    op.drop_table("trades")
    op.drop_index("ix_positions_lead_closed", table_name="positions")
    op.drop_table("positions")
