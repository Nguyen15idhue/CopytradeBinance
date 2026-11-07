# 04 — Kế hoạch: giữ trạng thái Screener, đa khung thời gian, mở rộng bộ lọc, cấp đủ dữ liệu cho AI

> Trạng thái: **kế hoạch**, chưa triển khai.
> Phạm vi: Frontend Screener/Detail + backend screener/metrics/agent.
> Nguồn khảo sát: đọc `ScreenerPage.tsx`, `TraderDetailPage.tsx`, `services/screener.py`,
> `api/v1/screener.py`, `services/agent/db_tools.py`, `services/agent/orchestrator.py`,
> `models/trader_metric.py` + query trực tiếp PostgreSQL (511 trader, ngày 2026-11-07).

---

## 1. Vấn đề đã xác nhận (có bằng chứng)

### V1 — Mất bộ lọc và vị trí khi xem trader rồi quay lại

| Bằng chứng | Chi tiết |
|---|---|
| `ScreenerPage.tsx:72-94` | Toàn bộ filter là `useState` thuần: `search, tier, risk, roiMin, mddMax, sharpeMin, winRateMin, runtimeMin, ordersMin, leverageMax, minCopyMax, sortBy, sortDir, page`. |
| Không có `useSearchParams` / `localStorage` | Không đồng bộ URL, không lưu storage → unmount là mất. |
| `TraderDetailPage.tsx:175,196` | `<Link to="/screener">` hardcode → luôn về filter mặc định. |
| Hệ quả | Người dùng phải lọc lại từ đầu mỗi lần xem chi tiết. |

### V2 — Bộ lọc quá ít trường

| Nguồn | Số lượng |
|---|---|
| `ScreenerFilters` (backend) | 22 filter |
| UI dùng | 12 filter |
| Có backend nhưng thiếu UI | `portfolio_type`, `status`, `min_score`, `min_pre_score`, `max_roi_90d`, `max_sharpe`, `max_win_rate`, `min_copiers`, `min_copy_aum`, `has_sharpe` |
| Chưa có ở cả backend | copier PnL, AUM min/max, `avg_leverage`, `profit_factor`, `fee_drag_pct`, `position_win_rate`, `confidence`, `risk_score_max`, `copy_aum_ratio`, `hhi`, `positive_days_pct`, `roi_stability` |
| Chưa có ở đâu | **Toàn bộ filter theo khung 7D / 30D / 180D** |

Độ phủ dữ liệu live (511 trader): `copier_pnl_90d` **511/511**, `max_leverage` 281,
`profit_factor` 248, `fee_drag_pct` 57, `current_copiers` 0–1000.

### V3 — UI chỉ hiển thị khung 90D

| Bằng chứng | Chi tiết |
|---|---|
| `trader_metrics` | Chỉ có cột scalar `roi_90d, mdd_90d, sharpe_90d, win_rate_order_90d, total_orders_90d, copier_pnl_90d`. |
| `metrics.published` (JSONB) | Đủ 4 khung, **511/511 trader có 7D và 180D**. |
| `ScreenerPage.tsx:565-577` | 13 cột, tất cả 90D. `SORT_COLUMNS` cũng chỉ 90D. |
| `TraderDetailPage.tsx:184,269,399` | Có gọi `/traders/{id}/performance` (trả đủ 4 window) nhưng **chỉ dùng chart**; `performance.data.windows` không render. |
| Hệ quả | Không thể lọc/sort ngắn hạn (7D, 30D) hay dài hạn (180D). |

### V4 — AI không nhận đủ dữ liệu

Ba nguyên nhân độc lập:

1. **Tool cắt field** (`db_tools.py:237-242`): mỗi khung chỉ trả `roi, mdd, sharpe` —
   mất `pnl, copier_pnl, win_orders, total_orders, win_rate_order`.
   Không gửi `derived` (38 field) và `profile` (10 field).
2. **Cắt chuỗi** (`orchestrator.py:210`): `str(tool_result.data)[:4000]` → 10 trader ×
   nhiều field bị cụt giữa bảng. `history` cắt `[:2000]` (dòng 77).
3. **Dùng Python `str()`** thay vì JSON compact → tốn token, khó parse.
   `ai_max_tokens = 2500`.

**Tổng chỉ số thực có trong DB** (khớp mô tả "vài chục đến gần trăm"):

| Nhóm | Số field |
|---|---:|
| `published` × 4 khung (8 field/khung) | 32 |
| `derived` | 38 |
| `profile` | 10 |
| `score.breakdown` (7 nhóm × score/weight/contribution) | 21 |
| tier, confidence, risk_score, veto, flags, risk_events | ~10 |
| **Tổng** | **~110** |

AI hiện chỉ nhận ~15–20 field trong số này.

---

## 2. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| D1 | URL là **nguồn sự thật duy nhất** của trạng thái Screener | F5, back/forward, share link, mở tab mới đều giữ nguyên |
| D2 | Thêm **`window` param** (`7D/30D/90D/180D`) thay vì nhân 4 bộ filter | UI gọn, filter/sort/column đổi theo khung đang chọn |
| D3 | Đa khung lưu **cột scalar** cho field cần filter/sort (roi, mdd, sharpe, copier_pnl, win_rate) | Index được, không phải ép kiểu JSONB mỗi query |
| D4 | `derived`/`profile` vẫn ở JSONB, chỉ thêm cột cho field cần filter | Tránh phình bảng |
| D5 | AI nhận **JSON compact**, có tham số `detail` để chọn mức dữ liệu | Cân bằng token và độ đầy đủ |
| D6 | Không đổi port, không sửa migration cũ, migration mới đánh số tiếp từ `0018` | AGENTS.md §2, §3 |
| D7 | Không đưa lời khuyên đầu tư; mọi số AI trả vẫn qua verifier | AGENTS.md §4 |

---

## 3. Thiết kế chi tiết

### 3.1 URL state (D1)

```
/screener?q=&tier=high_upper&risk=low&window=30D
  &roi_min=&mdd_max=&sharpe_min=&win_min=&runtime_min=&orders_min=
  &lev_max=&copiers_min=&copier_pnl_min=&aum_min=&pf_min=&conf_min=
  &copy_aum_max=&fee_max=&sort=score&dir=desc&page=2&size=50
```

- Mọi thay đổi filter → `setSearchParams(..., {replace: true})` để không rác history.
- Đọc param khi mount → khởi tạo state; state chỉ là bản sao để render.
- Nút "Xóa bộ lọc" xóa toàn bộ param (giữ `window`).
- `saved_views` lưu nguyên query string này.
- Detail: nút quay lại dùng `navigate(-1)` khi có history, fallback `/screener?<query đã lưu>`.
  Lưu query gần nhất vào `sessionStorage["ct_screener_query"]` để deep-link từ nơi khác vẫn khôi phục.

### 3.2 Đa khung thời gian (D2, D3)

**Migration `0018_metric_windows`** — thêm 15 cột vào `trader_metrics`:

| Nhóm | Cột mới |
|---|---|
| ROI | `roi_7d, roi_30d, roi_180d` |
| MDD | `mdd_7d, mdd_30d, mdd_180d` |
| Sharpe | `sharpe_7d, sharpe_30d, sharpe_180d` |
| Copier PnL | `copier_pnl_7d, copier_pnl_30d, copier_pnl_180d` |
| WinRate order | `win_rate_order_7d, win_rate_order_30d, win_rate_order_180d` |

Index đề xuất:

```sql
CREATE INDEX ix_tm_roi_7d   ON trader_metrics (roi_7d);
CREATE INDEX ix_tm_roi_30d  ON trader_metrics (roi_30d);
CREATE INDEX ix_tm_roi_180d ON trader_metrics (roi_180d);
CREATE INDEX ix_tm_copiers  ON trader_metrics (current_copiers DESC);
CREATE INDEX ix_tm_copier_pnl ON trader_metrics (copier_pnl_90d DESC);
CREATE INDEX ix_tm_pf       ON trader_metrics (profit_factor);
```

- `builder.py` ghi thêm cột khi `rebuild_metrics()` chạy.
- Backfill: `python -m app.collector_cli metrics` (idempotent).
- Null giữ null (7D của trader mới có thể thiếu) — không gán 0.

### 3.3 Bộ lọc mở rộng (D4)

`ScreenerFilters` thêm:

```
window: Literal["7D","30D","90D","180D"] = "90D"
min_copiers, max_copiers
min_copier_pnl, max_copier_pnl
min_aum, max_aum
min_avg_leverage, max_avg_leverage
min_profit_factor, max_profit_factor
max_fee_drag_pct
min_position_win_rate
min_confidence
max_risk_score
min_copy_aum_ratio
```

Quy tắc: `window` quyết định cột `roi_*`, `mdd_*`, `sharpe_*`, `win_rate_*`, `copier_pnl_*`
dùng cho filter/sort hiển thị. `copier_pnl_7d` chưa có thì filter theo khung đó trả rỗng
có `meta.window_missing` — **không fallback im lặng sang 90D**.

### 3.4 UI Screener (D2)

- Thanh chọn khung: `7D | 30D | 90D | 180D` (mặc định 90D) — đổi khung đổi luôn
  cột ROI/MDD/Sharpe/Copier PnL/WinRate và sort.
- Cột mới: **Số copier**, **Copier PnL**, **AUM**, **Profit factor**, **Độ tin cậy**.
- Bộ lọc chia 3 nhóm có thể thu gọn:
  1. Hiệu suất (ROI, MDD, Sharpe, WinRate, Profit factor)
  2. Quy mô & phổ biến (Số copier, Copier PnL, AUM, Copy AUM)
  3. Rủi ro & chất lượng (Risk level, Risk score, Leverage, Fee drag, Confidence, Runtime, Orders)
- Badge đếm số filter đang bật + nút "Xóa tất cả".
- Giữ nguyên bảng, drawer breakdown, saved views, CSV.

### 3.5 Detail hiển thị đủ 4 khung (D3)

- Bảng "Hiệu suất theo khung": 4 dòng (7D/30D/90D/180D) × cột
  `ROI, PnL, MDD, Sharpe, WinRate, Copier PnL, số lệnh`.
- Nguồn: `performance.data.windows` (API đã có sẵn, chỉ cần render).
- Đánh dấu khung đang chọn ở Screener nếu user bấm từ bảng đa khung.

### 3.6 AI nhận đủ dữ liệu (D5)

**a) `get_trader_profile` tham số mới `detail`** (`summary` | `full`, mặc định `full`):

```json
{
  "trader_id": "...",
  "tier": "...", "score": 74.1, "band": "good", "confidence": 0.91,
  "risk": {"level": "low", "score": 28.5, "veto": []},
  "windows": {
    "7D":   {"roi": 4.8, "pnl": 65.6, "mdd": 2.08, "sharpe": 0.67,
             "copier_pnl": 1119.0, "win_rate_order": 50.0,
             "win_orders": 2, "total_orders": 4},
    "30D":  { "...": "..." },
    "90D":  { "...": "..." },
    "180D": { "...": "..." }
  },
  "derived": { "profit_factor": 1.4, "fee_drag_pct": 2.1, "hhi": 0.18,
               "roi_stability": 4.9, "positive_days_pct": 19.1,
               "max_leverage": 5, "avg_leverage": 2.7,
               "position_win_rate": 55.2, "copy_aum_ratio": 94.6,
               "worst_position_roi": -12.3, "near_liquidation_count": 0,
               "...": "đủ 38 field" },
  "profile": { "aum": 26396.2, "copy_aum": 24965.6, "current_copiers": 2,
               "max_copiers": 200, "profit_sharing_rate": 10.0 },
  "breakdown": { "components": { "...": "7 nhóm" } },
  "flags": ["missing_benchmark"],
  "as_of": "2026-11-07T15:06:58Z"
}
```

**b) `search_traders`**: thêm `include` (`metrics` | `full`) để chọn field trả về,
mặc định trả bộ rút gọn có copier/PnL nhưng không `derived` đầy đủ.

**c) `orchestrator`**:
- Đổi `str(data)` → `json.dumps(data, ensure_ascii=False, separators=(",", ":"))`.
- Giới hạn observation: `summary` 8.000 ký tự; nếu vượt → trả
  `{"truncated": true, "omitted_rows": n, "hint": "gọi lại với limit nhỏ hơn"}` thay vì cắt giữa chuỗi.
- Nâng `ai_max_tokens` 2500 → **4000**; thêm config `agent_observation_chars = 8000`.
- Giữ verifier: mọi số vẫn phải có evidence; thêm evidence cho từng window.

**d) Prompt**: nêu rõ agent phải trả lời theo khung thời gian khi câu hỏi liên quan
ngắn/dài hạn, và hiển thị `unknown` khi khung thiếu dữ liệu.

---

## 4. Các bước triển khai

### Bước 4.0.1 — URL state + quay lại giữ vị trí
- `useSearchParams` là nguồn sự thật cho mọi filter + `window` + `sort` + `page` + `size`.
- `sessionStorage["ct_screener_query"]` cho deep-link.
- Detail: `navigate(-1)` + fallback link mang query đã lưu.
- Test Playwright: lọc → mở trader → back → filter + trang giữ nguyên; F5 vẫn giữ; share URL mở đúng.

### Bước 4.0.2 — Migration `0018_metric_windows`
- 15 cột + index; `downgrade()` đầy đủ; không sửa migration cũ.
- Test: `alembic upgrade head` → check cột; `downgrade -1` → `upgrade head`.

### Bước 4.0.3 — Builder ghi đa khung
- `quant/builder.py` map `published[window]` → cột mới; null giữ null.
- Backfill live; test: 511/511 có `roi_7d` và `roi_180d`; null không thành 0.

### Bước 4.0.4 — Screener API đa khung + filter mở rộng
- `ScreenerFilters.window`; `SORT_COLUMNS` theo window; filter mới.
- `meta.window_missing` khi khung thiếu dữ liệu.
- Test: sort ROI 7D đúng thứ tự; filter copier PnL; filter AUM; window thiếu → rỗng + meta.

### Bước 4.0.5 — UI Screener đa khung
- Selector 7D/30D/90D/180D; cột mới; 3 nhóm filter thu gọn; badge filter; xóa tất cả.
- Test build + Playwright: đổi khung đổi cột; filter copier/PnL/AUM hoạt động; không `undefined/NaN`.

### Bước 4.0.6 — Detail hiển thị 4 khung
- Bảng "Hiệu suất theo khung" từ `performance.data.windows`.
- Test: 4 dòng, đủ cột, null → `N/A`.

### Bước 4.0.7 — Agent trả đủ dữ liệu
- `get_trader_profile` đủ windows + derived + profile; `detail` param.
- `search_traders` thêm `include`.
- Evidence cho từng window; verifier vẫn chặn số bịa.

### Bước 4.0.8 — Orchestrator JSON + giới hạn
- `json.dumps` compact; cắt có cấu trúc; `ai_max_tokens=4000`, `agent_observation_chars=8000`.
- Prompt nhắc trả lời theo khung.

### Bước 4.0.9 — QA cuối
- Backend full `RUN_INTEGRATION=1` + ruff; frontend build; Playwright full + case mới.
- `check_refs` 0 lỗi; kiểm tra không secret; `git status` sạch.

---

## 5. Checklist nghiệm thu

### UX
- [ ] Lọc → mở trader → back: giữ nguyên filter, trang, sort.
- [ ] F5 trên Screener: giữ nguyên trạng thái.
- [ ] Copy URL gửi máy khác: mở đúng filter.
- [ ] Nút "Xóa tất cả" hoạt động, giữ `window`.

### Đa khung
- [ ] Chọn 7D: cột ROI/MDD/Sharpe/Copier PnL/WinRate đổi sang 7D.
- [ ] Sort theo ROI 7D, 30D, 180D đúng thứ tự.
- [ ] Khung thiếu dữ liệu: hiện `N/A` + thông báo, không hiện 0.
- [ ] Detail có bảng 4 khung, khớp API.

### Bộ lọc
- [ ] Lọc theo số copier (min/max).
- [ ] Lọc theo Copier PnL (min/max).
- [ ] Lọc AUM, profit factor, fee drag, confidence, risk score, leverage trung bình.
- [ ] Không thêm điều kiện ngoài câu hỏi khi dùng NL search.

### AI
- [ ] Hỏi "trader X 7D vs 180D" → trả cả hai khung, có nguồn.
- [ ] Hỏi "top 5 copier đông + copier PnL cao" → dùng filter thật, không báo unknown.
- [ ] Không còn `str()` truncation làm cụt bảng.
- [ ] Verifier: số trong câu trả lời đều có evidence.
- [ ] Không lời khuyên đầu tư.

### Kỹ thuật
- [ ] Migration `0018` up/down OK.
- [ ] `ruff` pass, `pytest` full pass.
- [ ] `npm run build` pass, Playwright full pass.
- [ ] `check_refs` 0 lỗi.
- [ ] Không commit file rác/secret.

---

## 6. Rủi ro & kiểm soát

| Rủi ro | Kiểm soát |
|---|---|
| Thêm 15 cột làm chậm ghi metrics | Chỉ ghi 1 lần/trader/run; index chỉ trên field filter/sort |
| Null 7D/180D bị hiểu là 0 | Null giữ null; UI `N/A`; test riêng |
| URL dài, khó đọc | Chỉ đưa param khác mặc định vào URL |
| AI tốn token hơn (4000 tokens) | Chỉ `detail=full` khi cần; search mặc định rút gọn; log cost |
| Truncation mới làm mất dữ liệu | Cắt có cấu trúc kèm `hint`, không cắt giữa JSON |
| Filter đa khung gây hiểu nhầm | Hiển thị rõ "Đang xem khung 30D" trên bảng và chip |

---

## 7. Việc không làm

- Không thêm WebSocket realtime.
- Không auto-trade, không khuyến nghị đầu tư.
- Không đổi cổng host (web 8090, backend 8010).
- Không sửa `phase0/`, không sửa migration cũ.
- Không tính lại MDD từ `chartItems` (giữ published).

---

## 8. Definition of Done

- 4 vấn đề V1–V4 đóng, có test chứng minh.
- Screener giữ trạng thái qua back/F5/share URL.
- Lọc/sort được cả 4 khung và đủ nhóm chỉ số (copier, PnL, AUM, leverage, profit factor…).
- Detail hiển thị đủ 4 khung.
- AI nhận đủ ~110 chỉ số (theo `detail`), trả lời có nguồn, không bịa số.
- Backend + frontend + E2E pass; docs cập nhật (`api.md`, `12-ai.md`, `TASKS.md`, `SESSION.md`).

## 9. Tiến độ triển khai

- [x] B4.0.1 URL state Screener — `frontend/src/lib/screenerQuery.ts` (parse/serialize + sessionStorage),
  `ScreenerPage` dùng `useSearchParams` (replace), `TraderDetailPage` back bằng `navigate(-1)` + fallback
  query đã lưu; E2E checkpoint "Screener giữ trạng thái" PASS.
  → Bằng chứng: `npm run build` pass; `npm run test:e2e` PASS; commit `4.0.1`.
