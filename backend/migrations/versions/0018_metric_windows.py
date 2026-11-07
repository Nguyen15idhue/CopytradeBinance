"""Them cot chi so cho khung 7D/30D/180D (giu nguyen 90D).

Revision ID: 0018_metric_windows
Revises: 0017_knowledge_chunks
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_metric_windows"
down_revision: str | None = "0017_knowledge_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = [
    ("roi_7d", sa.Numeric(18, 8)),
    ("roi_30d", sa.Numeric(18, 8)),
    ("roi_180d", sa.Numeric(18, 8)),
    ("mdd_7d", sa.Numeric(18, 8)),
    ("mdd_30d", sa.Numeric(18, 8)),
    ("mdd_180d", sa.Numeric(18, 8)),
    ("sharpe_7d", sa.Numeric(18, 8)),
    ("sharpe_30d", sa.Numeric(18, 8)),
    ("sharpe_180d", sa.Numeric(18, 8)),
    ("copier_pnl_7d", sa.Numeric(24, 8)),
    ("copier_pnl_30d", sa.Numeric(24, 8)),
    ("copier_pnl_180d", sa.Numeric(24, 8)),
    ("win_rate_order_7d", sa.Numeric(9, 4)),
    ("win_rate_order_30d", sa.Numeric(9, 4)),
    ("win_rate_order_180d", sa.Numeric(9, 4)),
]

INDEXES = [
    ("ix_tm_roi_7d", "roi_7d"),
    ("ix_tm_roi_30d", "roi_30d"),
    ("ix_tm_roi_180d", "roi_180d"),
    ("ix_tm_profit_factor", "profit_factor"),
]


def upgrade() -> None:
    for name, column_type in COLUMNS:
        op.add_column("trader_metrics", sa.Column(name, column_type, nullable=True))
    for index_name, column_name in INDEXES:
        op.create_index(index_name, "trader_metrics", [column_name])
    op.execute(
        "CREATE INDEX ix_tm_current_copiers_desc "
        "ON trader_metrics (current_copiers DESC)"
    )
    op.execute(
        "CREATE INDEX ix_tm_copier_pnl_90d_desc "
        "ON trader_metrics (copier_pnl_90d DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tm_copier_pnl_90d_desc")
    op.execute("DROP INDEX IF EXISTS ix_tm_current_copiers_desc")
    for index_name, _column_name in reversed(INDEXES):
        op.drop_index(index_name, table_name="trader_metrics")
    for name, _column_type in reversed(COLUMNS):
        op.drop_column("trader_metrics", name)
