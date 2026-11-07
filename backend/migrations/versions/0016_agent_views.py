"""View agent_* cho sql_query read-only.

Revision ID: 0016_agent_views
Revises: 0015_agent_tables
Create Date: 2026-11-07
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0016_agent_views"
down_revision: str | None = "0015_agent_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OVERVIEW = """
CREATE VIEW agent_trader_overview AS
SELECT
    t.lead_portfolio_id,
    t.nickname,
    t.portfolio_type,
    t.status,
    u.potential_tier,
    u.pre_score,
    m.roi_90d,
    m.mdd_90d,
    m.sharpe_90d,
    m.win_rate_order_90d,
    m.runtime_days,
    m.max_leverage,
    m.current_copiers,
    m.copy_aum,
    m.aum,
    m.confidence AS metric_confidence,
    m.risk_level,
    m.risk_score,
    m.risk_veto,
    s.score,
    s.band,
    s.confidence AS score_confidence,
    s.rankable,
    s.config_version,
    m.computed_at AS as_of
FROM traders t
JOIN trader_universe u ON u.lead_portfolio_id = t.lead_portfolio_id
LEFT JOIN trader_metrics m ON m.lead_portfolio_id = t.lead_portfolio_id
LEFT JOIN scoring_config_versions v ON v.is_active
LEFT JOIN trader_scores s
    ON s.lead_portfolio_id = t.lead_portfolio_id
    AND s.config_version = v.version
"""

CONSTRAINTS = """
CREATE VIEW agent_trader_copy_constraints AS
SELECT DISTINCT ON (d.lead_portfolio_id)
    d.lead_portfolio_id,
    (d.raw ->> 'nickname') AS nickname,
    NULLIF(d.raw ->> 'fixedRadioMinCopyUsd', '')::numeric AS fixed_radio_min_copy_usd,
    NULLIF(d.raw ->> 'fixedAmountMinCopyUsd', '')::numeric AS fixed_amount_min_copy_usd,
    NULLIF(d.raw ->> 'profitSharingRate', '')::numeric AS profit_sharing_rate,
    NULLIF(d.raw ->> 'currentCopyCount', '')::integer AS current_copy_count,
    NULLIF(d.raw ->> 'maxCopyCount', '')::integer AS max_copy_count,
    NULLIF(d.raw ->> 'marginBalance', '')::numeric AS margin_balance,
    NULLIF(d.raw ->> 'aumAmount', '')::numeric AS aum_amount,
    NULLIF(d.raw ->> 'copyAum', '')::numeric AS copy_aum,
    d.collected_at AS as_of
FROM portfolio_snapshots d
WHERE d.source = 'detail'
ORDER BY d.lead_portfolio_id, d.collected_at DESC
"""

RISK_LATEST = """
CREATE VIEW agent_risk_latest AS
SELECT DISTINCT ON (e.lead_portfolio_id)
    e.lead_portfolio_id,
    e.code,
    e.severity,
    e.label,
    e.evidence,
    e.status,
    e.created_at AS as_of
FROM risk_events e
ORDER BY e.lead_portfolio_id, e.created_at DESC
"""

RANKING_LATEST = """
CREATE VIEW agent_ranking_latest AS
SELECT DISTINCT ON (r.board)
    r.board,
    r.config_version,
    r.collected_at AS as_of,
    r.items
FROM ranking_snapshots r
ORDER BY r.board, r.collected_at DESC
"""

PERF_WINDOWS = """
CREATE VIEW agent_performance_windows AS
SELECT
    m.lead_portfolio_id,
    NULLIF(m.metrics -> 'published' -> '7D' ->> 'roi', '')::numeric AS roi_7d,
    NULLIF(m.metrics -> 'published' -> '7D' ->> 'mdd', '')::numeric AS mdd_7d,
    NULLIF(m.metrics -> 'published' -> '30D' ->> 'roi', '')::numeric AS roi_30d,
    NULLIF(m.metrics -> 'published' -> '30D' ->> 'mdd', '')::numeric AS mdd_30d,
    NULLIF(m.metrics -> 'published' -> '90D' ->> 'roi', '')::numeric AS roi_90d,
    NULLIF(m.metrics -> 'published' -> '90D' ->> 'mdd', '')::numeric AS mdd_90d,
    NULLIF(m.metrics -> 'published' -> '90D' ->> 'sharpe', '')::numeric AS sharpe_90d,
    NULLIF(m.metrics -> 'published' -> '180D' ->> 'roi', '')::numeric AS roi_180d,
    NULLIF(m.metrics -> 'published' -> '180D' ->> 'mdd', '')::numeric AS mdd_180d,
    m.computed_at AS as_of
FROM trader_metrics m
"""

VIEWS = [
    "agent_trader_overview",
    "agent_trader_copy_constraints",
    "agent_risk_latest",
    "agent_ranking_latest",
    "agent_performance_windows",
]


def upgrade() -> None:
    op.execute(OVERVIEW)
    op.execute(CONSTRAINTS)
    op.execute(RISK_LATEST)
    op.execute(RANKING_LATEST)
    op.execute(PERF_WINDOWS)


def downgrade() -> None:
    for view in reversed(VIEWS):
        op.execute(f"DROP VIEW IF EXISTS {view}")
