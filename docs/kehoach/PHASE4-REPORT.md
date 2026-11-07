# PHASE 4 REPORT — Detail + Compare + Risk Monitor

> Ngày: 07/11/2026 · Phạm vi 4.1–4.5 · Trạng thái: **ĐẠT GATE**

## 1. Gate

| Tiêu chí | Yêu cầu | Kết quả |
|---|---|---|
| Tooltip mỗi chỉ số | Có nguồn + cửa sổ | 10/10 metric card có `title` nguồn + window; E2E assert ≥ 10 |
| Compare 4 trader | Không vỡ layout | E2E ở 1440px, không overflow ngang (≤ 4px) |
| Risk evidence | Mở được | Click event mở JSON evidence; E2E pass |
| Không open positions giả | Không hiển thị | UI ghi rõ Binance không cung cấp; API chỉ trả vị thế đã đóng |
| Correlation disclaimer | “estimated” | Có trong API + UI; E2E assert |
| Detail p95 | < 300ms cache / < 1s cold | **cold 78ms · warm p95 49ms** (median 41ms) |
| Không undefined/NaN/null | Không lọt UI | E2E assert trên Screener, Compare, Risk, Detail |
| Test | Pass | **97 passed** (container, gồm integration) |

## 2. Đã triển khai

```text
api/v1/trader_detail.py     performance/positions/trades/transfers/risk/score
api/v1/compare.py           /compare?ids= (2–4)
api/v1/risk.py              /risk/summary, /risk/events
services/compare.py         Pearson trên sai phân chartItems
frontend/pages/TraderDetailPage.tsx   10 card, 3 chart recharts, breakdown, risk, tables
frontend/pages/ComparePage.tsx        picker, bảng 15 chỉ số, chart, correlation
frontend/pages/RiskMonitorPage.tsx    filter, list, evidence
```

## 3. Kiểm thử

- API detail: contract 6 endpoint, 404 wrapper, phân trang + filter side.
- Compare: 5 unit (identity/identical/inverse/insufficient/empty) + 2 integration (contract, 422).
- Risk: integration summary + filter + evidence.
- E2E: login → Data Health → Screener → Compare (4 trader) → Risk (mở evidence) → Detail qualified → Detail excluded → logout.
- Full suite: 97 passed; `npm audit` 0 lỗi.

## 4. Quyết định

- Benchmark vẫn null (chưa có nguồn klines); UI ghi “Không có”, không nội suy.
- Drawdown chart là **estimated** từ chartItems, có cảnh báo flow.
- Correlation cần ≥ 30 điểm chung; thiếu thì `null`.
- Không cache riêng cho detail; p95 hiện tại đã dưới ngưỡng cache.
- Chart bundle tăng (recharts) → build cảnh báo chunk > 500kB; chấp nhận ở Phase 4, có thể code-split Phase 5.

## 5. Vấn đề đã biết

1. `excess_return` null do thiếu benchmark.
2. Ranking UI chưa có (mới có service + snapshot); nằm ngoài checklist 4.x.
3. Saved views chưa hỗ trợ chia sẻ giữa user (đúng thiết kế Phase 3).
4. Chart dùng chartItems có thể lệch khi nạp/rút lớn.

## 6. Kết luận

Phase 4 đạt gate: detail đủ sâu, compare 4 trader ổn định, risk evidence mở được, không bịa dữ liệu.
Sẵn sàng Phase 5 — AI report + Settings + Hardening.
