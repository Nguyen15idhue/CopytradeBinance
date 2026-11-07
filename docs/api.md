# API v1 — Phase 1

Base: `/api/v1`

## Quy ước

- Response thành công:

```json
{
  "data": {},
  "meta": { "request_id": "...", "generated_at": "..." },
  "error": null
}
```

- Response lỗi:

```json
{
  "data": null,
  "meta": { "request_id": "..." },
  "error": { "code": "TRADER_NOT_FOUND", "message": "...", "details": {} }
}
```

## Auth

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/auth/login` | `{email, password}` → access + refresh token |
| POST | `/auth/refresh` | `{refresh_token}` → cặp token mới (rotate) |
| POST | `/auth/logout` | `{refresh_token}` → thu hồi |
| GET | `/auth/me` | Thông tin user hiện tại |

- Access token 15 phút, refresh 7 ngày.
- Login rate limit 5/phút/IP.
- Gửi header `Authorization: Bearer <access_token>` cho endpoint bảo vệ.

## Trader detail mở rộng

| Endpoint | Nội dung |
|---|---|
| GET `/traders/{id}/performance` | 4 window, `chartItems`, benchmark null + note |
| GET `/traders/{id}/positions` | Phân trang 50 (≤200), filter `symbol`, `side` |
| GET `/traders/{id}/trades` | Phân trang 100 (≤200), filter `symbol`, `side` |
| GET `/traders/{id}/transfers` | Timeline nạp/rút |
| GET `/traders/{id}/risk` | `risk_level`, flags, events + evidence |
| GET `/traders/{id}/score` | `config_version`, score, band, breakdown, hard flags |

- 404 wrapper `TRADER_NOT_FOUND` nếu id không tồn tại.
- `benchmark` luôn `null` khi chưa có nguồn klines; không nội suy.

## Compare

### GET `/compare?ids=a,b`

- Bắt buộc 2–4 id; sai số lượng → 422 `INVALID_COMPARE`.
- Trả `items`, `series` (chartItems), `correlation` (Pearson + `sample_days` + disclaimer “estimated”).
- Correlation cần ≥ 30 điểm chung; thiếu → `null`, không bịa số.

## Screener

### GET `/traders`

Filter/sort/pagination. Mặc định `include_excluded=false`, sort `score desc`, `page_size ≤ 100`.

Query: `q, portfolio_type, status, potential_tier (lặp lại), include_excluded, min_pre_score,
min_roi_90d, max_roi_90d, max_mdd_90d, min_sharpe, max_sharpe, min_win_rate, max_win_rate,
min_runtime_days, min_total_orders, min_copiers, min_copy_aum, max_leverage, risk_level,
has_sharpe, sort_by, sort_dir, page, page_size`.

`potential_tier` nhận alias `excluded | watch | qualified | high` hoặc tên nội bộ.

Mỗi item có score, band, confidence, breakdown, risk_level, tier, metrics chính và `filter_reasons`.

### GET `/traders/funnel-summary`

`{ universe, watch, qualified, high, excluded }`.

### GET `/traders/export.csv`

CSV theo filter hiện tại (tối đa 100 dòng), UTF-8.

### Saved views

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/saved-views` | Danh sách view của user |
| POST | `/saved-views` | `{name, filters}`; trùng tên thì cập nhật |
| DELETE | `/saved-views/{id}` | Xoá view của user |

## Collector & Data Health

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| GET | `/collector/status` | user | Tier counts, lần chạy gần nhất theo tầng, jobs, raw archive, kill switch |
| POST | `/collector/run-scan` | admin | 202 + `job_id`; scan + recompute |
| POST | `/collector/run-deep` | admin | 202 + `job_id`; performance → detail/positions/transfers → trades |
| GET | `/collector/jobs/{job_id}` | user | Trạng thái job trong process |
| POST | `/collector/kill-switch` | admin | `{active: true}` tắt collector; `{active: false}` bật lại |

- Kill switch: env `COLLECTOR_KILL_SWITCH` hoặc `app_settings['collector.enabled']`; khi tắt, run-* trả **409** `COLLECTOR_DISABLED`.
- Job chạy nền trong process API; restart sẽ mất trạng thái job (Phase 5 chuyển sang queue/DB).
- Khóa chống chạy song song: Redis `lock:collector:scan` / `lock:collector:deep`, TTL 30 phút.

## Universe

### GET `/universe/summary`

Số lượng theo tier + lần scan L0 gần nhất.

```json
{ "data": { "counts": { "watch": 398, "qualified_upper": 97, "high_upper": 14, "excluded": 10621 },
            "total": 11130, "watch_total": 509, "qualified_total": 111, "high_total": 14,
            "cohort": "all", "last_scan": { "status": "success" } } }
```

### GET `/universe/traders`

Query: `tier` (nhận cả alias `qualified`/`high`), `reason`, `min_pre_score`, `q`, `page`, `page_size` (≤100).
Sắp xếp mặc định theo `pre_score` giảm dần.

### POST `/universe/recompute` (admin)

Tính lại tier/pre_score từ list snapshot mới nhất. Trả `counts`, `changed`, `watch_total`, `duration_seconds`.

- `potential_tier`: `excluded | watch | qualified_upper | high_upper` (B/A là upper bound ở tầng list).
- `pre_score`: percentile cohort chung PUBLIC+SIGNAL, chỉ để xếp thứ tự deep fetch.

## Trader

### GET `/traders/{id}`

Trả hồ sơ trader + 10 chỉ số + tier + confidence + provenance + flags.

- `null` giữ nguyên `null`, không đổi thành `0`.
- `tier`: `excluded | watch | qualified | high | unknown`.
- `reasons`: lý do loại/xếp tầng.
- `flags`: `missing_sharpe`, `missing_mdd`, `no_copiers`, `low_sample`, `excluded`, `derived_unavailable`.
- `provenance`: `source`, `collected_at`, `window`, `published`.

Ví dụ rút gọn:

```json
{
  "data": {
    "trader": { "id": "...", "nickname": "...", "portfolio_type": "PUBLIC" },
    "tier": "qualified",
    "reasons": [],
    "metrics": [
      { "key": "roi_90d", "label": "ROI 90D", "value": 19.19, "unit": "%", "window": "90D" }
    ],
    "confidence": 0.89,
    "flags": ["derived_unavailable"],
    "provenance": { "source": "demo", "window": "90D", "published": true }
  },
  "error": null
}
```
