"""Prompt v1 + template fallback tất định."""

import json
from typing import Any

from app.services.ai.schema import AIReportPayload

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = (
    "Bạn là trợ lý phân tích dữ liệu copy-trading. Chỉ trả JSON hợp lệ, không markdown. "
    "Không đưa lời khuyên đầu tư, không hứa hẹn lợi nhuận."
)

ALLOWED_EVIDENCE = [
    "id",
    "tier",
    "confidence",
    "roi_90d",
    "mdd_90d",
    "sharpe",
    "win_rate_order",
    "total_orders",
    "max_leverage",
    "worst_position_roi",
    "profit_factor",
    "payoff_ratio",
    "copy_aum_ratio",
    "copier_pnl",
    "runtime_days",
    "freshness_minutes",
    "R01",
    "R02",
    "R03",
    "R04",
    "R05",
    "R06",
    "R07",
    "R08",
    "R09",
    "R10",
    "R11",
]


def build_prompt(context: dict[str, Any]) -> str:
    payload = {
        "trader_id": context["id"],
        "tier": context["tier"],
        "confidence": context["confidence"],
        "published_90d": context["published"],
        "derived": context["derived"],
        "flags": context["flags"],
        "risk_events": context["risk_events"],
        "allowed_evidence_ids": ALLOWED_EVIDENCE,
    }
    return (
        "Dữ liệu trader đã chuẩn hóa:\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Trả JSON đúng schema:\n"
        '{"summary": "3 câu", "strengths": ["..."], "weaknesses": ["..."], '
        '"risk_flags": ["..."], "missing_data": ["..."], "evidence_ids": ["..."]}\n'
        "Quy tắc:\n"
        "- Chỉ dùng số liệu ở trên; không suy đoán ngoài dữ liệu.\n"
        "- evidence_ids phải nằm trong allowed_evidence_ids.\n"
        "- Nêu chỉ số null trong missing_data.\n"
        "- Không đưa lời khuyên đầu tư.\n"
    )


def template_report(context: dict[str, Any]) -> AIReportPayload:
    published = context["published"] or {}
    derived = context["derived"] or {}
    flags = context["flags"] or []
    events = context["risk_events"] or []
    missing = [flag for flag in flags if flag.startswith("missing") or "insufficient" in flag]

    strengths: list[str] = []
    if published.get("roi") is not None and published["roi"] > 0:
        strengths.append(f"ROI 90D dương ({published['roi']:.2f}%)")
    if derived.get("profit_factor") and derived["profit_factor"] > 1:
        strengths.append(f"Profit factor > 1 ({derived['profit_factor']:.2f})")
    if context["confidence"] >= 0.8:
        strengths.append(f"Độ tin cậy dữ liệu cao ({context['confidence']:.2f})")
    if not strengths:
        strengths.append("Chưa có điểm mạnh nổi bật từ dữ liệu hiện tại")

    weaknesses: list[str] = []
    if published.get("mdd") is not None and published["mdd"] > 20:
        weaknesses.append(f"MDD cao ({published['mdd']:.2f}%)")
    if derived.get("max_leverage") and derived["max_leverage"] > 10:
        weaknesses.append(f"Leverage cao ({derived['max_leverage']:.1f}x)")
    if derived.get("worst_position_roi") is not None and derived["worst_position_roi"] < -80:
        weaknesses.append(f"Vị thế lỗ sâu ({derived['worst_position_roi']:.1f}%)")
    if not weaknesses:
        weaknesses.append("Không phát hiện điểm yếu nghiêm trọng trong dữ liệu hiện tại")

    risk_flags = [f"{event['code']}: {event['label']}" for event in events][:5]
    evidence = ["id", "tier", "confidence", "roi_90d", "mdd_90d", "runtime_days"]
    evidence += [event["code"] for event in events][:5]

    summary = (
        f"Trader {context['id']} thuộc tier {context['tier']}, độ tin cậy "
        f"{context['confidence']:.2f}. ROI 90D là {published.get('roi')}% và MDD 90D là "
        f"{published.get('mdd')}%. Báo cáo được tạo bằng template tất định khi AI không khả dụng."
    )
    return AIReportPayload(
        summary=summary,
        strengths=strengths[:5],
        weaknesses=weaknesses[:5],
        risk_flags=risk_flags,
        missing_data=missing[:5] or ["không có dữ liệu thiếu được ghi nhận"],
        evidence_ids=evidence,
    )
