---
id: chi-so
title: "Bộ chỉ số"
group: "Phân tích"
order: 6
keywords: "chỉ số, roi, pnl, mdd, sharpe, winrate, profit factor, payoff, calmar, confidence, low sample"
---

# Bộ chỉ số

## 1. Phân tầng chỉ số

| Tầng | Nội dung |
|---|---|
| T0 | Metadata và chất lượng dữ liệu |
| T1 | Published metrics từ Binance |
| T2 | Derived metrics từ position/trade |
| T3 | Dữ liệu không có |

## 2. T0 — Metadata và chất lượng

- `potential_tier`: excluded/watch/qualified/high.
- `pre_score`: 0–100, chỉ để xếp thứ tự deep fetch.
- `filter_reasons`: lý do bị loại.
- `runtime_days`: thời gian hoạt động.
- `portfolio_type`: PUBLIC/SIGNAL/PRIVATE.
- `status`: ACTIVE/CLOSED/PAUSED.
- `data_freshness_minutes`: độ mới dữ liệu.
- `data_confidence`: 0–1.
- `missing_fields`: field null.

## 3. T1 — Published metrics

ROI, PnL, MDD, Sharpe, WinRate order, winOrders, totalOrders, copier PnL,
AUM, Copy AUM, margin balance, số copier, slot, profit sharing, badge, tags.

## 4. T2 — Derived metrics

Max leverage, avg leverage, margin mode, thời gian giữ, position win rate,
profit factor, payoff ratio, best/worst position PnL, worst position ROI,
near liquidation count, long/short ratio, symbol concentration, total fills.

## 5. Công thức quan trọng

- **ROI** = lợi nhuận / vốn × 100.
- **MDD** = mức sụt giảm lớn nhất từ đỉnh, dùng published.
- **Sharpe** = lợi nhuận điều chỉnh biến động; null → N/A.
- **WinRate order** = winOrders / totalOrders × 100.
- **Profit Factor** = tổng lãi / |tổng lỗ|; null nếu mẫu < 5 vị thế.
- **Payoff** = lãi trung bình / |lỗ trung bình|.
- **Calmar** = ROI / MDD.
- **Fee drag** = phí / notional.
- **Symbol concentration** = notional lớn nhất / tổng notional.

## 6. WinRate order và position

Hai chỉ số khác nhau. Không dùng lẫn:

- Order: số lệnh thắng / tổng lệnh đóng.
- Position: số vị thế thắng / tổng vị thế đóng.

## 7. Low sample

- Mẫu nhỏ làm kết luận kém tin cậy.
- Profit factor null nếu < 5 vị thế.
- Không chấm 0 cho chỉ số thiếu dữ liệu.

## 8. Nguồn

`docs/kehoach/03-bo-chi-so-va-scoring.md`, `backend/app/services/quant/`.
