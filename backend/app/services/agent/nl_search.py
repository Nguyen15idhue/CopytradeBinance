"""Parser NL → filter cho Screener (tất định, không gọi LLM)."""

import re
from typing import Any

SAFE_DEFAULT_FILTERS: dict[str, Any] = {
    "risk_level": ["low", "none"],
    "min_runtime_days": 90,
    "sort": [{"field": "score", "dir": "desc"}],
    "limit": 50,
}

NUMBER = r"(\d+(?:[.,]\d+)?)"


def _num(raw: str) -> float:
    return float(raw.replace(",", "."))


def parse_nl_filters(text: str) -> dict[str, Any]:
    """Trả {filters, chips, assumptions}. Không bịa điều kiện ngoài câu hỏi."""
    query = (text or "").lower()
    filters: dict[str, Any] = {}
    chips: list[str] = []
    assumptions: list[str] = []

    if re.search(r"an toàn|ít rủi ro|rủi ro thấp|low.?risk", query):
        filters["risk_level"] = ["low", "none"]
        filters["no_veto"] = True
        chips += ["Rủi ro: thấp", "Không veto"]
    if re.search(r"lợi nhuận tốt|roi cao|sharpe cao|lãi tốt", query):
        filters["min_sharpe"] = 0.5
        chips.append("Sharpe ≥ 0.5")
    if re.search(r"còn slot|còn chỗ|chưa đầy", query):
        filters["has_slot"] = True
        chips.append("Còn slot")
    mdd = re.search(r"mdd\s*(?:≤|<=|dưới|không quá|tối đa)?\s*" + NUMBER, query)
    if mdd:
        filters["max_mdd_90d"] = _num(mdd.group(1))
        chips.append(f"MDD ≤ {mdd.group(1)}%")
    sharpe = re.search(r"sharpe\s*(?:≥|>=|trên|từ)?\s*" + NUMBER, query)
    if sharpe:
        filters["min_sharpe"] = _num(sharpe.group(1))
        chips.append(f"Sharpe ≥ {sharpe.group(1)}")
    score = re.search(r"(?:score|điểm)\s*(?:≥|>=|trên|từ)?\s*" + NUMBER, query)
    if score:
        filters["min_score"] = _num(score.group(1))
        chips.append(f"Điểm ≥ {score.group(1)}")
    runtime = re.search(
        r"(?:runtime|ngày(?: hoạt động)?)\s*(?:≥|>=|trên|tối thiểu|từ)?\s*" + NUMBER,
        query,
    )
    if runtime:
        filters["min_runtime_days"] = _num(runtime.group(1))
        chips.append(f"Hoạt động ≥ {runtime.group(1)} ngày")
    capital = re.search(
        r"(?:vốn|vốn tối thiểu|min(?:imum)? copy)"
        r"\s*(?:≤|<=|dưới|không quá|tối đa)?\s*" + NUMBER + r"\s*\$?",
        query,
    )
    if capital is None:
        loose = re.search(r"(?:vốn|có|với)\s*[^\d$]{0,12}" + NUMBER + r"\s*\$", query)
        if loose:
            capital = loose
    if capital is None:
        bare_money = re.search(NUMBER + r"\s*(?:\$|usd|usdt)", query)
        if bare_money:
            capital = bare_money
    if capital:
        filters["min_copy_usd_max"] = _num(capital.group(1))
        chips.append(f"Vốn tối thiểu ≤ {capital.group(1)}$")
    leverage = re.search(
        r"(?:đòn bẩy|leverage)\s*(?:≤|<=|dưới|không quá|tối đa)?\s*" + NUMBER,
        query,
    )
    if leverage:
        filters["max_leverage"] = _num(leverage.group(1))
        chips.append(f"Đòn bẩy ≤ {leverage.group(1)}x")

    if not filters:
        filters.update({key: value for key, value in SAFE_DEFAULT_FILTERS.items()
                         if key != "limit"})
        chips += ["Rủi ro: thấp", "Hoạt động ≥ 90 ngày"]
        assumptions.append("Câu hỏi mơ hồ — dùng mặc định an toàn")
    filters.setdefault("sort", [{"field": "score", "dir": "desc"}])
    filters.setdefault("limit", 50)
    return {"filters": filters, "chips": chips, "assumptions": assumptions}
