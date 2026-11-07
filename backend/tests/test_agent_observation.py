import json

from app.services.agent.orchestrator import compact_observation


def test_compact_observation_is_valid_json() -> None:
    payload = {"items": [{"id": "1", "roi": 4.8}], "total": 1}
    text = compact_observation(payload, 8000)
    assert json.loads(text) == payload
    assert " " not in text.split('"roi"')[0]


def test_compact_observation_truncates_structurally() -> None:
    payload = {
        "items": [{"id": str(index), "blob": "x" * 200} for index in range(50)],
        "total": 50,
        "config_version": 5,
    }
    text = compact_observation(payload, 1500)
    parsed = json.loads(text)
    assert parsed["truncated"] is True
    assert parsed["omitted_rows"] > 0
    assert parsed["total"] == 50
    assert parsed["config_version"] == 5
    assert len(parsed["items"]) < 50
    # Không cắt giữa object: phần tử cuối vẫn parse được và có đủ field.
    assert set(parsed["items"][-1]) == {"id", "blob"}
    assert len(text) < 2000


def test_compact_observation_non_list_payload_keeps_preview() -> None:
    text = compact_observation({"weird": "y" * 3000}, 500)
    parsed = json.loads(text)
    assert parsed["truncated"] is True
    assert "preview" in parsed
