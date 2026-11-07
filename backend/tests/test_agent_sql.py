import os

import pytest

from app.core.database import SessionLocal
from app.services.agent.sql_tools import validate_sql
from app.services.agent.tools import run_tool

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


def test_validate_select_ok_appends_limit() -> None:
    query, error = validate_sql("SELECT 1")
    assert error is None
    assert "LIMIT 200" in query


def test_validate_blocks_dml_ddl_multi() -> None:
    for bad in (
        "DELETE FROM traders",
        "DROP TABLE traders",
        "SELECT 1; SELECT 2",
        "INSERT INTO x VALUES (1)",
        "SELECT * FROM users",
        "SELECT * FROM app_settings",
        "SELECT * FROM traders LIMIT 501",
        "GRANT SELECT ON traders TO x",
    ):
        _query, error = validate_sql(bad)
        assert error is not None, bad


def test_validate_with_allowed() -> None:
    query, error = validate_sql("WITH a AS (SELECT 1 AS x) SELECT * FROM a")
    assert error is None
    assert query.lower().startswith("with")


def test_validate_allows_schema_introspection() -> None:
    query, error = validate_sql(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'traders'"
    )
    assert error is None, error
    query, error = validate_sql("SELECT tablename FROM pg_catalog.pg_tables")
    assert error is None, error


@pytest.mark.asyncio
async def test_sql_query_views_and_limits() -> None:
    async with SessionLocal() as db:
        ok_result = await run_tool(
            db, "sql_query",
            {"query": "SELECT lead_portfolio_id, score FROM agent_trader_overview LIMIT 5"},
        )
        assert ok_result.error is None
        assert ok_result.data["row_count"] <= 5

        views = await run_tool(
            db, "sql_query",
            {"query": "SELECT board, config_version FROM agent_ranking_latest"},
        )
        assert views.error is None

        blocked = await run_tool(db, "sql_query", {"query": "DELETE FROM traders"})
        assert blocked.error is not None
        assert blocked.data is None

        secret = await run_tool(db, "sql_query", {"query": "SELECT * FROM sessions"})
        assert secret.error is not None
