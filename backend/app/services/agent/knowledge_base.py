"""Knowledge base tất định cho câu hỏi khái niệm.

Dùng khi full-text index rỗng hoặc không khớp: trả lời ngay, không phụ thuộc LLM
và không phụ thuộc việc index đã chạy hay chưa.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Concept:
    id: str
    title: str
    keywords: tuple[str, ...]
    body: str
    ref: str


CONCEPTS: tuple[Concept, ...] = (
    Concept(
        id="tier",
        title="Nhóm trader A / B / C / Bị loại",
        keywords=(
            "nhóm a", "nhóm b", "nhóm c", "tier", "high_upper", "qualified_upper",
            "watch", "excluded", "bị loại", "phễu", "cao (a)", "đạt (b)", "theo dõi (c)",
        ),
        body=(
            "Hệ thống chia trader thành 4 nhóm theo phễu:\n"
            "- Cao (A, high_upper): hoạt động ≥ 180 ngày, ROI 90D ≥ 20%, WinRate ≥ 50%, "
            "MDD ≤ 20%, AUM ≥ 20.000 USDT, Sharpe ≥ 1.0 (nếu có), và tổng lệnh 90D ≥ 100.\n"
            "- Đạt (B, qualified_upper): hoạt động ≥ 90 ngày, ROI ≥ 10%, WinRate ≥ 45%, "
            "MDD ≤ 30%, AUM ≥ 10.000 USDT, Sharpe ≥ 0.5, tổng lệnh ≥ 50.\n"
            "- Theo dõi (C, watch): hoạt động ≥ 30 ngày, ROI > 0, PnL > 0, WinRate ≥ 40%, "
            "MDD ≤ 40%, AUM ≥ 5.000 USDT, tổng lệnh ≥ 20, còn slot, có giao dịch trong 7 ngày.\n"
            "- Bị loại (excluded): không đạt các điều kiện của nhóm C.\n"
            "Nhóm không phải điểm số cuối cùng; nó là bộ lọc thô trước khi chấm điểm. "
            "Trader có thể bị hạ nhóm nếu tổng lệnh 90D thấp hơn ngưỡng của nhóm (HF04)."
        ),
        ref="docs/ky-thuat/05-pheu-va-tier.md#tier",
    ),
    Concept(
        id="sharpe",
        title="Sharpe",
        keywords=("sharpe", "sharp ratio", "sharpRatio"),
        body=(
            "Sharpe là chỉ số do Binance công bố cho từng khung 7D/30D/90D/180D. "
            "Hệ thống giữ nguyên giá trị published, không tự tính lại. "
            "Sharpe null hiển thị N/A và bị tính là thiếu dữ liệu, không chấm 0. "
            "Sharpe âm bị Risk V2 veto: nâng mức rủi ro lên tối thiểu high và "
            "cấm vào bảng Low Risk."
        ),
        ref="docs/ky-thuat/06-bo-chi-so.md#sharpe",
    ),
    Concept(
        id="mdd",
        title="MDD (Maximum Drawdown)",
        keywords=("mdd", "drawdown", "sụt giảm", "maximum drawdown"),
        body=(
            "MDD là mức sụt giảm lớn nhất trong khung thời gian, lấy từ dữ liệu Binance công bố "
            "(published). Hệ thống không tự tính thay thế. MDD phụ thuộc khung: cùng một trader "
            "có thể MDD 3% ở 90D nhưng 8% ở 7D. Khi thiếu, giá trị là null kèm cờ missing_mdd, "
            "không đổi thành 0."
        ),
        ref="docs/ky-thuat/06-bo-chi-so.md#mdd",
    ),
    Concept(
        id="winrate",
        title="WinRate order và WinRate vị thế",
        keywords=("winrate", "win rate", "tỷ lệ thắng", "win_rate_order", "position_win_rate"),
        body=(
            "Có hai định nghĩa tách biệt:\n"
            "- WinRate order = winOrders / totalOrder trên dữ liệu hiệu suất Binance.\n"
            "- WinRate vị thế = tỷ lệ vị thế đóng có PnL dương, tính từ position-history.\n"
            "Hai số này không thay thế nhau; UI hiển thị riêng và không trộn."
        ),
        ref="docs/ky-thuat/06-bo-chi-so.md#winrate",
    ),
    Concept(
        id="risk_score",
        title="Điểm rủi ro và mức rủi ro",
        keywords=("risk_score", "điểm rủi ro", "risk level", "mức rủi ro", "veto"),
        body=(
            "Risk V2 tính risk_score 0–100 từ MDD (30%), đòn bẩy (20%), Sharpe (15%), "
            "tập trung (15%), chất lượng dữ liệu (10%), yếu tố copy (10%). "
            "Mức: 0–20 none, 21–40 low, 41–60 medium, 61–80 high, 81–100 critical. "
            "Veto nâng mức tối thiểu và cấm bảng Low Risk, ví dụ Sharpe âm → tối thiểu high. "
            "Thiếu dữ liệu thì mức là unknown, không đoán."
        ),
        ref="docs/ky-thuat/08-risk.md#risk-score",
    ),
    Concept(
        id="score_bands",
        title="Mức điểm (band)",
        keywords=("band", "mức điểm", "xếp loại điểm", "excellent", "high_risk"),
        body=(
            "Điểm tổng 0–100 chia mức: ≥ 85 excellent, ≥ 70 good, ≥ 55 average, "
            "≥ 40 weak, < 40 high_risk. Band chỉ mô tả chất lượng tổng hợp, "
            "không phải khuyến nghị đầu tư."
        ),
        ref="docs/ky-thuat/07-scoring.md#band",
    ),
    Concept(
        id="ranking",
        title="Ba bảng xếp hạng",
        keywords=("ranking", "bảng xếp hạng", "overall", "low_risk", "consistency"),
        body=(
            "Có 3 bảng: Overall (theo điểm tổng), Low Risk (hoạt động ≥ 90 ngày, MDD ≤ 20%, "
            "đòn bẩy ≤ 5x, độ tin cậy ≥ 0.8, Sharpe ≥ 0 kèm ngoại lệ), "
            "Consistency (theo điểm ổn định, hoạt động ≥ 90 ngày). "
            "Không có bảng High Return để tránh chạy theo ROI."
        ),
        ref="docs/ky-thuat/09-ranking.md#boards",
    ),
    Concept(
        id="copier",
        title="Copier PnL và Copy AUM",
        keywords=("copier", "copier pnl", "copy aum", "người sao chép", "số copier"),
        body=(
            "Copier PnL là tổng PnL của những người đang sao chép trader, do Binance công bố. "
            "Copy AUM là vốn của các copier. Hai chỉ số này khác PnL của lead. "
            "Copier PnL có thể âm dù ROI của lead dương vì người sao chép vào ở thời điểm khác, "
            "dùng đòn bẩy/khối lượng khác. Hệ thống không có dữ liệu từng copier."
        ),
        ref="docs/ky-thuat/02-copy-trading-binance.md#copier",
    ),
    Concept(
        id="window",
        title="Bốn khung thời gian 7D/30D/90D/180D",
        keywords=("khung", "7d", "30d", "90d", "180d", "cửa sổ", "window"),
        body=(
            "Mỗi chỉ số published có 4 khung: 7 ngày, 30 ngày, 90 ngày, 180 ngày. "
            "Cùng một trader có thể lãi ngắn hạn nhưng lỗ dài hạn, hoặc ngược lại. "
            "Khi so sánh phải nêu rõ khung; không trộn số giữa các khung."
        ),
        ref="docs/ky-thuat/04-du-lieu.md#windows",
    ),
    Concept(
        id="pre_score",
        title="pre_score và confidence",
        keywords=("pre_score", "confidence", "độ tin cậy", "prescore"),
        body=(
            "pre_score là điểm thô dùng để xếp thứ tự deep fetch, tính theo percentile trên "
            "toàn cohort universe (không phải điểm cuối). "
            "confidence 0–1 phản ánh độ đầy đủ của dữ liệu (4 thành phần: published, derived, "
            "freshness, continuity). confidence thấp không có nghĩa trader xấu, "
            "chỉ là thiếu dữ liệu."
        ),
        ref="docs/ky-thuat/04-du-lieu.md#confidence",
    ),
    Concept(
        id="profit_factor",
        title="Profit factor và phí",
        keywords=("profit factor", "hệ số lợi nhuận", "fee", "phí", "rebate", "fee drag"),
        body=(
            "Profit factor = tổng lãi / |tổng lỗ| từ position-history; null nếu mẫu < 5 vị thế, "
            "không chấm 0. Phí giao dịch có thể âm (rebate) và được giữ nguyên dấu; "
            "không cộng phí âm như chi phí dương."
        ),
        ref="docs/ky-thuat/06-bo-chi-so.md#profit-factor",
    ),
    Concept(
        id="freshness",
        title="Độ mới dữ liệu",
        keywords=("freshness", "độ mới", "dữ liệu cũ", "as_of", "cập nhật"),
        body=(
            "Mỗi bản ghi có mốc thu thập. Hệ thống coi dữ liệu quá 150 phút là cũ "
            "và phải cảnh báo. "
            "Số liệu published lấy từ lần thu thập gần nhất, không phải lúc tính lại. "
            "Khi dữ liệu cũ, câu trả lời phải nêu rõ mốc as_of thay vì trình bày "
            "như số hiện tại."
        ),
        ref="docs/ky-thuat/11-data-health-collector.md#freshness",
    ),
    Concept(
        id="leverage",
        title="Đòn bẩy",
        keywords=("đòn bẩy", "leverage", "margin", "ký quỹ"),
        body=(
            "max_leverage là đòn bẩy lớn nhất trong lịch sử vị thế; avg_leverage là trung bình. "
            "Đòn bẩy cao làm MDD tính bằng tiền tăng nhanh và dễ bị thanh lý. "
            "Risk V2 gắn cảnh báo khi đòn bẩy > 10x và veto ở mức cao hơn."
        ),
        ref="docs/ky-thuat/08-risk.md#leverage",
    ),
)


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def search_concepts(query: str, limit: int = 3) -> list[dict]:
    """Trả các concept khớp keyword, xếp theo số keyword khớp."""
    text = _normalize(query)
    if not text:
        return []
    scored: list[tuple[int, Concept]] = []
    for concept in CONCEPTS:
        hits = sum(1 for keyword in concept.keywords if keyword in text)
        for word in concept.title.lower().split():
            if len(word) > 2 and word in text:
                hits += 1
        if hits:
            scored.append((hits, concept))
    scored.sort(key=lambda item: (-item[0], item[1].id))
    return [
        {
            "path": concept.ref.split("#")[0],
            "line_start": None,
            "line_end": None,
            "heading": concept.title,
            "snippet": concept.body,
            "anchor": concept.ref,
        }
        for _score, concept in scored[:limit]
    ]
