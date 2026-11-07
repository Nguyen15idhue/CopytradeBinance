---
id: compare
title: "Compare và tương quan"
group: "Phân tích"
order: 10
keywords: "compare, correlation, tương quan, estimated, chartItems, 30 ngày"
---

# Compare và tương quan

## 1. So sánh

- So sánh 2–4 trader.
- Bảng gồm tier, score, band, confidence, risk, ROI, MDD, Sharpe,
  WinRate, leverage, profit factor, runtime, copier PnL, Copy AUM.
- Chart ROI lũy kế từ chartItems.

## 2. Tương quan

- Là **ước tính** từ ROI lũy kế chartItems.
- Sai phân theo ngày.
- Bị pha loãng bởi nạp/rút.
- Cần tối thiểu 30 ngày mẫu.
- Không dùng để chia vốn hoặc position sizing.

## 3. Giới hạn

- Correlation không phải quan hệ nhân quả.
- Không phản ánh rủi ro đuôi.
- Không thay thế risk review.

## 4. Nguồn

`backend/app/services/compare.py`, `docs/api.md`.
