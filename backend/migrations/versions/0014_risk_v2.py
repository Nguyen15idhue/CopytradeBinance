"""Thêm risk_score + risk_veto cho trader_metrics (Risk V2).

Revision ID: 0014_risk_v2
Revises: 0013_audit_logs
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_risk_v2"
down_revision: str | None = "0013_audit_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "trader_metrics",
        sa.Column("risk_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "trader_metrics",
        sa.Column("risk_veto", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("trader_metrics", "risk_veto")
    op.drop_column("trader_metrics", "risk_score")
