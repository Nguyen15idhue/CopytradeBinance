"""Tạo bảng risk_events và cột risk_level cho trader_metrics.

Revision ID: 0009_risk_events
Revises: 0008_trader_metrics
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_risk_events"
down_revision: str | None = "0008_trader_metrics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "trader_metrics",
        sa.Column("risk_level", sa.String(length=24), nullable=True),
    )
    op.create_table(
        "risk_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("severity", sa.String(length=24), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"], ["traders.lead_portfolio_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_portfolio_id", "code", name="uq_risk_lead_code"),
    )
    op.create_index("ix_risk_events_severity", "risk_events", ["severity", "status"])


def downgrade() -> None:
    op.drop_index("ix_risk_events_severity", table_name="risk_events")
    op.drop_table("risk_events")
    op.drop_column("trader_metrics", "risk_level")
