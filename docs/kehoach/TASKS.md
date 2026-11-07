# TASKS — CHECKLIST THỰC HIỆN

> **Vai trò:** đây là checklist thực thi duy nhất cho **Phase 1–6**.  
> **Phase 0 giữ nguyên** trong file này vì đã hoàn thành; không sửa nội dung Phase 0.
>
> **Nguồn tham chiếu:** [`KE-HOACH-TONG-THE.md`](./KE-HOACH-TONG-THE.md).  
> Mỗi bước bên dưới ghi rõ **mục + khoảng dòng** cần đọc thêm, để không phải đọc lại toàn bộ kế hoạch.
>
> **Quy ước trạng thái:** `[ ]` chưa làm · `[~]` đang làm · `[x]` xong có bằng chứng · `[!]` bị chặn/cần quyết định.  
> **Quy ước dòng:** số dòng tính theo bản `KE-HOACH-TONG-THE.md` ngày **07/11/2026**. Nếu file thay đổi, tìm lại theo **tên mục** (ổn định hơn số dòng).  
> **Quy tắc task:** mỗi task ≤ 1 ngày; nếu lớn hơn thì tách nhỏ.

---

## 0. TỔNG QUAN

| Phase | Trạng thái | Thời lượng | Gate chính | Tham chiếu nhanh |
|---|---|---:|---|---|
| 0 — Data spike & pre-filter | `[x]` hoàn thành | 3–5 ngày | GO có điều kiện | `phase0/PHASE0_REPORT.md` |
| 1 — Foundation + vertical slice | `[x]` hoàn thành | 5–7 ngày | 1 trader chạy E2E | §5.2 (417–439), §10.1 (1615–1921), §13.4 (2345–2456) |
| 2 — Collector 2 tầng | `[ ]` | 4–6 ngày | Scan 11.124 ≥ 99%, Watch 400–700 | §6 (528–973), §12 (2105–2219) |
| 3 — Quant + Scoring + Screener | `[ ]` | 7–9 ngày | Screener dùng được, score breakdown đúng | §8 (1187–1449), §9 (1450–1612) |
| 4 — Detail + Compare + Risk | `[ ]` | 5–7 ngày | Detail sâu, compare 4 trader, risk evidence | §11.2–11.3 (2009–2057), §13.4–13.5 (2345–2489) |
| 5 — AI + Settings + Hardening | `[ ]` | 5–7 ngày | AI không sửa score, config version/rollback | §11.5 (2071–2084), §13.6–13.7 (2490–2543), §15.8 (3075–3095) |
| 6 — Testing + Deploy + Beta | `[ ]` | 4–6 ngày | Uptime 7 ngày, beta 3–5 user | §14 (2617–2918), §15 (2919–3128) |
| | | **33–47 ngày** | +20% buffer → **40–56 ngày** | |

**Đường găng:** Phase 1 → Phase 2 → Phase 3. Phase 4–5 có thể song song một phần nếu có thêm người.  
**Thực tế 1 dev full-time:** 7–9 tuần. **Part-time:** nhân đôi.

---

## 1. CÁCH DÙNG THAM CHIẾU

| Ký hiệu | Nghĩa | Ví dụ |
|---|---|---|
| `§X.Y (A–B)` | Mục X.Y trong `KE-HOACH-TONG-THE.md`, từ dòng A đến dòng B | `§7.4 (1007–1021)` |
| `§X (A–B)` | Toàn bộ mục X | `§12 (2105–2219)` |
| `→ đọc khi` | Thời điểm nên mở tài liệu | `→ đọc khi viết parser` |

**Nguyên tắc:**  
1. Làm theo checklist trước.  
2. Khi cần hiểu **vì sao** hoặc **chi tiết kỹ thuật**, mở đúng mục/dòng ở cột tham chiếu.  
3. Không đọc lại toàn bộ kế hoạch nếu chỉ cần một bước.  
4. Nếu số dòng lệch do file kế hoạch được sửa, dùng tên mục để tìm.

---

## Phase 0 — Data spike & pre-filter spec

> **Trạng thái cập nhật:** 2026-11-06  
> **Quy ước:** `[ ]` chưa làm · `[~]` đang làm / mới có code chưa chạy · `[x]` đã chạy và có artifact.  
> **Ghi chú:** checklist cũ ghi `spike_fetch.py`;implementation thực tế dùng `phase0/fetch.py` (client + smoke test).

### A. Setup & smoke test 6 endpoint

- [x] Tạo thư mục `phase0/data/raw/` (tự tạo khi chạy) và script client `phase0/fetch.py`.
- [x] Fetch list `PUBLIC` 1 trang, lưu raw. → 30 dòng, total live 8.969.
- [x] Fetch list `SIGNAL` 1 trang, lưu raw. → 30 dòng, total live 2.154.
- [x] Fetch detail trader `5296057151807357697` (audit fixture). → `ACTIVE`, `SIGNAL`.
- [x] Fetch performance 7D/30D/90D/180D bằng `BASE_P`. → đủ 4 window.
- [x] Fetch position-history (8 bản ghi). → `total=8`.
- [x] Fetch trade-history page 1 (200 bản ghi). → `total=5.292`, page 1 = 200.
- [x] Fetch transfer-history (17 bản ghi). → `total=17`.
- [x] Probe các endpoint không khả dụng: open positions, copier list, funding. → 6/6 trả 404.
- [x] Xác nhận `performance` dùng `BASE_P`, không 404.
- [x] Xác nhận page size list = 30, trade = 200.

### B. Universe & pre-filter

- [x] Chốt universe = PUBLIC + SIGNAL, bỏ PRIVATE mặc định. → live 8.970 PUBLIC + 2.154 SIGNAL = **11.124**.
- [x] Viết hàm `traded_last_7d` từ `chartItems`.
- [x] Viết pre-filter + tier C/B/A/Excluded (`phase0/tiering.py`). → kiểm tra trên snapshot cũ khớp 460/103/13.
- [x] Chốt preset AUM: Broad 1k / Balanced 5k / Strict 10k.
- [x] Chốt `pre_score` và thứ tự deep fetch. → dùng percentile, missing = 50 neutral.
- [x] Scan universe 90D thật, lưu `universe_90d.jsonl`. → **11.124 dòng, 100% coverage**, 0 page lỗi.
- [x] Kiểm tra counts: Watch 460/57, Qualified 103/10, High 13/0 (hoặc giải thích lệch).  
      → live: Watch **457 PUBLIC + 58 SIGNAL = 515**; Qualified gồm High **99 + 10 = 109**; High **13 + 0 = 13**.  
      → Lệch nhỏ so với snapshot 06/11 do list thay đổi; không ép số.
- [x] So sánh `traded_last_7d` với `lastTradeTime` trên 20 mẫu.  
      → Trên 63 mẫu: **60/63 khớp (95,2%)**, 3 false positive, **0 false negative**.  
      → Proxy không bỏ sót trader đang giao dịch, nhưng có thể giữ lại trader đã ngừng trade; cần xác nhận bằng `lastTradeTime` ở tầng deep fetch.

### C. Sample & deep fetch

- [x] Fetch **20 trader C + 20 trader B + 20 trader A + 10 excluded**, lưu JSONL/raw.  
      → Đã chọn **63 trader**: C=20, B=20, A=**13** (lấy toàn bộ vì high_upper chỉ có 13), excluded=10.  
      → `sample_manifest.csv` phủ đủ 8 lý do loại + trader mẫu bắt buộc.
- [x] Deep fetch 70 trader: detail + performance 4 windows + positions + transfers + trade page 1.  
      → Thực tế **63 trader**, 63/63 thành công, 153s, 0 endpoint lỗi.
- [x] Không lấy full trade-history cho bất kỳ trader nào trong Phase 0. → Chỉ page 1 (200 fill).
- [x] Không deep fetch trader excluded ngoài 10 mẫu + 50 audit. → Đúng 10 + 50.

### D. Audit & kiểm chứng

- [x] Audit false negative: 50 trader excluded → gọi performance/detail. → 50/50 thành công, 19,9s.
- [x] Tính false negative rate; đề xuất chỉnh ngưỡng nếu > 5%.  
      → **fn_watch_eligible = 0/50 (0%)** → không cần chỉnh ngưỡng.  
      → `fn_prompt` literal = 12/50 (24%) nhưng 12 ca này bị loại có chủ đích vì AUM < 5k hoặc MDD > 40.
- [x] Kiểm chứng MDD published vs MDD từ `chartItems`.  
      → **63/63 khớp** khi dùng `equity = 1 + value/100`; sai số tuyệt đối lớn nhất **4,9 × 10⁻⁷ pp**.  
      → Con số 88,67% trước đây là **lỗi công thức** (coi ROI lũy kế là equity), không phải lỗi dữ liệu.  
      → MDD **phụ thuộc window**: chỉ 6/63 trader giống nhau ở cả 4 window; chênh tối đa **70,26 pp**.  
      → Production vẫn dùng `performance.mdd`; tự tính chỉ để audit.
- [x] Kiểm chứng WinRate order vs position-level.  
      → 59/63 so sánh được; median lệch **2,52 pp**, max **33,33 pp**, **18 ca lệch > 5 pp**.  
      → `winRate` = `winOrders / totalOrder` khớp tuyệt đối; position-level là định nghĩa khác.
- [x] Kiểm chứng Sharpe null rate, AUM vs CopyAum, Copier PnL vs Lead PnL.  
      → Sharpe null: **34,9%** universe, **4,8%** sample.  
      → CopyAum/AUM median **0,2486**; **28/63** dưới 5%, **23/63** dưới 1%.  
      → CopierPnl/LeadPnl median **0,0002**; **35/63** dưới 1%; **17/63** copier PnL âm.
- [x] Kiểm chứng fee âm (rebate), `chartItems` length = 90, window equality khi runtime < 30.  
      → Fee âm: **56/58** trader có ít nhất 1 fill fee âm; tổng fee page 1 = **−5.835,4656**.  
      → `chartItems` = 90 điểm: **63/63** sample và **11.124/11.124** universe.  
      → Young portfolio: **1/2** có cả 4 window giống hệt; portfolio 29,98 ngày đã khác giữa các window.
- [x] Xác nhận không có open positions / per-copier / funding. → 6/6 endpoint probe trả 404.

### E. Đo lường & tài liệu

- [x] Đo rate limit: 1, 5, 10 request đồng thời.  
      → 32 request, **0 rate-limit, 0 lỗi**. Median: 1 worker ~650ms; 5 worker ~1,1–1,35s; 10 worker ~1,5–1,6s.
- [x] Đo thời gian: scan 11k, performance 517, detail 113–313, full trades 13.  
      → **Scan 11k: 78,0s** thực đo (371 trang, 6 worker, 0 lỗi).  
      → **Performance 517 trader**: 12 trader × 4 window = 9,51s → **~6,9 phút** cho 517 (6 worker).  
      → **Detail 113**: 20 trader = 4,06s → **~23s**; **detail 313 → ~64s**.  
      → **Full trades 13 High**: ước tính **~32s** cho 158 trang (dựa trên `total` page 1 của nhóm A).  
      → Không fetch full trade-history trader nào; chỉ ước tính từ `total`.
- [x] Viết `02-data-contract-binance.md` bản cuối. → đã đính chính MDD, bổ sung audit.
- [x] Cập nhật `data-availability-matrix.csv` nếu có field/giới hạn mới.  
      → Thêm: list thiếu `lastTradeTime`; `positionShow=false` không chặn position-history; `chartItems` 90 điểm; audit MDD.
- [x] Viết `phase0/PHASE0_REPORT.md`. → đầy đủ số liệu + gate.
- [x] Quyết định go/no-go. → **GO CÓ ĐIỀU KIỆN** (xem mục 9 của report).
- [x] Cập nhật `SESSION.md`. → tạo mới ở root, tóm tắt Phase 0.
- [x] Cập nhật lại chính `TASKS.md` sau mỗi mốc. → đã cập nhật trong suốt phiên.

**Gate:** 6 endpoint ổn định + 70 raw file + tiêu chí phễu + false negative < 5%.  
→ 6 endpoint: ✅ · raw: **63 trader** (A chỉ có 13, thiếu do cấu trúc) · phễu: ✅ · false negative: **0%** ✅.

---

## Phase 1 — Foundation + vertical slice — HOÀN THÀNH

**Mục tiêu:** một trader chạy end-to-end: collect → raw → quant → API → UI.  
**Thời lượng:** 5–7 ngày.

### Bước 1.1 — Khởi tạo repo & hạ tầng

**Tham chiếu:** §5.2 Stack (417–439) · §5.5 Cấu trúc repo (473–527) · §15.1 Topology (2921–2947) · §15.2 Biến môi trường (2948–2996)  
**→ đọc khi:** dựng khung dự án, Docker, cấu hình ban đầu.

- [x] Khởi tạo repo cho ca ma nguon, khong duoc tao cac folder tung buoc nhu folder phase0, `.gitignore`, `.env.example`. → Bằng chứng: `backend/`, `frontend/`, `infra/`, `.gitignore`, `.env.example`; không tạo `phase1/`.
- [x] `docker-compose.yml` với db/backend/frontend/nginx. → Bằng chứng: `docker compose config` OK; `docker compose up -d --build` OK.
- [x] FastAPI app + `/health`. → Bằng chứng: `GET http://localhost:8000/health` → `{"status":"ok","database":"ok"}`.
- [x] Config bằng Pydantic Settings. → Bằng chứng: `backend/app/core/config.py`.
- [x] SQLAlchemy async engine. → Bằng chứng: `backend/app/core/database.py`.
- [x] Alembic init + migration đầu. → Bằng chứng: `backend/alembic.ini`, `backend/migrations/`; `alembic upgrade head` OK.
- [x] CI tối thiểu: lint + typecheck + unit test. → Bằng chứng: `.github/workflows/ci.yml`; local `ruff` pass, `pytest` 1 pass, `npm run build` OK.

### Bước 1.2 — Database & model lõi

**Tham chiếu:** §10.1 Nhóm bảng (1615–1921) · §10.3 Index bắt buộc (1928–1940) · §10.4 Chống trùng & resume (1941–1952)  
**→ đọc khi:** viết migration/model, chọn kiểu dữ liệu, index.

- [x] Model `traders`. → Bằng chứng: `backend/app/models/trader.py`.
- [x] Model `portfolio_snapshots`. → Bằng chứng: `backend/app/models/snapshot.py`; unique `(lead_portfolio_id, collected_hour, source)`.
- [x] Model `performance_metrics`. → Bằng chứng: `backend/app/models/performance.py`; unique `(lead_portfolio_id, time_range, collected_at)`.
- [x] Model `users`. → Bằng chứng: `backend/app/models/user.py`; role check admin/viewer.
- [x] Unique constraint + index tối thiểu. → Bằng chứng: `ix_users_email`, `ix_traders_portfolio_type`, `ix_snapshots_lookup`, `ix_perf_lookup`.
- [x] Migration `upgrade` và `downgrade` chạy được. → Bằng chứng: `0001_core_tables`; downgrade base → upgrade head OK; `alembic current` = head.

### Bước 1.3 — Auth & RBAC

**Tham chiếu:** §15.8 Security checklist (3075–3095) · §11.1 Quy ước API (1982–2008)  
**→ đọc khi:** làm login/JWT/phân quyền.

- [x] Seed admin, login, JWT access/refresh. → Bằng chứng: `app/seed.py`, `app/services/auth.py`; smoke login admin OK; refresh rotate OK, refresh cũ bị 401.
- [x] RBAC `admin` / `viewer`, kiểm tra server-side. → Bằng chứng: `app/api/deps.py`; viewer gọi `/admin/ping` → 403.
- [x] Rate limit login 5/phút/IP. → Bằng chứng: `slowapi`; `scripts/test_rate_limit.ps1` → lần 6 = 429.
- [x] Không trả token/secret về browser ngoài access token cần thiết. → Bằng chứng: login chỉ trả access/refresh/user; không trả `password_hash`/`JWT_SECRET`.

### Bước 1.4 — Adapter + seed 2 trader

**Tham chiếu:** §12.1 Adapter interface (2107–2123) · §2.5 Sai lệch cần sửa (245–261) · §6.11 Bài học dữ liệu (897–973) · §7.4 Tiêu chí tier (1007–1021)  
**→ đọc khi:** viết `DataSourceAdapter`, seed fixture, xử lý null/zero.

- [x] `DataSourceAdapter` interface. → Bằng chứng: `backend/app/services/collector/base.py`.
- [x] `DemoAdapter` (và stub `CsvImportAdapter`). → Bằng chứng: `demo.py` 2 fixture; `csv_import.py` raise NotImplementedError.
- [x] Seed 1 trader excluded: `5296057151807357697`. → Bằng chứng: `python -m app.seed all`; `trader_universe.tier=excluded`, reasons runtime/aum.
- [x] Seed 1 trader qualified từ shortlist. → Bằng chứng: ID `4520644381136785152`; tier `qualified`; 4 window performance.
- [x] Mỗi bản ghi có `source`, `collected_at`, `window`. → Bằng chứng: snapshot/metric `raw` có `source=demo`, `collectedAt`, `window`.
- [x] API trả `null` đúng cho field thiếu, không trả `0`. → Bằng chứng: API excluded trả `mdd=null`, `sharpe=null`; smoke 1.5 pass.

### Bước 1.5 — API trader detail

**Tham chiếu:** §11.2 Trader & screener (2009–2049) · §8.2 10 chỉ số cốt lõi (1206–1220) · §8.9 Quy tắc missing/null (1438–1449)  
**→ đọc khi:** định nghĩa response, field null, tier/reason.

- [x] API `/api/v1/traders/{id}`. → Bằng chứng: `app/api/v1/traders.py`; smoke 200 cho qualified/excluded.
- [x] Trả 10 chỉ số + tier + confidence + provenance. → Bằng chứng: response có `metrics` 10 item, `tier`, `confidence`, `provenance`.
- [x] Trả lý do excluded/watch. → Bằng chứng: excluded trả `reasons=[runtime_lt_30,aum_lt_5000]`.
- [x] Không trả field không có nguồn. → Bằng chứng: field derived chưa có → `null` + flag `derived_unavailable`; không bịa giá trị.

### Bước 1.6 — Frontend tối giản

**Tham chiếu:** §13.2 Layout (2235–2254) · §13.4 Trader Detail (2345–2456) · §13.8 Component & style (2544–2576)  
**→ đọc khi:** dựng layout, trang detail, component.

- [x] Vite + React + TS + Tailwind. → Bằng chứng: `frontend/`; `npm run build` pass.
- [x] Layout + sidebar + topbar. → Bằng chứng: `src/components/Layout.tsx`; sidebar + freshness + user menu.
- [x] Login page. → Bằng chứng: `src/pages/LoginPage.tsx`; E2E đăng nhập OK.
- [x] Trader Detail tối giản: 10 chỉ số + tier. → Bằng chứng: `src/pages/TraderDetailPage.tsx`; E2E render qualified/excluded OK.
- [x] API client + TanStack Query. → Bằng chứng: `src/lib/api.ts`; `useQuery` trong detail.
- [x] Loading/error/empty state. → Bằng chứng: skeleton, error panel, empty/N/A handling.
- [x] Badge “Excluded” + lý do. → Bằng chứng: banner excluded + reasons map; E2E thấy “Runtime < 30 ngày”.

### Bước 1.7 — QA & gate Phase 1

**Tham chiếu:** §14.1 Test pyramid (2619–2631) · §14.6 Integration test (2789–2821) · §14.10 Acceptance MVP (2898–2918) · §22.4 Quy ước trạng thái (3564–3581)  
**→ đọc khi:** viết test, kiểm tra gate.

- [x] 3 unit test + 1 integration test. → Bằng chứng: `pytest` container: **12 passed** (11 unit + 1 integration API).
- [x] `docker compose up` chạy từ máy sạch. → Bằng chứng: `docker compose down -v` → `up -d --build` → 4 service healthy/chạy.
- [x] Đăng nhập được; viewer không vào trang admin. → Bằng chứng: `smoke_auth.ps1` PASS; viewer `/admin/ping` = 403.
- [x] Mở trader qualified thấy dữ liệu thật. → Bằng chứng: `smoke_trader.ps1` + E2E: tier qualified, ROI 19.19%, MDD 8.54%, Sharpe 2.84.
- [x] Mở trader excluded thấy badge + lý do. → Bằng chứng: E2E thấy banner excluded + `Runtime < 30 ngày`; MDD/Sharpe = null.
- [x] Không có secret trong repo. → Bằng chứng: `git ls-files` không có `.env`; `git check-ignore .env` OK; grep secret pattern 0 match.
- [x] `alembic downgrade` chạy được trên DB trống. → Bằng chứng: downgrade base → upgrade head trên volume mới; current = `0003_trader_universe`.

**Gate:** mở được trader thật end-to-end; API trả `null` đúng, không trả `0`.

---

## Phase 2 — Collector 2 tầng + raw storage

**Mục tiêu:** quét universe 11.124, tạo shortlist ~515, chỉ deep-fetch trader có tiềm năng.  
**Thời lượng:** 4–6 ngày.

### Bước 2.1 — Adapter đầy đủ 6 endpoint

**Tham chiếu:** §6.3 Danh sách endpoint (565–575) · §6.5 List (589–665) · §6.6 Detail (666–719) · §6.7 Performance (720–757) · §6.8 Position (758–810) · §6.9 Trade (811–860) · §6.10 Transfer (861–896) · §12.1 Adapter (2107–2123) · §12.3 Rate limit & retry (2136–2154)  
**→ đọc khi:** viết adapter/parser, xử lý page size, base URL, retry.

- [x] `BinanceBapiAdapter` list (page size 30). → Bằng chứng: `app/services/collector/binance.py`; live total PUBLIC=8966.
- [x] `BinanceBapiAdapter` detail. → Bằng chứng: live trader `4520644381136785152` status=ACTIVE, paused=False.
- [x] `BinanceBapiAdapter` performance (`BASE_P`, 4 window). → Bằng chứng: live 90D roi=19.22040291, mdd=8.5435368.
- [x] `BinanceBapiAdapter` position-history (page size 50). → Bằng chứng: `PAGE_SIZE_POSITIONS=50`; live total=1251.
- [x] `BinanceBapiAdapter` trade-history (page size 200). → Bằng chứng: `PAGE_SIZE_TRADES=200`; live total=2556.
- [x] `BinanceBapiAdapter` transfer-history. → Bằng chứng: page size 50; live total=2.
- [x] Retry/backoff `11012005`; timeout 20s. → Bằng chứng: `collector/http.py`; test retry 2 lần rồi success + test 500 retry + test 404 không retry.
- [x] Circuit breaker khi lỗi liên tiếp. → Bằng chứng: `CircuitBreaker(threshold=5, reset=60s)`; test mở sau 3 lỗi cấu hình.

### Bước 2.2 — Tầng 0: Universe scan

**Tham chiếu:** §7.1 Universe (976–986) · §7.2 Preset AUM (987–994) · §12.2 Chu kỳ thu thập (2124–2135) · §6.5 List trader (589–665)  
**→ đọc khi:** viết scan list, dedupe, snapshot.

- [x] Scan list PUBLIC + SIGNAL, **chỉ 90D**. → Bằng chứng: `services/universe.py`; live 372 trang, PUBLIC=8966, SIGNAL=2164, tổng 11.130.
- [x] Dedupe theo `leadPortfolioId`. → Bằng chứng: `dedupe()` + `seen_ids` toàn cục; live duplicates=0.
- [x] Lưu list snapshot + `collection_logs`. → Bằng chứng: 11.130 `portfolio_snapshots(source='list')`; 372 file JSONL `data/raw/.../list-public|signal`; `collection_logs.layer='L0'`.
- [x] Không gọi detail/position/trade ở tầng này. → Bằng chứng: adapter chỉ gọi `list_traders`; test mock assert 4 call list.
- [x] Redis lock chống 2 collector chạy song song. → Bằng chứng: `collector/lock.py`; integration test `test_lock_blocks_second_holder` pass; fallback advisory lock khi Redis lỗi.

### Bước 2.3 — Tầng 1: Pre-filter, tier, pre-score

**Tham chiếu:** §7.3 Các stage (995–1006) · §7.4 Tiêu chí tier (1007–1021) · §7.5 Mapping tier (1022–1032) · §7.6 Reason codes (1033–1047) · §7.7 Pre-score (1048–1068) · §7.12 Edge cases (1172–1186) · §12.7 Deep fetch selection (2182–2205)  
**→ đọc khi:** viết/sửa logic tier, reason, thứ tự deep fetch.

- [x] Hàm `traded_last_7d`. → Bằng chứng: `services/funnel.py`; proxy 8 điểm chartItems cuối.
- [x] Hàm `potential_tier`. → Bằng chứng: `evaluate_item()`; live `watch=398, qualified_upper=97, high_upper=14, excluded=10621`.
- [x] Hàm `pre_score`. → Bằng chứng: `annotate_pre_score()`; cohort chung `all` (Q02); live max 87.36.
- [x] Bảng `trader_universe` + `filter_reasons`. → Bằng chứng: 11.130 dòng; excluded có reasons (không tái diễn bug Phase 0).
- [x] Lưu lịch sử đổi tier (`tier_history`). → Bằng chứng: migration `0005`; test recompute lần 2 `changed=0`.
- [x] API `/universe/summary`. → Bằng chứng: live `total=11130, watch_total=509, qualified_total=111, high_total=14`.
- [x] API `/universe/traders`. → Bằng chứng: filter `tier=high` → 14; filter `reason=roi_le_0` → 6.989.
- [x] API `/universe/recompute` (admin). → Bằng chứng: chạy `python -m app.collector_cli recompute` 3,54s; viewer bị 403 (deps admin).

### Bước 2.4 — Tầng 2: Performance 4 window

**Tham chiếu:** §6.7 Performance (720–757) · §8.4 T1 Published metrics (1237–1262) · §15.4 Lịch chạy (3013–3028)  
**→ đọc khi:** gọi performance, lưu metric, xử lý null.

- [x] Gọi performance 4 window cho toàn bộ Watch (~515). → Bằng chứng: live 509 trader, 2.036 metric, 0 lỗi.
- [x] Lọc `totalOrder` theo tier. → Bằng chứng: HF04; 38 trader bị hạ tier (high→qualified, qualified→watch).
- [x] Lưu `performance_metrics` + provenance. → Bằng chứng: `raw.source=bapi`, `endpoint=performance`, `window`, `collectedAt`.
- [x] Sharpe null → `N/A`, không 0. → Bằng chứng: 90D có 9/509 sharpe null lưu `NULL`; test mdd null giữ null.

### Bước 2.5 — Tầng 3: Detail + positions + transfers

**Tham chiếu:** §6.6 Detail (666–719) · §6.8 Position history (758–810) · §6.10 Transfer history (861–896) · §7.11 Deep fetch policy (1157–1171) · §8.5 T2 Derived metrics (1263–1300)  
**→ đọc khi:** chọn trader deep fetch, parse position/transfer.

- [x] Gọi detail cho Qualified (~109) + top Watch (tối đa ~200) = ~109–309. → Bằng chứng: live 280 target (80 qualified/high + 200 watch), detail_ok=280.
- [x] Kiểm tra `status=ACTIVE`, `isPaused=false`. → Bằng chứng: `_is_eligible()`; live ineligible=0.
- [x] Kiểm tra `currentCopyCount < maxCopyCount`. → Bằng chứng: cùng hàm; test case full slot bị loại khỏi history.
- [x] Gọi position-history (không dựa vào `positionShow`). → Bằng chứng: live 71.026 vị thế; test `positionShow=false` vẫn gọi đủ trang.
- [x] Gọi transfer-history. → Bằng chứng: live 8.267 transfer.
- [x] Không gọi trade-history full ở tầng này. → Bằng chứng: L3 chỉ gọi detail/positions/transfers; trades=0 sau bước này.

### Bước 2.6 — Tầng 4: Full trade history

**Tham chiếu:** §6.9 Trade history (811–860) · §8.5 T2 Derived metrics (1263–1300) · §7.11 Deep fetch policy (1157–1171)  
**→ đọc khi:** fetch đủ trang, tính chỉ số trade-level.

- [x] Gọi full trade-history cho High (~13). → Bằng chứng: live 7 high_upper, full pages.
- [x] Gọi full trade-history cho top 30–50 Qualified. → Bằng chứng: live top 50 qualified.
- [x] Fetch đủ `total`, không break sớm. → Bằng chứng: `_fetch_pages` dừng khi `len >= total`; test 450 trade → 3 trang.
- [x] Không gọi cho Watch/Excluded. → Bằng chứng: query `trades ⋈ trader_universe` chỉ có high_upper (7) + qualified_upper (50); watch/excluded = 0.

### Bước 2.7 — Storage, scheduler, API vận hành

**Tham chiếu:** §10.4 Chống trùng (1941–1952) · §10.5 JSONL archive (1953–1960) · §10.6 Retention (1961–1979) · §12.4 Scheduler (2155–2161) · §12.5 Resume (2162–2172) · §12.6 Logs (2173–2181) · §12.8 Kill switch (2206–2219) · §15.4 Lịch chạy (3013–3028) · §11.4 Data health API (2058–2070)  
**→ đọc khi:** làm scheduler, raw archive, data health.

- [x] JSONL archive append-only; nén sau 7 ngày. → Bằng chứng: `storage/raw.py` `compress_older_than/purge_older_than`; 2 unit test pass; live 372 file / 144 MB.
- [x] Parser detail/performance/position/trade/transfer → DB. → Bằng chứng: `collector/parsers.py`; bảng positions/trades/transfers/performance_metrics đã có dữ liệu live.
- [x] Hash trade/transfer chống trùng. → Bằng chứng: unique `(lead, trade_hash)` / `(lead, transfer_hash)`; 10.367 bản ghi trùng bị loại khi chạy full trades.
- [x] `collection_logs` theo từng tầng. → Bằng chứng: log L0/L2/L3/L4 với pages/requests/items_ok/error_count/detail.
- [x] `data_quality_flags`. → Bằng chứng: migration `0007`; ghi `missing_sharpe`, `missing_mdd`, `low_sample` từ L2.
- [x] Scheduler 60 phút cho list scan. → Bằng chứng: `worker` service, `app/worker/scheduler.py`; test `due_jobs` pass.
- [x] Deep fetch scheduler riêng (6h/12h/24h). → Bằng chứng: `DEEP_INTERVAL_HOURS_WATCH/QUALIFIED/HIGH`; `intervals()`.
- [x] Advisory lock / Redis lock. → Bằng chứng: Redis lock + fallback advisory; job thật bị `skipped` khi worker đang giữ khóa.
- [x] API `/collector/status`. → Bằng chứng: trả tiers, latest_runs, jobs, raw_archive, enabled.
- [x] API `/collector/run-scan` (admin). → Bằng chứng: 202 + job; job success, scan 11.129 trader, watch 511.
- [x] API `/collector/run-deep` (admin). → Bằng chứng: 202 route; viewer 403; kill switch → 409 `COLLECTOR_DISABLED`.
- [x] UI Data Health theo tier. → Bằng chứng: `/data-health`; E2E thấy tier cards + bảng lần chạy.
- [x] Kill switch qua config. → Bằng chứng: env `COLLECTOR_KILL_SWITCH` + `POST /collector/kill-switch`; 409 khi tắt.

### Bước 2.8 — QA & gate Phase 2

**Tham chiếu:** §14.7 Data quality test (2822–2862) · §14.8 Performance test (2863–2877) · §14.10 Acceptance MVP (2898–2918)  
**→ đọc khi:** kiểm tra coverage, duplicate, resume, excluded.

- [ ] Scan đủ ≥ 99% của 11.124 trader trong 1 run.
- [ ] Shortlist Watch nằm trong **400–700**.
- [ ] Không có trader excluded nào bị deep fetch.
- [ ] Chạy lại 3 lần không duplicate.
- [ ] Restart giữa crawl resume được.
- [ ] Test rate limit/backoff (`11012005`).
- [ ] 1 chu kỳ list scan + deep fetch shortlist < 15 phút.
- [ ] Full-scale deep fetch ~515 đo được (không chỉ ngoại suy).

**Gate:** scan 11.124 ≥ 99%, shortlist 400–700, không deep fetch excluded, resume được.

---

## Phase 3 — Quant + Scoring + Screener

**Mục tiêu:** tính đủ chỉ số MVP, scoring v1.0, màn hình Screener dùng được.  
**Thời lượng:** 7–9 ngày.

### Bước 3.1 — Quant: published + derived metrics

**Tham chiếu:** §8.3 T0 Metadata (1221–1236) · §8.4 T1 Published (1237–1262) · §8.5 T2 Derived (1263–1300) · §8.6 T3 Unavailable (1301–1313) · §8.7 Công thức (1314–1410) · §8.8 Data Confidence (1411–1437) · §8.9 Missing/null (1438–1449)  
**→ đọc khi:** viết công thức, xử lý null/zero, confidence.

- [ ] ROI wrapper (4 window, giữ nguyên published).
- [ ] PnL wrapper.
- [ ] MDD wrapper (chỉ published).
- [ ] Sharpe wrapper (null handling).
- [ ] WinRate order + position tách biệt.
- [ ] Copier PnL.
- [ ] AUM / CopyAum.
- [ ] Runtime.
- [ ] Max/avg leverage.
- [ ] Margin mode.
- [ ] Holding time.
- [ ] Position win rate.
- [ ] Profit factor.
- [ ] Payoff ratio.
- [ ] Symbol concentration.
- [ ] Fee drag.
- [ ] Worst position ROI.
- [ ] Data confidence.
- [ ] Benchmark return.

### Bước 3.2 — Funnel & tier

**Tham chiếu:** §7.4 Tiêu chí tier (1007–1021) · §7.5 Mapping tier (1022–1032) · §7.6 Reason codes (1033–1047) · §7.7 Pre-score (1048–1068) · §7.10 Audit false negative (1123–1156) · §7.12 Edge cases (1172–1186) · §12.7 Deep fetch selection (2182–2205)  
**→ đọc khi:** chốt tier/reason, thứ tự ưu tiên, audit.

- [ ] `potential_tier` (excluded/watch/qualified/high).
- [ ] `pre_score`.
- [ ] `filter_reasons`.
- [ ] Tier history.
- [ ] Audit false negative (50 excluded).
- [ ] Chốt `mdd=None` và cohort `pre_score` (Q01/Q02, mục 20 dòng 3349–3379).

### Bước 3.3 — Risk rules

**Tham chiếu:** §9.7 Risk rules (1545–1572) · §8.5 T2 Derived metrics (1263–1300)  
**→ đọc khi:** viết R01–R11, severity, evidence.

- [ ] R01–R11.
- [ ] Evidence JSON.
- [ ] Risk level mapping.
- [ ] Không tạo risk event khi thiếu dữ liệu (dùng `unknown`).

### Bước 3.4 — Scoring & versioning

**Tham chiếu:** §9.1 Trọng số (1452–1464) · §9.2 Chuẩn hóa (1465–1488) · §9.3 Hard filters (1489–1502) · §9.4 Score bands (1503–1512) · §9.5 Score breakdown (1513–1536) · §9.6 Versioning (1537–1544)  
**→ đọc khi:** viết scoring, renormalize missing, version config.

- [ ] `scoring_config_versions`.
- [ ] Normalize percentile.
- [ ] Winsorize.
- [ ] Missing renormalize.
- [ ] Weight config.
- [ ] Hard filters.
- [ ] Score breakdown.
- [ ] `trader_scores`.
- [ ] `ranking_snapshots`.

### Bước 3.5 — Ranking 3 bảng

**Tham chiếu:** §9.8 Ranking boards (1573–1584) · §9.9 Ví dụ trader mẫu (1585–1612)  
**→ đọc khi:** định nghĩa Overall / Low Risk / Consistency.

- [ ] Overall.
- [ ] Low Risk.
- [ ] Consistency.
- [ ] Snapshot ranking theo `scoring_config_version`.
- [ ] Không có trader top chỉ vì ROI.

### Bước 3.6 — Screener API + UI

**Tham chiếu:** §11.2 Trader & screener API (2009–2049) · §13.3 Màn hình Screener (2255–2344) · §11.6 Thứ tự implement API (2085–2092)  
**→ đọc khi:** làm filter/sort/pagination, bảng, saved views.

- [ ] API `/traders` filter/sort/pagination + `potential_tier`.
- [ ] Filter bar.
- [ ] Tier column + tier filter.
- [ ] Funnel summary (Universe → Watch → Qualified → High).
- [ ] Table + virtualize.
- [ ] Count preview.
- [ ] Saved views.
- [ ] Export CSV.
- [ ] Score breakdown drawer.
- [ ] Empty state.
- [ ] Toggle “Include excluded” + lý do loại.

### Bước 3.7 — QA & gate Phase 3

**Tham chiếu:** §14.2 Golden dataset (2632–2648) · §14.3 Regression fixture (2649–2670) · §14.4 Unit test (2671–2748) · §14.10 Acceptance MVP (2898–2918)  
**→ đọc khi:** viết test công thức/scoring, kiểm tra gate.

- [ ] Golden dataset 12 archetype (gồm 2 excluded).
- [ ] Test trader mẫu → Excluded.
- [ ] Test missing data → không chấm 0.
- [ ] Test hard filter theo tier.
- [ ] Test pre-filter false negative.
- [ ] Test p95 shortlist ~700 (< 1s).
- [ ] Score breakdown khớp tổng điểm (sai số ≤ 0,01).
- [ ] Filter MDD ≤ 15 trả đúng (kiểm tra tay 10 dòng).

**Gate:** Screener shortlist ~700 dùng được; trader mẫu excluded không top; breakdown khớp.

---

## Phase 4 — Detail + Compare + Risk Monitor

**Mục tiêu:** trang chi tiết đủ sâu, so sánh 2–4 trader, risk monitor.  
**Thời lượng:** 5–7 ngày.

### Bước 4.1 — API detail mở rộng

**Tham chiếu:** §11.2 Trader & screener (2009–2049) · §11.3 Ranking & compare (2050–2057) · §11.6 Thứ tự implement API (2085–2092)  
**→ đọc khi:** thêm endpoint performance/positions/trades/transfers/risk/score.

- [ ] API `/traders/{id}/performance`.
- [ ] API `/traders/{id}/positions`.
- [ ] API `/traders/{id}/trades`.
- [ ] API `/traders/{id}/transfers`.
- [ ] API `/traders/{id}/risk`.
- [ ] API `/traders/{id}/score`.
- [ ] Phân trang + filter cho positions/trades.

### Bước 4.2 — Trader Detail UI

**Tham chiếu:** §13.4 Trader Detail (2345–2456) · §8.2 10 chỉ số cốt lõi (1206–1220) · §13.11 Checklist UI (2599–2616)  
**→ đọc khi:** dựng header, metric cards, chart, tooltip, empty state.

- [ ] Trader Detail header.
- [ ] 10 metric cards.
- [ ] ROI vs benchmark chart.
- [ ] Drawdown chart (có disclaimer “estimated”).
- [ ] Position PnL distribution.
- [ ] Score breakdown.
- [ ] Risk flags + evidence.
- [ ] What’s missing.
- [ ] Positions table.
- [ ] Trades summary.
- [ ] Transfers timeline.
- [ ] Tooltip definitions + nguồn + cửa sổ.
- [ ] Empty/loading/error.

### Bước 4.3 — Compare 2–4 trader

**Tham chiếu:** §13.5 Màn hình Compare (2457–2489) · §11.3 Ranking & compare (2050–2057)  
**→ đọc khi:** làm bảng so sánh, correlation, deep link.

- [ ] Compare page.
- [ ] Chọn 2–4 trader.
- [ ] Bảng so sánh.
- [ ] Chart so sánh.
- [ ] Correlation matrix + disclaimer “estimated”.
- [ ] Deep link/share URL.
- [ ] Responsive 1280px/1440px.

### Bước 4.4 — Risk Monitor

**Tham chiếu:** §9.7 Risk rules (1545–1572) · §13.4 Trader Detail (2345–2456)  
**→ đọc khi:** làm danh sách risk event, filter, evidence.

- [ ] Risk Monitor page.
- [ ] List event + filter severity/status.
- [ ] Mở evidence (trade/position/snapshot).
- [ ] Link từ Detail sang Risk Monitor.
- [ ] Không hiển thị open positions giả.

### Bước 4.5 — QA & gate Phase 4

**Tham chiếu:** §14.5 Contract test (2749–2788) · §14.10 Acceptance MVP (2898–2918) · §13.11 Checklist UI (2599–2616)  
**→ đọc khi:** kiểm tra contract, UI, evidence.

- [ ] Mỗi chỉ số có tooltip + nguồn + cửa sổ.
- [ ] Compare 4 trader không vỡ layout.
- [ ] Risk event mở được evidence.
- [ ] Không hiển thị open positions như thể có dữ liệu.
- [ ] Correlation có disclaimer “estimated”.
- [ ] Detail p95 < 300ms (cache) / < 1s (cold).
- [ ] Không có `undefined`/`NaN`/`null` lọt UI.

**Gate:** mỗi chỉ số có tooltip + nguồn; compare 4 trader không vỡ; risk evidence mở được.

---

## Phase 5 — AI + Settings + Hardening

**Mục tiêu:** AI report có kiểm soát, toàn bộ cấu hình chỉnh trên web, bảo mật cơ bản.  
**Thời lượng:** 5–7 ngày.

### Bước 5.1 — AI report có kiểm soát

**Tham chiếu:** §11.5 AI & settings API (2071–2084) · §13.7 Màn hình AI Report (2530–2543) · §3 D11 + D31 (277–316) · §15.2 Biến môi trường (2948–2996) · §16.3 Rủi ro sản phẩm (3169–3183)  
**→ đọc khi:** viết adapter/prompt/schema, evidence, cost control.

- [ ] Cấu hình OpenRouter trong `.env`: `OPENROUTER_API_KEY`, `AI_MODEL_PRIMARY`, `AI_MODEL_FALLBACK`.
- [ ] AI adapter gọi OpenRouter (OpenAI-compatible), dùng model chính.
- [ ] Fallback: lỗi/timeout/JSON invalid → thử model dự phòng 1 lần → template.
- [ ] Lưu model đã dùng (primary/fallback), cost, latency vào report metadata.
- [ ] Không log/không trả `OPENROUTER_API_KEY` về browser.
- [ ] Prompt template + JSON schema.
- [ ] Evidence IDs bắt buộc cho mọi nhận định.
- [ ] Chỉ nhận dữ liệu đã chuẩn hóa, không nhận raw trade.
- [ ] Cost tracking.
- [ ] Budget ngày/tháng.
- [ ] Cooldown 24h + dedupe input hash.
- [ ] Fallback template cuối cùng khi cả 2 model đều lỗi.
- [ ] AI Reports UI.
- [ ] Nút Analyze trên Detail.
- [ ] AI không sửa score/ranking.

### Bước 5.2 — Settings & versioning

**Tham chiếu:** §9.6 Versioning (1537–1544) · §11.5 AI & settings API (2071–2084) · §13.6 Settings & Data Health (2490–2529)  
**→ đọc khi:** làm form cấu hình, preview impact, rollback.

- [ ] Data Collection tab.
- [ ] Data Health tab.
- [ ] Scoring tab + preview impact.
- [ ] Risk Rules tab.
- [ ] AI tab: OpenRouter key (masked), `AI_MODEL_PRIMARY`, `AI_MODEL_FALLBACK`, budget.
- [ ] Ranking tab.
- [ ] Version + audit + rollback.
- [ ] Validation + confirm khi thay đổi ảnh hưởng ranking.

### Bước 5.3 — Hardening

**Tham chiếu:** §15.3 Quy trình deploy (2997–3012) · §15.5 Backup & restore (3029–3043) · §15.6 Monitoring (3044–3059) · §15.8 Security checklist (3075–3095)  
**→ đọc khi:** mã hóa secret, rate limit, backup, alert.

- [ ] Mã hóa API key at rest.
- [ ] Không trả API key về browser.
- [ ] Rate limit login/API.
- [ ] Backup script.
- [ ] Restore test trên staging.
- [ ] Prometheus metrics.
- [ ] Alert rules.
- [ ] Security headers + CORS production.
- [ ] Dependency scan (`pip-audit`, `npm audit`).

### Bước 5.4 — QA & gate Phase 5

**Tham chiếu:** §14.9 Security checklist (2878–2897) · §14.10 Acceptance MVP (2898–2918) · §15.8 Security checklist (3075–3095)  
**→ đọc khi:** kiểm tra AI/evidence, settings rollback, bảo mật.

- [ ] AI không sửa score.
- [ ] AI trả JSON hợp lệ hoặc fallback template.
- [ ] Không có report nào không có evidence.
- [ ] Đổi trọng số tạo version mới; score cũ giữ nguyên.
- [ ] API key không trả về browser/network response.
- [ ] Rollback hoạt động + audit log.
- [ ] Login sai 6 lần bị rate limit.
- [ ] Backup restore thành công.

**Gate:** AI không sửa score; settings version hóa; backup restore OK.

---

## Phase 6 — Testing + Deploy + Beta

**Mục tiêu:** MVP chạy VPS, có monitoring, có beta user.  
**Thời lượng:** 4–6 ngày.

### Bước 6.1 — Test toàn bộ

**Tham chiếu:** §14.1 Test pyramid (2619–2631) · §14.2 Golden dataset (2632–2648) · §14.5 Contract test (2749–2788) · §14.6 Integration test (2789–2821) · §14.8 Performance test (2863–2877) · §14.10 Acceptance MVP (2898–2918)  
**→ đọc khi:** chạy full suite, load test, regression.

- [ ] Chạy full test suite (unit + integration + contract + E2E).
- [ ] Load test shortlist ~700 + filter phức tạp.
- [ ] Test restart giữa crawl.
- [ ] Test backup/restore.
- [ ] Test rate limit/backoff.
- [ ] Test trader excluded không bị deep fetch.
- [ ] Test null/zero hiển thị đúng.

### Bước 6.2 — Deploy VPS

**Tham chiếu:** §15.1 Topology (2921–2947) · §15.2 Biến môi trường (2948–2996) · §15.3 Quy trình deploy (2997–3012) · §15.4 Lịch chạy (3013–3028)  
**→ đọc khi:** dựng VPS, Nginx, TLS, migration, rollback.

- [ ] Deploy VPS.
- [ ] Nginx + TLS + HSTS.
- [ ] Firewall chỉ 22/80/443.
- [ ] `alembic upgrade head` + smoke test.
- [ ] Rollback image hoạt động.
- [ ] Log dashboard.

### Bước 6.3 — Monitoring & vận hành

**Tham chiếu:** §15.5 Backup & restore (3029–3043) · §15.6 Monitoring & alert (3044–3059) · §15.7 Runbook sự cố (3060–3074) · §15.10 Tài liệu vận hành (3107–3115)  
**→ đọc khi:** đặt alert, viết runbook, kiểm tra backup.

- [ ] Alert collector fail/stale/disk/AI budget/5xx.
- [ ] Backup daily + retention 7 daily/4 weekly.
- [ ] Test restore < 30 phút.
- [ ] Viết runbook.
- [ ] Viết deployment doc.
- [ ] Viết data-quality doc.

### Bước 6.4 — Beta & feedback

**Tham chiếu:** §4.4 Tiêu chí thành công MVP (356–384) · §21 Việc cần làm ngay (3385–3483) · §18 Backlog v1.1 (3291–3319)  
**→ đọc khi:** chuẩn bị beta, thu feedback, chốt backlog.

- [ ] Beta 3–5 user.
- [ ] Thu feedback có cấu trúc.
- [ ] Chốt backlog v1.1 từ feedback.
- [ ] Cập nhật `SESSION.md`.
- [ ] Ghi lại bug/khác biệt phát hiện trong beta.

### Bước 6.5 — Gate Phase 6

**Tham chiếu:** §14.10 Acceptance MVP (2898–2918) · §15.8 Security checklist (3075–3095)  
**→ đọc khi:** nghiệm thu cuối.

- [ ] Uptime 7 ngày không crash nghiêm trọng.
- [ ] Collector chạy đủ 7 ngày, freshness < 150 phút.
- [ ] Backup restore thành công.
- [ ] Không có lỗi bảo mật nghiêm trọng.
- [ ] ≥ 3 người dùng thử và phản hồi.
- [ ] Không còn `[!]` blocking trong mục 20.

**Gate:** uptime 7 ngày, collector đủ 7 ngày, beta feedback.

---

## Definition of Done (mỗi phase)

**Tham chiếu:** §22.4 Quy ước trạng thái & quản trị (3564–3581) · §14.10 Acceptance MVP (2898–2918)

Một phase chỉ được coi là xong khi:

- [ ] Code chạy được, không lỗi nghiêm trọng; `main` build xanh.
- [ ] Unit test cho logic mới; integration test cho luồng chính.
- [ ] Không có TODO nghiêm trọng (hoặc có issue link).
- [ ] API/schema được cập nhật trong docs.
- [ ] `SESSION.md` ghi quyết định + việc còn lại.
- [ ] Không có secret/API key trong repo.
- [ ] Acceptance criteria của phase đạt và có bằng chứng (log/screenshot/số đo).
- [ ] Có ít nhất 1 người review hoặc self-review checklist.
- [ ] Dữ liệu demo/seed tái tạo được từ script.

---

## Phụ thuộc & đường găng

**Tham chiếu:** §5.4 Luồng xử lý (454–472) · §12.2 Chu kỳ thu thập (2124–2135)

```text
Phase 0 (đã xong)
   └─► Phase 1 (DB + auth + 1 trader E2E)
          ├─► Phase 2 (collector 2 tầng) ─► Phase 3 (quant + scoring + screener)
          │                                        ├─► Phase 4 (detail + compare + risk)
          │                                        └─► Phase 5 (AI + settings)
          └────────────────────────────────────────────► Phase 6 (test + deploy + beta)
```

| Phụ thuộc | Bị chặn nếu |
|---|---|
| Phase 1 → 2 | Schema `traders`/`performance_metrics` chưa chốt |
| Phase 2 → 3 | Chưa có dữ liệu performance 4 window cho Watch |
| Phase 3 → 4 | Chưa có score breakdown/risk events API |
| Phase 4 → 5 | Chưa có evidence IDs cho AI |
| Phase 5 → 6 | Chưa có config version/rollback |
| Phase 0 → tất cả | Còn `[!]` về `mdd=None`/cohort `pre_score` (mục 20, dòng 3349–3379) |

---

## Lịch tuần gợi ý (full-time)

| Tuần | Việc chính | Mốc kiểm tra |
|---:|---|---|
| 0 | Đóng Phase 0 (bug + quyết định + report) | `PHASE0_REPORT.md`, gate pass |
| 1 | Phase 1 | `docker compose up`, login, 2 trader E2E |
| 2 | Phase 2 | Scan 11k + shortlist 400–700 |
| 3 | Phase 3 | Screener + scoring + 3 ranking |
| 4 | Phase 3 hoàn thiện + Phase 4 | Detail + compare chạy |
| 5 | Phase 4 + Phase 5 | Risk monitor + AI report |
| 6 | Phase 5 + Phase 6 | Settings/rollback + deploy staging |
| 7 | Beta + sửa lỗi | 3–5 user feedback |
| 8 | Buffer / v1.1 | Retro + backlog |

**Part-time:** mỗi tuần gấp đôi. **Nếu chỉ có 10h/tuần:** 14–18 tuần.

---

## Backlog v1.1

Không đưa vào MVP. Danh sách đầy đủ + ưu tiên + phụ thuộc:

**→ §18 Backlog v1.1 (dòng 3286–3314)**

Tóm tắt ưu tiên: Watchlist/alert (B01), lịch sử ranking (B02), export PDF (B03), DCA/martingale (B07).  
Paper Copy (B08) chỉ làm khi dữ liệu đủ tốt và ghi rõ “estimated”.

---

## Việc không làm (non-goals)

**→ §19 Việc không làm (dòng 3315–3348)**

Tóm tắt: không auto-trading, không realtime WebSocket, không Paper Copy trong MVP, không per-copier analytics, không open positions giả, không funding drag chính xác, không mobile app, không microservices, không 6 bảng ranking.

---

## Quy tắc cập nhật file này

1. Đây là **nguồn tiến độ thực thi**. `KE-HOACH-TONG-THE.md` là nguồn quyết định/kiến trúc.
2. Mỗi task xong → đổi `[ ]` → `[x]` và ghi bằng chứng ngắn (file/log/số đo).
3. Task bị chặn → `[!]` + lý do + người/quyết định cần gỡ.
4. Task mới phát sinh → thêm vào đúng bước; nếu ảnh hưởng kiến trúc, cập nhật master trước.
5. Khi master đổi số dòng → cập nhật lại cột tham chiếu; nếu không, dùng tên mục để tra.
6. Cuối mỗi phase → cập nhật bảng tổng quan + gate + `SESSION.md`.
