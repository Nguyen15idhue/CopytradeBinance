"""Tạo bảng trader_metrics.

Revision ID: 0008_trader_metrics
Revises: 0007_ops_tables
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_trader_metrics"
down_revision: str | None = "0007_ops_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trader_metrics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("roi_90d", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("mdd_90d", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("sharpe_90d", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("win_rate_order_90d", sa.Numeric(precision=9, scale=4), nullable=True),
        sa.Column("total_orders_90d", sa.Integer(), nullable=True),
        sa.Column("copier_pnl_90d", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("aum", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("copy_aum", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("current_copiers", sa.Integer(), nullable=True),
        sa.Column("runtime_days", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("max_leverage", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("avg_leverage", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("position_win_rate", sa.Numeric(precision=9, scale=4), nullable=True),
        sa.Column("profit_factor", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("fee_drag_pct", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("low_sample", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"], ["traders.lead_portfolio_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_portfolio_id", name="uq_trader_metrics_lead"),
    )
    op.create_index("ix_trader_metrics_score", "trader_metrics", ["roi_90d", "mdd_90d"])


def downgrade() -> None:
    op.drop_index("ix_trader_metrics_score", table_name="trader_metrics")
    op.drop_table("trader_metrics")
