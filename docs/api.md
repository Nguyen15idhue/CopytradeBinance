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

## Ranking

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| GET | `/ranking?board=overall\|low_risk\|consistency` | user | Snapshot mới nhất của bảng |
| POST | `/ranking/run` | admin | Chụp snapshot 3 bảng theo config hiện tại |

Trả `board`, `config_version`, `collected_at`, `items` (rank, trader, score/band/confidence, tier,
risk_level, ROI/MDD/Sharpe), `total`. Board không hợp lệ → 422.

## Settings

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| GET | `/settings` | user | Snapshot scoring/ai/collector/system |
| PUT | `/settings` | admin | Lưu cấu hình; đổi scoring tạo version mới |
| POST | `/settings/preview` | admin | Preview impact trên metrics hiện có |
| GET | `/settings/versions` | user | Lịch sử version scoring |
| POST | `/settings/rollback/{version}` | admin | Kích hoạt lại version cũ |

- Trọng số: 7 nhóm, 0–100, tổng > 0; sai → 422 `INVALID_WEIGHTS`.
- AI trả `key_masked` + `key_configured`; không bao giờ trả key.
- Mọi thay đổi/rollback ghi `audit_logs` (user, action, before/after).

## AI Report

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| POST | `/ai/analyze/{id}` | admin | Tạo report (cooldown 24h, budget, fallback) |
| GET | `/ai/reports/{id}` | user | Danh sách report gần nhất |
| GET | `/ai/reports/{id}/{report_id}` | user | Chi tiết report |

Report gồm `model_role` (primary/fallback/template), `model_used`, `prompt_version` (v2),
`summary`, `strengths`, `weaknesses`, `risk_flags`, `missing_data`, `evidence_ids`.
Prompt v2 yêu cầu trả lời tiếng Việt, mỗi nhận định phải có chỉ số + giá trị + ý nghĩa/ngưỡng;
validator từ chối output không có số liệu để buộc fallback template.
Response analyze có `cached`, `ai_configured`, `errors`; không bao giờ trả API key.

Lỗi: 403 viewer, 404 trader/report, 409 `NO_METRICS`/`AI_DISABLED`, 429 `AI_BUDGET_EXCEEDED`.

## AI Agent (admin-only)

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| POST | `/agent/chat` | admin | Chat SSE: `token/tool_call/tool_result/citation/warning/done/error` |
| POST | `/agent/search` | admin | NL → `{filters, chips, assumptions}` cho Screener |
| GET | `/agent/sessions` | admin | Danh sách đoạn chat (50 gần nhất) |
| GET | `/agent/sessions/{id}` | admin | Chi tiết session + message (tối đa 200) |
| PATCH | `/agent/sessions/{id}` | admin | Đổi `title`, `archived` |
| DELETE | `/agent/sessions/{id}` | admin | Xóa session (cascade message/tool/citation) |
| POST | `/agent/feedback` | admin | Đánh giá `message_id` (rating 1–5) |
| GET | `/agent/health` | user | Trạng thái `enabled`, `max_steps` |

Tool loop tối đa 8 bước, timeout 120s/request, tool 10s, rate limit 20/phút/admin.
Budget dùng `ai_usage.feature='agent'`; model từ `AI_MODEL_PRIMARY`, fallback `AI_MODEL_FALLBACK`
(resolve qua Settings override). Không gọi live trong test — mock transport OpenRouter.
Lỗi: 403 viewer, 404 session/message, 409 `AGENT_DISABLED`, 429 `AGENT_RATE_LIMITED`/`AGENT_BUDGET_EXCEEDED`.

## Risk Monitor

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/risk/summary` | Tổng event + đếm theo severity |
| GET | `/risk/events` | Filter `severity`, `status`, `trader`; phân trang |
| GET | `/traders/{id}/risk` | Event/flags của một trader |

Mỗi event có `code` R01–R19, `severity`, `label`, `evidence` JSON và `status` (`open`).
`GET /traders/{id}/risk` trả thêm `risk_score (0–100)` và `veto_reasons[]`; Sharpe âm veto `>=high` và cấm board `low_risk`.
Không có dữ liệu open positions từ Binance; UI ghi rõ, không mô phỏng.

## Screener

Tham số mới (4.0.4):
- `window` = `7D|30D|90D|180D` (mặc định 90D) — quyết định cột dùng cho `min_roi`, `max_roi`,
  `max_mdd`, `min_sharpe`, `max_sharpe`, `min_win_rate`, `max_win_rate`, `min_copier_pnl`,
  `max_copier_pnl`, `has_sharpe`, và sort `roi|mdd|sharpe|win_rate|copier_pnl`.
- Filter mới: `min_copiers`, `max_copiers`, `min_copier_pnl`, `max_copier_pnl`,
  `min_aum`, `max_aum`, `max_copy_aum`, `min_avg_leverage`, `max_avg_leverage`,
  `min_profit_factor`, `max_profit_factor`, `max_fee_drag_pct`, `min_position_win_rate`,
  `min_confidence`, `max_risk_score`, `min_copy_aum_ratio`.
- Legacy: `min_roi_90d`, `max_roi_90d`, `max_mdd_90d`, `min_sharpe`… vẫn giữ nghĩa 90D cố định
  (`min_sharpe`/`min_win_rate` nay theo `window`).

Response thêm: mỗi item có `windows` (`7D/30D/90D/180D` × `roi/mdd/sharpe/copier_pnl/win_rate`),
`avg_leverage`, `position_win_rate`, `risk_score`; meta có `window` và `window_missing`.

## Trader Detail — hiệu suất đa khung

`GET /traders/{id}/performance` trả `windows` cho cả 4 khung; UI hiển thị bảng
"Hiệu suất theo khung" (ROI, PnL, MDD, Sharpe, WinRate, Copier PnL, số lệnh).
Null giữ `N/A`, không đổi thành 0.

Tham số cũ vẫn dùng được: `max_min_copy_usd` (vốn tối thiểu ≤ X, qua view `agent_trader_copy_constraints`).

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

CSV theo filter hiện tại (tối đa 100 dòng), UTF-8. Header tiếng Việt:
`Mã trader, Biệt danh, Nhóm, Điểm, Mức điểm, Độ tin cậy, ROI 90D, MDD 90D,
Sharpe, WinRate, Số lệnh, Số ngày hoạt động, Số copier, Copy AUM, Đòn bẩy tối đa, Rủi ro`.

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
