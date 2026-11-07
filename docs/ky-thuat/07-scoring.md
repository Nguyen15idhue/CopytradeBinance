---
id: scoring
title: "Scoring"
group: "Phân tích"
order: 7
keywords: "scoring, trọng số, percentile, winsor, band, hard filter, breakdown, config version"
---

# Scoring

## 1. Nguyên tắc

- Score là điểm tổng hợp tương đối theo cohort và cấu hình.
- Không phải khuyến nghị đầu tư.
- Không dùng score để che dữ liệu thiếu.
- AI không được sửa score/ranking.

## 2. Bảy nhóm và 19 component

| Nhóm | Component |
|---|---|
| Quản trị rủi ro | MDD, Calmar, max leverage, worst position ROI |
| Độ ổn định | Positive days, ROI stability |
| Khả năng sinh lời | ROI 90D, excess return, PnL scale |
| Chất lượng giao dịch | Profit factor, payoff, WinRate order |
| Hiệu quả copy | Copier PnL, copy AUM ratio, copiers |
| Hiệu quả vốn | PnL/AUM, AUM |
| Độ tin cậy dữ liệu | Confidence, sample size |

## 3. Trọng số

Trọng số nhóm mặc định (có thể đổi trong Settings):

- Quản trị rủi ro: 20
- Độ ổn định: 20
- Khả năng sinh lời: 20
- Chất lượng giao dịch: 15
- Hiệu quả copy: 10
- Độ tin cậy dữ liệu: 10
- Hiệu quả vốn: 5

## 4. Chuẩn hoá

- Percentile rank trong cohort.
- Winsorization để giảm outlier.
- Missing component không bị coi là 0; bị loại khỏi trọng số hoặc ghi missing.
- Score cuối = weighted average của các nhóm có mặt.

## 5. Hard filters

| Mã | Điều kiện |
|---|---|
| HF01 | Status khác ACTIVE |
| HF02 | Tier excluded |
| HF03 | Runtime < 30 ngày |
| HF04 | Không đủ tổng số lệnh theo tier |
| HF05 | Dữ liệu cũ > 150 phút |
| HF06 | Confidence < 0.5 |

Hard filter không sửa score; nó quyết định trader có được xếp hạng hay không.

## 6. Band

| Điểm | Band |
|---:|---|
| ≥ 85 | Xuất sắc |
| ≥ 70 | Tốt |
| ≥ 55 | Trung bình |
| ≥ 40 | Yếu |
| < 40 | Rủi ro cao |

## 7. Config version

- Mỗi lần đổi trọng số tạo version mới.
- Score cũ giữ nguyên; version active được rebuild.
- Rollback cũng rebuild score.
- Ranking đọc `config_version` để tránh trộn version.

## 8. Nguồn

`backend/app/services/scoring.py`, `backend/app/services/scoring_service.py`,
`docs/kehoach/03-bo-chi-so-va-scoring.md`.
