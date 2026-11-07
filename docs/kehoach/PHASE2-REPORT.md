# PHASE 2 REPORT — Collector 2 tầng + raw storage

> Ngày: 07/11/2026 · Phạm vi 2.1–2.8 · Trạng thái: **ĐẠT GATE**

## 1. Gate

| Tiêu chí | Yêu cầu | Kết quả |
|---|---|---|
| Coverage 1 run | ≥ 99% của 11.124 | **11.132 = 100,07%** |
| Watch (C+B+A) | 400–700 | **511** (watch 425 · qualified 76 · high 10) |
| Excluded deep fetch | 0 | 0 tại thời điểm chọn |
| Chạy lại 3 lần | Không duplicate | counts giống hệt |
| Restart giữa crawl | Resume | kill 35s → chạy lại đủ, duplicate = 0 |
| Chu kỳ scan + shortlist | < 15 phút | 142,6s + 38,7s = **181,3s** |
| Full deep | Đo thật | 511 perf + 278 detail + 57 trades = **250,8s** |
| Test | Pass | **41 passed** (container) |

## 2. Kiến trúc

```text
services/collector/{http,binance,parsers,lock}.py   adapter 6 endpoint + retry/cooldown
services/universe.py + funnel.py                    scan, dedupe, tier, pre_score
services/deep_fetch.py                              L2 performance, L3 detail, L4 trades
services/storage/raw.py                             JSONL + gzip + retention
services/{config_store,jobs}.py                     kill switch, job registry
worker/scheduler.py                                 scan 60m, perf 6h, detail 12h, trades 24h
api/v1/{universe,collector}.py                      tier API + vận hành
migrations 0004–0007
frontend/src/pages/DataHealthPage.tsx
scripts/{smoke_bapi,smoke_collector}.ps1, check_refs.py
```

## 3. Số liệu đo thật

| Tầng | Target | Request | Items | Thời gian | Lỗi |
|---|---:|---:|---:|---:|---:|
| L0 scan | 11.132 | 372 | 11.132 | 142,6s | 0 |
| L2 performance | 511 | 2.044 | 2.044 metric | 38,7s | 0 |
| L3 detail + positions + transfers | 278 | ~1.600 | 70.567 pos + 8.228 tr | 77,9s | 0 |
| L4 full trades | 57 | 679 | 130.962 fill (120.595 unique) | 134,2s | 0 |

Tồn kho: traders 11.134 · performance 4.088 · positions 68.714 · transfers 8.329 · trades 120.595.
Raw archive: 372 file / ~144 MB.

## 4. Idempotency & resume

- 3 lần scan liên tiếp: traders 11.133, list snapshots 22.261, universe 11.133, metrics 4.088, trades 120.595 — không đổi.
- Kill giữa crawl sau 35s → xóa khóa → chạy lại: coverage đủ, duplicate snapshot trong giờ = 0.
- Trades chạy lại không nhân bản (hash unique).

## 5. Rate limit

- Mock: `11012005`, 429 body HTML, `Retry-After`, 404 không retry, circuit breaker.
- Live: nhiều `11012005` trong lần full trades, backoff xử lý hết, 0 request thất bại.
- Sau crawl lớn bị IP 429 → bổ sung cooldown toàn cục 30–180s, 5 retry, trades 1 trader/lần + 0,4s/trang.
- Gỡ khóa khi process chết: `docker compose exec redis redis-cli DEL lock:collector:scan lock:collector:deep`.

## 6. Kiểm thử

| Hạng mục | Kết quả |
|---|---|
| Backend container (`RUN_INTEGRATION=1`) | 41 passed |
| Backend ngoài container | 28 passed, 13 skipped |
| ruff / build / E2E | Pass |
| npm audit / secret scan | 0 lỗi / 0 secret |
| check_refs | 164 tham chiếu, 0 lỗi |
| Migration | 0007 head |

## 7. Vấn đề đã biết

1. B/A upper bound → HF04 hạ tier sau L2; lịch sử có thể còn positions/trades của trader nay đã excluded.
2. Job registry trong process; restart mất trạng thái job.
3. Redis lock TTL 30 phút; cần xóa tay nếu process chết.
4. BAPI IP rate limit sau crawl lớn; scheduler đã giãn tần suất.
5. `mdd=null` và `sharpe=null` giữ null + flag; `pre_score` cohort chung `all`.

## 8. Kết luận

Đạt toàn bộ gate Phase 2. Sẵn sàng Phase 3 — Quant + Scoring + Screener.
