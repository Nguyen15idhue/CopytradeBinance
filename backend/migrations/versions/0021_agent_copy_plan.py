"""Them copy_plan vao agent_messages (ke hoach 06, buoc 6.1.1).

Revision ID: 0021_agent_copy_plan
Revises: 0020_collector_jobs
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021_agent_copy_plan"
down_revision: str | None = "0020_collector_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_messages",
        sa.Column("copy_plan", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "agent_messages",
        sa.Column("copy_plan_version", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_messages", "copy_plan_version")
    op.drop_column("agent_messages", "copy_plan")
