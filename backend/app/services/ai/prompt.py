"""Prompt v2 + template fallback tất định, phân tích theo số liệu."""

import json
from typing import Any

from app.services.ai.schema import AIReportPayload

PROMPT_VERSION = "v2"

SYSTEM_PROMPT = (
    "Bạn là nhà phân tích dữ liệu copy-trading. Trả lời hoàn toàn bằng tiếng Việt, "
    "chỉ trả JSON hợp lệ, không markdown. Phân tích và đánh giá dựa trên số liệu: "
    "mỗi nhận định phải nêu chỉ số, giá trị và ý nghĩa hoặc ngưỡng so sánh. "
    "Không chỉ liệt kê điểm tích cực/tiêu cực. Không đưa lời khuyên đầu tư, "
    "không hứa hẹn lợi nhuận."
)

TIER_LABELS_VI = {
    "high_upper": "Cao (A)",
    "qualified_upper": "Đạt (B)",
    "watch": "Theo dõi (C)",
    "excluded": "Bị loại",
    "unknown": "Chưa rõ",
}

RISK_LABELS_VI = {
    "R01": "Runtime < 30 ngày",
    "R02": "MDD > 20%",
    "R03": "MDD > 30%",
    "R04": "Đòn bẩy tối đa > 10x",
    "R05": "Đòn bẩy tối đa > 20x",
    "R06": "ROI vị thế ≤ −80%",
    "R07": "Tổng số lệnh < 20",
    "R08": "Sharpe trống",
    "R09": "Dữ liệu cũ > 150 phút",
    "R10": "Copier PnL âm, lead dương",
    "R11": "Copy AUM < 5% AUM",
}

MISSING_LABELS_VI = {
    "missing_sharpe": "Sharpe",
    "missing_mdd": "MDD",
    "missing_benchmark": "benchmark",
    "no_copiers": "copier",
    "low_sample": "mẫu giao dịch",
    "insufficient_positions": "mẫu vị thế",
    "missing_trades": "lịch sử giao dịch",
    "derived_unavailable": "chỉ số derived",
}

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


def _text(value: Any, digits: int = 2, suffix: str = "") -> str:
    """Số kiểu Việt Nam (dấu phẩy thập phân), không bịa khi null."""
    if value is None:
        return "chưa có"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:.{digits}f}".replace(".", ",") + suffix


def build_prompt(context: dict[str, Any]) -> str:
    events = [
        {
            "code": event.get("code"),
            "label": RISK_LABELS_VI.get(
                str(event.get("code")), str(event.get("label") or "")
            ),
            "severity": event.get("severity"),
        }
        for event in context.get("risk_events") or []
    ]
    flags = [
        MISSING_LABELS_VI.get(str(flag), str(flag)) for flag in context.get("flags") or []
    ]
    payload = {
        "trader_id": context["id"],
        "tier": TIER_LABELS_VI.get(str(context.get("tier")), "Chưa rõ"),
        "confidence": context["confidence"],
        "published_90d": context["published"],
        "derived": context["derived"],
        "flags": flags,
        "risk_events": events,
        "allowed_evidence_ids": ALLOWED_EVIDENCE,
    }
    return (
        "Dữ liệu trader đã chuẩn hóa:\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Trả JSON đúng schema:\n"
        '{"summary": "3-4 câu", "strengths": ["..."], "weaknesses": ["..."], '
        '"risk_flags": ["..."], "missing_data": ["..."], "evidence_ids": ["..."]}\n\n'
        "Quy tắc bắt buộc:\n"
        "- Viết hoàn toàn bằng tiếng Việt.\n"
        "- summary 3-4 câu: đánh giá tổng quan, nêu ít nhất 2 chỉ số kèm giá trị, "
        "nêu mặt đánh đổi và giới hạn dữ liệu.\n"
        "- Mỗi mục strengths/weaknesses là một câu phân tích: chỉ số + giá trị + "
        "ý nghĩa hoặc ngưỡng so sánh. Không viết chung chung kiểu 'ROI cao' hoặc "
        "'MDD thấp'.\n"
        "- risk_flags bắt đầu bằng mã R..., mô tả hệ quả của rủi ro.\n"
        "- Chỉ dùng số liệu trong payload; không bịa số. Chỉ số null phải nêu trong "
        "missing_data.\n"
        "- evidence_ids phải nằm trong allowed_evidence_ids.\n"
        "- Không đưa lời khuyên đầu tư, không hứa hẹn lợi nhuận.\n\n"
        "Ví dụ cách viết đạt:\n"
        "- 'ROI 90D 20,00% cao hơn ngưỡng tham chiếu 10%, nhưng MDD 10,00% vẫn "
        "trong ngưỡng cảnh báo 20%'.\n"
        "- 'MDD 31,34% vượt ngưỡng nghiêm trọng 30%, hàm ý mức sụt giảm có thể "
        "lớn hơn khẩu vị rủi ro thông thường'.\n"
        "Không đạt:\n"
        "- 'ROI cao, MDD thấp, dữ liệu đủ'.\n"
    )


def template_report(context: dict[str, Any]) -> AIReportPayload:
    published = context.get("published") or {}
    derived = context.get("derived") or {}
    flags = context.get("flags") or []
    events = context.get("risk_events") or []
    confidence = float(context.get("confidence") or 0.0)
    roi = published.get("roi")
    mdd = published.get("mdd")
    leverage = derived.get("max_leverage")
    worst = derived.get("worst_position_roi")
    profit_factor = derived.get("profit_factor")

    missing = [MISSING_LABELS_VI.get(str(flag), str(flag)) for flag in flags]
    missing = [item for item in missing if item]
    tier = TIER_LABELS_VI.get(str(context.get("tier")), "Chưa rõ")

    strengths: list[str] = []
    if roi is not None and float(roi) > 0:
        strengths.append(
            f"ROI 90D {_text(roi, suffix='%')} cao hơn 0, cho thấy hiệu suất dương "
            "trong cửa sổ 90 ngày."
        )
    if profit_factor is not None and float(profit_factor) > 1:
        strengths.append(
            f"Profit Factor {_text(profit_factor)} > 1, lợi nhuận gộp lớn hơn lỗ gộp."
        )
    if confidence >= 0.8:
        strengths.append(
            f"Độ tin cậy {_text(confidence)} cho thấy phần lớn nhóm dữ liệu đã có mặt."
        )
    if not strengths:
        strengths.append(
            f"Độ tin cậy {_text(confidence)} là điểm tích cực duy nhất; chưa có chỉ số "
            "hiệu suất nổi bật."
        )

    weaknesses: list[str] = []
    if mdd is not None and float(mdd) > 30:
        weaknesses.append(
            f"MDD 90D {_text(mdd, suffix='%')} vượt ngưỡng nghiêm trọng 30%, hàm ý "
            "mức sụt giảm có thể lớn hơn khẩu vị rủi ro thông thường."
        )
    elif mdd is not None and float(mdd) > 20:
        weaknesses.append(
            f"MDD 90D {_text(mdd, suffix='%')} vượt ngưỡng cảnh báo 20%, cần đặt "
            "ưu tiên quản trị rủi ro lên trước lợi nhuận."
        )
    if leverage is not None and float(leverage) > 10:
        weaknesses.append(
            f"Đòn bẩy tối đa {_text(leverage, digits=1, suffix='x')} vượt ngưỡng 10x, "
            "làm tăng rủi ro thanh lý khi thị trường đảo chiều."
        )
    if worst is not None and float(worst) < -80:
        weaknesses.append(
            f"ROI vị thế xấu nhất {_text(worst, digits=1, suffix='%')} cho thấy một "
            "lệnh có thể lỗ rất sâu."
        )
    if roi is not None and float(roi) <= 0:
        weaknesses.append(
            f"ROI 90D {_text(roi, suffix='%')} không dương, hiệu suất chưa đủ để bù rủi ro."
        )
    if not weaknesses:
        weaknesses.append(
            f"Độ tin cậy {_text(confidence)} chưa đạt 1,0 nên kết luận vẫn còn khoảng "
            "trống dữ liệu."
        )

    risk_flags = [
        f"{event.get('code')}: "
        f"{RISK_LABELS_VI.get(str(event.get('code')), str(event.get('label') or ''))}"
        for event in events
    ][:5]
    if not risk_flags:
        risk_flags = ["Không có risk event kích hoạt."]

    evidence = ["id", "tier", "confidence", "roi_90d", "mdd_90d", "runtime_days"]
    evidence += [str(event.get("code")) for event in events][:5]

    if roi is not None and float(roi) > 0 and mdd is not None and float(mdd) > 20:
        tradeoff = (
            f"lợi nhuận dương nhưng MDD {_text(mdd, suffix='%')} vượt ngưỡng 20%, "
            "rủi ro sụt giảm lớn"
        )
    elif roi is not None and float(roi) <= 0:
        tradeoff = "hiệu suất không dương, ưu tiên bảo toàn vốn hơn theo đuổi lợi nhuận"
    else:
        tradeoff = "hiệu suất và mức sụt giảm cần được đọc cùng nhau, không tách rời"

    parts = [
        f"Trader {context.get('id')} thuộc nhóm {tier}, độ tin cậy {_text(confidence)}.",
        f"ROI 90D là {_text(roi, suffix='%')} và MDD 90D là {_text(mdd, suffix='%')}.",
        f"Đánh đổi chính: {tradeoff}.",
    ]
    if missing:
        parts.append(
            f"Dữ liệu còn thiếu {', '.join(missing[:3])}, nên kết luận chỉ mang tính tham khảo."
        )
    parts.append("Báo cáo được tạo bằng mẫu tất định khi AI không khả dụng.")

    return AIReportPayload(
        summary=" ".join(parts),
        strengths=strengths[:5],
        weaknesses=weaknesses[:5],
        risk_flags=risk_flags,
        missing_data=missing[:5] or ["không có dữ liệu thiếu được ghi nhận"],
        evidence_ids=evidence,
    )
