---
id: data-health
title: "Data Health và Collector"
group: "Vận hành"
order: 11
keywords: "data health, collector, L0, L2, L3, L4, lock, retry, kill switch, freshness"
---

# Data Health và Collector

## 1. Các tầng thu thập

| Tầng | Việc làm |
|---|---|
| L0 | Quét universe |
| L2 | Performance 4 cửa sổ |
| L3 | Detail + position + transfer |
| L4 | Toàn bộ trade history |

## 2. Chu kỳ mặc định

- Scan: 60 phút.
- Performance: 6 giờ.
- Detail: 12 giờ.
- Trades: 24 giờ.

Có thể đổi trong Settings; worker đọc lại mỗi vòng 60 giây.

## 2b. Cách tính "đến hạn"

- `last_success` = `max(collection_logs.finished_at)` theo layer tương ứng và `status='success'`;
  bỏ qua log do test tạo (`detail.test = true`).
- Job đến hạn khi `now - last_success >= interval` (deep job cộng jitter ±5 phút cố định theo job).
- Chưa từng chạy → chạy ngay khi worker khởi động.
- Job lỗi/timeout → thử lại sau 15 phút, tối đa 3 lần rồi chờ interval tiếp theo.
- Timeout mỗi job: `COLLECTOR_JOB_TIMEOUT_MIN` (mặc định 60 phút).
- Nhờ vậy restart worker không còn đẩy deep fetch lùi 6/12/24 giờ.

## 3. Lock và retry

- Redis lock + fallback advisory lock.
- Retry/backoff khi Binance lỗi.
- Cooldown khi bị rate limit.
- Job skip nếu không lấy được lock.

## 4. Kill switch

- Dừng collector khẩn cấp.
- Job mới bị skip.
- Không xoá dữ liệu đã thu thập.

## 5. Freshness

- Dữ liệu cũ > 150 phút bị cảnh báo R09/HF05.
- Data Health hiển thị lần chạy gần nhất, request, items, lỗi.

## 6. Raw archive

- Lưu JSON thô.
- Nén sau 7 ngày, giữ 90 ngày.
- Không commit vào git.

## 7. Nguồn

`docs/kehoach/01-pham-vi-va-kien-truc.md`, `backend/app/services/deep_fetch.py`,
`backend/app/services/universe.py`, `docs/api.md`.
