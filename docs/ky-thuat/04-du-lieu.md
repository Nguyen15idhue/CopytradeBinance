---
id: du-lieu
title: "Nguồn và hợp đồng dữ liệu"
group: "Nền tảng"
order: 4
keywords: "dữ liệu, binance, list, detail, performance, position, trade, transfer, published, derived, estimated, null"
---

# Nguồn và hợp đồng dữ liệu

## 1. Sáu endpoint Binance

| Endpoint | Dữ liệu chính |
|---|---|
| List | Universe, ROI, PnL, MDD, WinRate, AUM, Sharpe, copier, tier đầu vào |
| Detail | AUM, Copy AUM, số copier, slot, leverage, mô tả |
| Performance | ROI/PnL/MDD/Sharpe/WinRate/copier PnL theo 7/30/90/180D |
| Position history | Vị thế đã đóng, leverage, PnL, ROI, thời gian giữ |
| Trade history | Fill, phí, realized profit |
| Transfer history | Nạp/rút |

## 2. Cửa sổ thời gian

Các chỉ số performance có 4 cửa sổ: `7D`, `30D`, `90D`, `180D`.
Hệ thống mặc định dùng `90D` cho screener/detail; compare có thể dùng nhiều cửa sổ.

## 3. Published / Derived / Estimated

| Loại | Nguồn | Ví dụ |
|---|---|---|
| Published | Binance trả trực tiếp | ROI, PnL, MDD, Sharpe, WinRate, copier PnL |
| Derived | Hệ thống tính từ position/trade | max leverage, profit factor, payoff, holding, fee drag |
| Estimated | Ước tính từ chartItems | drawdown, tương quan |

Quy tắc: **Published > Derived > Estimated**. Không tự tính thay thế số published.

## 4. Quy tắc null

- `null` nghĩa là không có dữ liệu, **không đổi thành 0**.
- Sharpe null hiển thị `N/A`, không chấm 0.
- Profit factor null nếu mẫu < 5 vị thế.
- MDD chỉ dùng published, không tự tính từ chartItems.

## 5. WinRate

- **WinRate order** = winOrders / totalOrder.
- **WinRate position** = vị thế thắng / tổng vị thế đóng.
- Hai chỉ số này khác nhau; không trộn.

## 6. Data confidence

Confidence 0–1 phản ánh độ đầy đủ và độ mới của dữ liệu:

- coverage: bao nhiêu nhóm dữ liệu có mặt;
- history: đủ lịch sử;
- freshness: dữ liệu mới;
- continuity: chuỗi không bị đứt.

Confidence thấp không có nghĩa trader xấu; nghĩa là kết luận kém chắc chắn.

## 7. Dữ liệu không có

- Vị thế đang mở.
- PnL từng copier.
- Funding, slippage, giá thanh lý.
- Lý do lead vào/ra lệnh.

## 8. Nguồn

`docs/kehoach/02-data-contract-binance.md`, `docs/kehoach/03-bo-chi-so-va-scoring.md`.
