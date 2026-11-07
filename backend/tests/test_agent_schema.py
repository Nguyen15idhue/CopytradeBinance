from app.models import AgentCitation, AgentFeedback, AgentMessage, AgentSession, AgentToolCall, Base


def test_agent_tables_registered() -> None:
    assert {
        "agent_sessions",
        "agent_messages",
        "agent_tool_calls",
        "agent_citations",
        "agent_feedback",
    } <= set(Base.metadata.tables)


def test_agent_message_columns_no_secret() -> None:
    cols = set(Base.metadata.tables["agent_messages"].columns)
    assert not ({"token", "password_hash", "secret"} & cols)


def test_agent_tool_call_indexes() -> None:
    table = Base.metadata.tables["agent_tool_calls"]
    idx_cols = [tuple(i.columns.keys()) for i in table.indexes]
    assert ("message_id",) in idx_cols
    assert ("session_id", "created_at") in idx_cols


def test_agent_models_importable() -> None:
    assert AgentSession.__tablename__ == "agent_sessions"
    assert AgentMessage.__tablename__ == "agent_messages"
    assert AgentToolCall.__tablename__ == "agent_tool_calls"
    assert AgentCitation.__tablename__ == "agent_citations"
    assert AgentFeedback.__tablename__ == "agent_feedback"
