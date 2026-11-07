---
id: tier
title: "Phễu sàng lọc và Tier"
group: "Phân tích"
order: 5
keywords: "tier, high_upper, qualified_upper, watch, excluded, totalOrder, pre-score, upper bound"
---

# Phễu sàng lọc và Tier

## 1. Tier là gì?

Tier là **nhóm tiềm năng ở tầng danh sách**, dùng để quyết định trader nào được lấy dữ liệu sâu
và chấm điểm. Tier không phải score cuối cùng và không phải khuyến nghị đầu tư.

| Mã backend | UI | Ý nghĩa |
|---|---|---|
| `excluded` | Bị loại | Không đạt điều kiện tối thiểu |
| `watch` | Theo dõi (C) | Đạt điều kiện tối thiểu |
| `qualified_upper` | Đạt (B) | Đạt ngưỡng B ở tầng list |
| `high_upper` | Cao (A) | Đạt ngưỡng A ở tầng list |

## 2. Điều kiện

### Bị loại

Bị loại nếu có ít nhất một điều kiện:

- Không giao dịch 7 ngày.
- Runtime < 30 ngày.
- ROI ≤ 0.
- PnL ≤ 0.
- WinRate < 40%.
- MDD > 40%.
- AUM < 5.000.
- Hết slot copy.

### Theo dõi (C)

- Runtime ≥ 30 ngày.
- ROI > 0.
- PnL > 0.
- WinRate ≥ 40%.
- MDD ≤ 40%.
- AUM ≥ 5.000.
- Còn slot copy.
- Có giao dịch 7 ngày.

### Đạt (B)

- Runtime ≥ 90 ngày.
- ROI ≥ 10%.
- WinRate ≥ 45%.
- MDD ≤ 30%.
- AUM ≥ 10.000.
- Sharpe ≥ 0,5 hoặc null.
- Tổng số lệnh ≥ 50.

### Cao (A)

- Runtime ≥ 180 ngày.
- ROI ≥ 20%.
- WinRate ≥ 50%.
- MDD ≤ 20%.
- AUM ≥ 20.000.
- Sharpe ≥ 1.
- Tổng số lệnh ≥ 100.

## 3. Upper bound và hạ tier

A/B ban đầu là upper bound. Sau đó hạ theo tổng số lệnh:

- A → B nếu `totalOrder < 100`.
- B → C nếu `totalOrder < 50`.
- C và Bị loại giữ nguyên.

## 4. Pre-score

`pre_score` chỉ dùng để xếp thứ tự deep fetch, không hiển thị như điểm chất lượng:

```text
pre_score = 0.30 × norm(roi)
          + 0.30 × norm(−mdd)
          + 0.20 × norm(sharpe)
          + 0.10 × norm(winRate)
          + 0.10 × norm(min(runtime/180, 1))
```

## 5. Preset AUM

| Preset | AUM min | Mục đích |
|---|---:|---|
| Broad | 1.000 | Nhiều ứng viên |
| Balanced | 5.000 | Mặc định |
| Strict | 10.000 | Ít nhiễu |

## 6. Vì sao Bị loại không hẳn là xấu

Có thể chỉ vì mới chạy, không giao dịch 7 ngày, hết slot, AUM thấp hoặc thiếu dữ liệu.
Luôn đọc `filter_reasons` trước khi kết luận.

## 7. Nguồn

`backend/app/services/funnel.py`, `docs/kehoach/03-bo-chi-so-va-scoring.md`.
