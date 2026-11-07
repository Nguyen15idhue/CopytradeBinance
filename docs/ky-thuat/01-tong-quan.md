---
id: tong-quan
title: "Tổng quan hệ thống"
group: "Nền tảng"
order: 1
keywords: "tổng quan, phạm vi, auto-trade, screener, risk, kiến trúc, mục tiêu"
---

# Tổng quan hệ thống

## 1. Mục tiêu

CopytradeBinance là công cụ **screener & risk analytics** cho copy trading Binance Futures.
Hệ thống thu thập dữ liệu công khai, tính chỉ số, xếp hạng và hiển thị rủi ro để người dùng
tự quyết định.

## 2. Làm gì

- Thu thập dữ liệu công khai từ Binance Futures.
- Chuẩn hóa dữ liệu list, detail, performance, position, trade, transfer.
- Tính chỉ số published/derived/estimated.
- Gán tier, chấm score, phát risk event, xếp hạng.
- So sánh trader, xem lịch sử, xuất CSV.
- Tạo nhận định AI có evidence (không sửa score/ranking).

## 3. Không làm gì

- Không auto-trade.
- Không kết nối API giao dịch của người dùng.
- Không paper copy.
- Không đưa lời khuyên đầu tư.
- Không hiển thị dữ liệu Binance không cung cấp: vị thế đang mở, PnL từng copier,
  funding, slippage, giá thanh lý.

## 4. Thành phần

| Thành phần | Vai trò |
|---|---|
| Frontend React/Vite | Screener, Detail, Compare, Risk, Ranking, Settings, Help, Technical docs |
| FastAPI backend | API, auth, scoring, risk, AI, settings |
| PostgreSQL | Trader, snapshot, metric, score, risk, audit |
| Redis | Lock collector, cache/coordination |
| Worker | Scheduler collector |
| Nginx | Reverse proxy, CSP, TLS |
| OpenRouter | AI report |

## 5. Luồng dữ liệu

```text
Binance BAPI
   ↓ collector (L0/L2/L3/L4)
PostgreSQL + raw archive
   ↓ quant/scoring
metrics → tier → score → risk → ranking
   ↓ API
React UI
```

## 6. Giới hạn

- Dữ liệu công khai có thể thiếu, trễ hoặc thay đổi.
- Không có dữ liệu vị thế đang mở hoặc PnL từng copier.
- Kết quả quá khứ không đảm bảo tương lai.
- Hệ thống chỉ hỗ trợ quyết định, không thay thế quyết định của người dùng.

## 7. Nguồn

`docs/kehoach/01-pham-vi-va-kien-truc.md`, `docs/huong-dan-nguoi-moi.md`.
