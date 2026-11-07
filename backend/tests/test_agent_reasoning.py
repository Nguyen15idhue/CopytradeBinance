"""Quy tắc reasoning dùng chung report/agent (không hardcode enabled:false)."""

from app.core.config import get_settings
from app.services.ai.openrouter import build_reasoning


def test_glm_requires_low() -> None:
    assert build_reasoning("glm-5.3-flash-chat") == {"effort": "low"}


def test_deepseek_and_others_disabled() -> None:
    assert build_reasoning("deepseek/deepseek-chat") == {"enabled": False}
    assert build_reasoning("nvidia/nemotron-3.5-super-vl:free") == {"enabled": False}


def test_explicit_effort_respected() -> None:
    settings = get_settings()
    original = settings.ai_reasoning_effort
    try:
        settings.ai_reasoning_effort = "high"
        assert build_reasoning("deepseek/x") == {"effort": "high"}
        settings.ai_reasoning_effort = "off"
        assert build_reasoning("glm-5.3-flash") == {"enabled": False}
    finally:
        settings.ai_reasoning_effort = original
