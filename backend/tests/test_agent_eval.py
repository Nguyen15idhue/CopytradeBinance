"""Eval 50 câu: top10, $100, code, web, multi-turn, unknown, SQL attack, advice."""

import pytest

from app.services.agent.nl_search import parse_nl_filters
from app.services.agent.sql_tools import validate_sql
from app.services.agent.verifier import contains_advice, verify_answer

CASES: list[tuple[str, str, dict]] = [
    # top 10 an toàn (8)
    ("top10", "top 10 trader an toàn", {"risk_level": ["low", "none"]}),
    ("top10", "10 trader ít rủi ro lợi nhuận tốt",
     {"risk_level": ["low", "none"], "min_sharpe": 0.5}),
    ("top10", "trader low risk mdd dưới 15", {"max_mdd_90d": 15.0}),
    ("top10", "an toàn, sharpe từ 1", {"min_sharpe": 1.0}),
    ("top10", "rủi ro thấp, điểm từ 80", {"min_score": 80.0}),
    ("top10", "top trader an toàn còn slot", {"has_slot": True}),
    ("top10", "ít rủi ro, runtime tối thiểu 180", {"min_runtime_days": 180.0}),
    ("top10", "low_risk", {"risk_level": ["low", "none"]}),
    # vốn 100$ (8)
    ("fit", "trader X với vốn 100$", {"min_copy_usd_max": 100.0}),
    ("fit", "vốn tối thiểu dưới 50$", {"min_copy_usd_max": 50.0}),
    ("fit", "vốn 200$ còn slot", {"min_copy_usd_max": 200.0, "has_slot": True}),
    ("fit", "min copy không quá 10", {"min_copy_usd_max": 10.0}),
    ("fit", "tôi có 1000$, tìm trader an toàn",
     {"min_copy_usd_max": 1000.0, "risk_level": ["low", "none"]}),
    ("fit", "vốn nhỏ 20$ có copy được không", {"min_copy_usd_max": 20.0}),
    ("fit", "vốn tối đa 500$ đòn bẩy dưới 3", {"min_copy_usd_max": 500.0, "max_leverage": 3.0}),
    ("fit", "100 usd", {"min_copy_usd_max": 100.0}),
    # code/docs (6) — parser không bịa filter, trả default + assumption
    ("code", "hệ thống tính sharpe thế nào", {"safe_default": True}),
    ("code", "risk_score tính ra sao", {"safe_default": True}),
    ("code", "tier qualified là gì", {"safe_default": True}),
    ("code", "R18 nghĩa là gì", {"safe_default": True}),
    ("code", "API ranking trả gì", {"safe_default": True}),
    ("code", "collector chạy mấy giờ một lần", {"safe_default": True}),
    # web (4)
    ("web", "Binance copy trading là gì", {"safe_default": True}),
    ("web", "tin tức funding rate hôm nay", {"safe_default": True}),
    ("web", "hướng dẫn mở tài khoản Binance", {"safe_default": True}),
    ("web", "giá BTC hiện tại", {"safe_default": True}),
    # multi-turn (6) — id phải khớp row_ids
    ("multi", "so sánh 5143921081414022657 và 5296057151807357697",
     {"row_ids": ["5143921081414022657", "5296057151807357697"], "unknown": []}),
    ("multi", "phân tích trader 5143921081414022657 với vốn 100$",
     {"row_ids": ["5143921081414022657"], "unknown": []}),
    ("multi", "trader 5143921081414022658 có an toàn không",
     {"row_ids": ["5143921081414022657"], "unknown": ["5143921081414022658"]}),
    ("multi", "so sánh 2 trader đó", {"row_ids": [], "unknown": []}),
    ("multi", "mdd của 5143921081414022657 là bao nhiêu",
     {"row_ids": ["5143921081414022657"], "unknown": []}),
    ("multi", "trong 3 trader 5143921081414022657, 5296057151807357697,"
     " 3602559103560077057 thì ai tốt",
     {"row_ids": ["5143921081414022657", "5296057151807357697",
                  "3602559103560077057"], "unknown": []}),
    # unknown/mơ hồ (6)
    ("unknown", "abc xyz", {"safe_default": True}),
    ("unknown", "tìm trader ngon", {"safe_default": True}),
    ("unknown", "???", {"safe_default": True}),
    ("unknown", "cho tôi con số đẹp", {"safe_default": True}),
    ("unknown", "làm giàu nhanh", {"safe_default": True}),
    ("unknown", "", {"safe_default": True}),
    # SQL attack (6)
    ("sql", "SELECT * FROM traders; DELETE FROM traders", {"blocked": True}),
    ("sql", "DROP TABLE agent_sessions", {"blocked": True}),
    ("sql", "SeLeCT * FrOM users", {"blocked": True}),
    ("sql", "SELECT * FROM sessions", {"blocked": True}),
    ("sql", "SELECT * FROM portfolio_snapshots LIMIT 9999", {"blocked": True}),
    ("sql", "COPY traders TO '/tmp/x.csv'", {"blocked": True}),
    # advice (6)
    ("advice", "Bạn nên copy trader này ngay", {"advice": True}),
    ("advice", "có nên đầu tư 100$ không", {"advice": True}),
    ("advice", "khuyên tôi mua con này", {"advice": True}),
    ("advice", "chắc chắn có lãi", {"advice": True}),
    ("advice", "ROI 19.19% theo dữ liệu", {"advice": False}),
    ("advice", "mua ngay kẻo lỡ", {"advice": True}),
]


@pytest.mark.parametrize("category,text,expected", CASES)
def test_eval_50(category: str, text: str, expected: dict) -> None:
    if category in ("top10", "fit", "code", "web", "unknown"):
        result = parse_nl_filters(text)
        for key, value in expected.items():
            if key == "safe_default":
                assert result["filters"]["risk_level"] == ["low", "none"]
                assert result["assumptions"]
            else:
                assert result["filters"].get(key) == value, f"{text}: {key}"
        assert result["chips"]
    elif category == "multi":
        checked = verify_answer(text, [], row_ids=expected["row_ids"])
        assert checked["unknown_ids"] == expected["unknown"]
    elif category == "sql":
        _query, error = validate_sql(text)
        assert error is not None, text
    elif category == "advice":
        assert contains_advice(text) is expected["advice"], text
