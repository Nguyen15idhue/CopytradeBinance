import pytest

from app.services.compare import correlation_matrix


def _chart(step: float, days: int = 60, noise: float = 0.0) -> list[dict]:
    return [
        {
            "dateTime": 1_700_000_000_000 + index * 86_400_000,
            "value": step * (((index * 37) % 11) + index * 0.1) + (index % 2) * noise,
        }
        for index in range(days)
    ]


def test_correlation_identity_diagonal() -> None:
    result = correlation_matrix({"a": _chart(1.0), "b": _chart(2.0)})
    assert result["matrix"][0][0] == 1.0
    assert result["matrix"][1][1] == 1.0
    assert result["sample_days"] == 59


def test_correlation_identical_series_is_one() -> None:
    result = correlation_matrix({"a": _chart(1.0), "b": _chart(1.0)})
    assert result["matrix"][0][1] == pytest.approx(1.0)


def test_correlation_inverse_series_is_minus_one() -> None:
    up = _chart(1.0)
    down = [{"dateTime": point["dateTime"], "value": -point["value"]} for point in up]
    result = correlation_matrix({"a": up, "b": down})
    assert result["matrix"][0][1] == pytest.approx(-1.0)


def test_correlation_null_when_insufficient_days() -> None:
    result = correlation_matrix({"a": _chart(1.0, days=10), "b": _chart(1.0, days=10)})
    assert result["matrix"][0][1] is None
    assert "ước tính" in result["disclaimer"]


def test_correlation_handles_empty_chart() -> None:
    result = correlation_matrix({"a": [], "b": []})
    assert result["matrix"][0][1] is None
    assert result["sample_days"] == 0
