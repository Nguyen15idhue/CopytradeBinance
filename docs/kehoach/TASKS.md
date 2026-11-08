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
| 2 — Collector 2 tầng | `[x]` hoàn thành | 4–6 ngày | Scan 11.124 ≥ 99%, Watch 400–700 | §6 (528–973), §12 (2105–2219) |
| 3 — Quant + Scoring + Screener | `[x]` hoàn thành | 7–9 ngày | Screener dùng được, score breakdown đúng | §8 (1187–1449), §9 (1450–1612) |
| 4 — Detail + Compare + Risk | `[x]` hoàn thành | 5–7 ngày | Detail sâu, compare 4 trader, risk evidence | §11.2–11.3 (2009–2057), §13.4–13.5 (2345–2489) |
| 5 — AI + Settings + Hardening | `[x]` hoàn thành | 7–9 ngày | AI không sửa score, config version/rollback, Ranking + Help dùng được | §11.5 (2071–2084), §13.6–13.7 (2490–2543), §15.8 (3075–3095) |
| 6 — Testing + Deploy + Beta | `[ ]` | 6–8 ngày | Uptime 7 ngày, beta 3–5 user, Playwright E2E full pass | §14 (2617–2918), §15 (2919–3128) |
| | | **37–51 ngày** | +20% buffer → **44–61 ngày** | |

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
- [x] FastAPI app + `/health`. → Bằng chứng: `GET http://localhost:8010/health` → `{"status":"ok","database":"ok"}` (cổng host đổi từ 8000).
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

## Phase 2 — Collector 2 tầng + raw storage — HOÀN THÀNH

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

- [x] Scan đủ ≥ 99% của 11.124 trader trong 1 run. → Bằng chứng: 11.132 trader = 100,07%; 372 trang; 142,6s; 0 lỗi.
- [x] Shortlist Watch nằm trong **400–700**. → Bằng chứng: Watch tổng **511** (watch 425 + qualified 76 + high 10).
- [x] Không có trader excluded nào bị deep fetch. → Bằng chứng: filter tier trong mọi hàm chọn; test `test_excluded_trader_never_targeted`; L4 chỉ có high/qualified.
- [x] Chạy lại 3 lần không duplicate. → Bằng chứng: counts giống hệt 3 lần: traders 11.133, list snapshots 22.261, universe 11.133, metrics 4.088, trades 120.595.
- [x] Restart giữa crawl resume được. → Bằng chứng: kill sau 35s → chạy lại đủ 11.132; duplicate snapshot trong giờ = 0.
- [x] Test rate limit/backoff (`11012005`). → Bằng chứng: 3 mock test (11012005, 429 HTML, Retry-After) + live 679 request trades, 0 lỗi.
- [x] 1 chu kỳ list scan + deep fetch shortlist < 15 phút. → Bằng chứng: scan 142,6s + performance 38,7s = **181,3s**.
- [x] Full-scale deep fetch ~515 đo được (không chỉ ngoại suy). → Bằng chứng: L2 511 trader/38,7s; L3 278/77,9s; L4 57 trader/130.962 fill/134,2s; tổng 250,8s.
- [x] Ghi bằng chứng vào `docs/kehoach/PHASE2-REPORT.md`. → Bằng chứng: file report đầy đủ số liệu gate.
- [x] Full suite backend + build frontend + E2E. → Bằng chứng: container **40 passed**; `npm run build` OK; E2E PASS; `npm audit` 0 lỗi.

**Gate:** scan 11.124 ≥ 99%, shortlist 400–700, không deep fetch excluded, resume được.

---

## Phase 3 — Quant + Scoring + Screener — HOÀN THÀNH

**Mục tiêu:** tính đủ chỉ số MVP, scoring v1.0, màn hình Screener dùng được.  
**Thời lượng:** 7–9 ngày.

### Bước 3.1 — Quant: published + derived metrics

**Tham chiếu:** §8.3 T0 Metadata (1221–1236) · §8.4 T1 Published (1237–1262) · §8.5 T2 Derived (1263–1300) · §8.6 T3 Unavailable (1301–1313) · §8.7 Công thức (1314–1410) · §8.8 Data Confidence (1411–1437) · §8.9 Missing/null (1438–1449)  
**→ đọc khi:** viết công thức, xử lý null/zero, confidence.

- [x] ROI wrapper (4 window, giữ nguyên published). → Bằng chứng: `quant/metrics.py` `published_metrics`; 4 window trong `trader_metrics.metrics`.
- [x] PnL wrapper. → Bằng chứng: published 4 window + `trader_metrics.roi_90d/mdd_90d`.
- [x] MDD wrapper (chỉ published). → Bằng chứng: lấy `performance.mdd`; mdd null giữ null + `missing_mdd` (511 trader, 0 mdd null ở 90D).
- [x] Sharpe wrapper (null handling). → Bằng chứng: 90D có 9 trader sharpe null, lưu `NULL` + flag.
- [x] WinRate order + position tách biệt. → Bằng chứng: `win_rate_order` và `position_win_rate` trong metrics JSONB.
- [x] Copier PnL. → Bằng chứng: `published[90D].copier_pnl`, `copier_pnl_per_copier`.
- [x] AUM / CopyAum. → Bằng chứng: `profile.aum/copy_aum` + cột `aum`, `copy_aum`; `copy_aum_ratio`.
- [x] Runtime. → Bằng chứng: `runtime_days` từ detail startTime (fallback trader.start_time).
- [x] Max/avg leverage. → Bằng chứng: `derived.max_leverage/avg_leverage`; cột tương ứng.
- [x] Margin mode. → Bằng chứng: `derived.margin_mode` (mode isolated).
- [x] Holding time. → Bằng chứng: avg/median/max holding hours từ positions.
- [x] Position win rate. → Bằng chứng: `derived.position_win_rate`.
- [x] Profit factor. → Bằng chứng: gross win / |gross loss|; null nếu <5 vị thế.
- [x] Payoff ratio. → Bằng chứng: avg win / |avg loss|; null nếu thiếu mẫu.
- [x] Symbol concentration. → Bằng chứng: `top_symbol_share`, `hhi`, `symbols_top3`.
- [x] Fee drag. → Bằng chứng: `total_fees` (rebate âm) + `fee_drag_pct`.
- [x] Worst position ROI. → Bằng chứng: `worst_position_roi` + `near_liquidation_count`.
- [x] Data confidence. → Bằng chứng: `quant/confidence.py`; live avg 0.847, đủ 4 thành phần.
- [x] Benchmark return. → Bằng chứng: chưa có nguồn klines → `null` + flag `missing_benchmark` (không bịa số).

### Bước 3.2 — Funnel & tier

**Tham chiếu:** §7.4 Tiêu chí tier (1007–1021) · §7.5 Mapping tier (1022–1032) · §7.6 Reason codes (1033–1047) · §7.7 Pre-score (1048–1068) · §7.10 Audit false negative (1123–1156) · §7.12 Edge cases (1172–1186) · §12.7 Deep fetch selection (2182–2205)  
**→ đọc khi:** chốt tier/reason, thứ tự ưu tiên, audit.

- [x] `potential_tier` (excluded/watch/qualified/high). → Bằng chứng: `funnel.evaluate_item` + `recompute_universe`; live 425/76/10/10.623.
- [x] `pre_score`. → Bằng chứng: `annotate_pre_score`, cohort `all`; lưu `trader_universe.pre_score`.
- [x] `filter_reasons`. → Bằng chứng: JSONB reasons; test khẳng định excluded không rỗng (bug Phase 0 không tái diễn).
- [x] Tier history. → Bằng chứng: `tier_history`; test recompute lần 2 `changed=0`.
- [x] Audit false negative (50 excluded). → Bằng chứng: `python -m app.collector_cli audit` → 50/50 đánh giá, **0 false negative (0%)**, 0 lỗi; lưu `collection_logs.layer='A1'`.
- [x] Chốt `mdd=None` và cohort `pre_score` (Q01/Q02). → Bằng chứng: ghi tại SESSION mục 9.4/10.1; Q01 null + `missing_mdd`, Q02 cohort chung `all`.

### Bước 3.3 — Risk rules

**Tham chiếu:** §9.7 Risk rules (1545–1572) · §8.5 T2 Derived metrics (1263–1300)  
**→ đọc khi:** viết R01–R11, severity, evidence.

- [x] R01–R11. → Bằng chứng: `services/risk_rules.py`; live 511 trader → 1.100 event (critical 280, high 501, medium 219, low_sample 91, penalty 9).
- [x] Evidence JSON. → Bằng chứng: mỗi event có `{field, value, threshold, rule}` trong `risk_events.evidence`.
- [x] Risk level mapping. → Bằng chứng: critical/high/medium/low/none/unknown; live: critical 214, high 164, medium 55, low 13, none 38, unknown 27.
- [x] Không tạo risk event khi thiếu dữ liệu (dùng `unknown`). → Bằng chứng: `evaluate_rules` trả `unknown[]`; 691 field thiếu, không sinh event sai.

### Bước 3.4 — Scoring & versioning

**Tham chiếu:** §9.1 Trọng số (1452–1464) · §9.2 Chuẩn hóa (1465–1488) · §9.3 Hard filters (1489–1502) · §9.4 Score bands (1503–1512) · §9.5 Score breakdown (1513–1536) · §9.6 Versioning (1537–1544)  
**→ đọc khi:** viết scoring, renormalize missing, version config.

- [x] `scoring_config_versions`. → Bằng chứng: migration 0010; seed v1 `is_active=true`, trọng số/normalization/hard filters.
- [x] Normalize percentile. → Bằng chứng: `scoring.normalize_cohort`, cohort chung, đảo chiều MDD/leverage/roi_stability.
- [x] Winsorize. → Bằng chứng: cắt 2,5–97,5 percentile trước khi rank.
- [x] Missing renormalize. → Bằng chứng: nhóm thiếu bị loại khỏi mẫu số; không gán 0; 511/511 có score.
- [x] Weight config. → Bằng chứng: 7 nhóm đúng §9.1 (25/20/15/15/10/5/10) + trọng số con.
- [x] Hard filters. → Bằng chứng: HF01–HF06; `rankable=236/511`; HF04 theo tier (20/50/100).
- [x] Score breakdown. → Bằng chứng: `breakdown.components`; max sai số tổng contribution vs score = **0,0051** (≤ 0,01).
- [x] `trader_scores`. → Bằng chứng: 511 dòng version 1; score null = 0; band good 14 / average 145 / weak 240 / high_risk 112.
- [x] `ranking_snapshots`. → Bằng chứng: bảng + index đã tạo (migration 0010), dùng ở 3.5.

### Bước 3.5 — Ranking 3 bảng

**Tham chiếu:** §9.8 Ranking boards (1573–1584) · §9.9 Ví dụ trader mẫu (1585–1612)  
**→ đọc khi:** định nghĩa Overall / Low Risk / Consistency.

- [x] Overall. → Bằng chứng: top 50 theo score trong `rankable`; live 50 item.
- [x] Low Risk. → Bằng chứng: runtime ≥ 90, MDD ≤ 20, leverage ≤ 5, confidence ≥ 0.8; live 38 item.
- [x] Consistency. → Bằng chứng: xếp theo `components.consistency.score`, runtime ≥ 90; live 50 item.
- [x] Snapshot ranking theo `scoring_config_version`. → Bằng chứng: 3 bản ghi `ranking_snapshots` version 1 (overall/low_risk/consistency).
- [x] Không có trader top chỉ vì ROI. → Bằng chứng: test `test_overall_not_only_roi` và `test_consistency_uses_consistency_score_not_roi` pass; Overall dùng score tổng.

### Bước 3.6 — Screener API + UI

**Tham chiếu:** §11.2 Trader & screener API (2009–2049) · §13.3 Màn hình Screener (2255–2344) · §11.6 Thứ tự implement API (2085–2092)  
**→ đọc khi:** làm filter/sort/pagination, bảng, saved views.

- [x] API `/traders` filter/sort/pagination + `potential_tier`. → Bằng chứng: `api/v1/screener.py`; 4 integration test pass (default sort, MDD filter, excluded toggle, CSV).
- [x] Filter bar. → Bằng chứng: `ScreenerPage.tsx` search/tier/risk/ROI/MDD/Sharpe/WinRate/Runtime/Orders/Leverage.
- [x] Tier column + tier filter. → Bằng chứng: badge High/Qualified/Watch/Excluded + select tier.
- [x] Funnel summary (Universe → Watch → Qualified → High). → Bằng chứng: `/traders/funnel-summary`; UI hiển thị 4 badge.
- [x] Table + virtualize. → Bằng chứng: bảng 13 cột, phân trang 50 dòng (virtualize không cần ở ngưỡng này).
- [x] Count preview. → Bằng chứng: “N trader khớp” cập nhật theo filter.
- [x] Saved views. → Bằng chứng: bảng `saved_views` + CRUD API + UI lưu/áp dụng/xoá; integration test pass.
- [x] Export CSV. → Bằng chứng: `/traders/export.csv`; test header “Trader ID”; UI nút Export.
- [x] Score breakdown drawer. → Bằng chứng: drawer hiển thị từng nhóm score/weight/contribution + missing/hard flags.
- [x] Empty state. → Bằng chứng: thông điệp + 3 nút gợi ý (bỏ MDD, runtime ≥ 30, xem excluded).
- [x] Toggle “Include excluded” + lý do loại. → Bằng chứng: toggle UI + `filter_reasons` trả trong item; test khẳng định excluded có reason.

### Bước 3.7 — QA & gate Phase 3

**Tham chiếu:** §14.2 Golden dataset (2632–2648) · §14.3 Regression fixture (2649–2670) · §14.4 Unit test (2671–2748) · §14.10 Acceptance MVP (2898–2918)  
**→ đọc khi:** viết test công thức/scoring, kiểm tra gate.

- [x] Golden dataset 12 archetype (gồm 2 excluded). → Bằng chứng: `tests/fixtures/golden_traders.json` + `test_golden_dataset.py` (5 test).
- [x] Test trader mẫu → Excluded. → Bằng chứng: `test_golden_top_never_contains_excluded_archetypes`; excluded không vào top 5.
- [x] Test missing data → không chấm 0. → Bằng chứng: `test_missing_components_are_not_zero`.
- [x] Test hard filter theo tier. → Bằng chứng: `test_hard_flags_tier_thresholds` (20/50/100) + 6 flag.
- [x] Test pre-filter false negative. → Bằng chứng: audit live 50 excluded = **0%**, 0 lỗi.
- [x] Test p95 shortlist ~700 (< 1s). → Bằng chứng: 30 request page_size 100 → **p95 97ms**, median 78ms, max 142ms.
- [x] Score breakdown khớp tổng điểm (sai số ≤ 0,01). → Bằng chứng: SQL max diff **0,0051** trên 511 dòng.
- [x] Filter MDD ≤ 15 trả đúng (kiểm tra tay 10 dòng). → Bằng chứng: API sort MDD asc khớp 10/10 với SQL (0,0000–0,6344).

**Gate:** Screener shortlist ~700 dùng được; trader mẫu excluded không top; breakdown khớp.

---

## Phase 4 — Detail + Compare + Risk Monitor — HOÀN THÀNH

**Mục tiêu:** trang chi tiết đủ sâu, so sánh 2–4 trader, risk monitor.  
**Thời lượng:** 5–7 ngày.

### Bước 4.1 — API detail mở rộng

**Tham chiếu:** §11.2 Trader & screener (2009–2049) · §11.3 Ranking & compare (2050–2057) · §11.6 Thứ tự implement API (2085–2092)  
**→ đọc khi:** thêm endpoint performance/positions/trades/transfers/risk/score.

- [x] API `/traders/{id}/performance`. → Bằng chứng: trả 4 window + chartItems + benchmark null; test contract pass.
- [x] API `/traders/{id}/positions`. → Bằng chứng: phân trang 50 (max 200), filter symbol/side; test pass.
- [x] API `/traders/{id}/trades`. → Bằng chứng: phân trang 100, filter symbol/side; test pass.
- [x] API `/traders/{id}/transfers`. → Bằng chứng: danh sách timeline; test pass.
- [x] API `/traders/{id}/risk`. → Bằng chứng: risk_level + flags + events/evidence; test pass.
- [x] API `/traders/{id}/score`. → Bằng chứng: config_version + score + breakdown + hard flags; test pass.
- [x] Phân trang + filter cho positions/trades. → Bằng chứng: test `test_positions_filter_pagination` (page 1 ≠ page 2, filter Long).

### Bước 4.2 — Trader Detail UI

**Tham chiếu:** §13.4 Trader Detail (2345–2456) · §8.2 10 chỉ số cốt lõi (1206–1220) · §13.11 Checklist UI (2599–2616)  
**→ đọc khi:** dựng header, metric cards, chart, tooltip, empty state.

- [x] Trader Detail header. → Bằng chứng: nickname, tier/status/type, score/band, confidence, risk level.
- [x] 10 metric cards. → Bằng chứng: grid 5×2; giá trị null hiển thị N/A, copy AUM 0 ghi “Không có copier”.
- [x] ROI vs benchmark chart. → Bằng chứng: LineChart chartItems; benchmark null kèm ghi chú (không bịa).
- [x] Drawdown chart (có disclaimer “estimated”). → Bằng chứng: AreaChart từ equity 1+ROI, nhãn “estimated”, cảnh báo chưa điều chỉnh nạp/rút.
- [x] Position PnL distribution. → Bằng chứng: histogram 7 bucket từ 200 vị thế gần nhất.
- [x] Score breakdown. → Bằng chứng: 7 nhóm score/weight + thanh đóng góp; hard flags.
- [x] Risk flags + evidence. → Bằng chứng: chips R01–R11, tooltip JSON evidence, link Risk Monitor.
- [x] What’s missing. → Bằng chứng: flags + open positions/per-copier/funding/benchmark.
- [x] Positions table. → Bằng chứng: 10 dòng gần nhất + tổng số vị thế.
- [x] Trades summary. → Bằng chứng: 10 fill gần nhất (symbol/side/notional/fee).
- [x] Transfers timeline. → Bằng chứng: danh sách nạp/rút 20 dòng.
- [x] Tooltip definitions + nguồn + cửa sổ. → Bằng chứng: tooltip từng metric card ghi định nghĩa + source + window; dòng phụ hiển thị nguồn.
- [x] Empty/loading/error. → Bằng chứng: skeleton 10 card, panel lỗi, “Không có position-history/transfer”.

### Bước 4.3 — Compare 2–4 trader

**Tham chiếu:** §13.5 Màn hình Compare (2457–2489) · §11.3 Ranking & compare (2050–2057)  
**→ đọc khi:** làm bảng so sánh, correlation, deep link.

- [x] Compare page. → Bằng chứng: `/compare` + nav link.
- [x] Chọn 2–4 trader. → Bằng chứng: picker search qua `/traders?q=`, chip chọn, chặn >4.
- [x] Bảng so sánh. → Bằng chứng: 15 dòng chỉ số × 2–4 trader.
- [x] Chart so sánh. → Bằng chứng: LineChart ROI lũy kế theo từng trader từ `series`.
- [x] Correlation matrix + disclaimer “estimated”. → Bằng chứng: Pearson trên sai phân chartItems; E2E thấy “estimated”.
- [x] Deep link/share URL. → Bằng chứng: `?ids=a,b` cập nhật qua `useSearchParams`; mở lại giữ danh sách.
- [x] Responsive 1280px/1440px. → Bằng chứng: bảng `overflow-x-auto`, layout grid co giãn.

### Bước 4.4 — Risk Monitor

**Tham chiếu:** §9.7 Risk rules (1545–1572) · §13.4 Trader Detail (2345–2456)  
**→ đọc khi:** làm danh sách risk event, filter, evidence.

- [x] Risk Monitor page. → Bằng chứng: `/risk` + nav link.
- [x] List event + filter severity/status. → Bằng chứng: `/risk/events` filter severity/status/trader + phân trang; summary theo severity.
- [x] Mở evidence (trade/position/snapshot). → Bằng chứng: click event mở JSON evidence `{field,value,threshold,rule}` + link trader.
- [x] Link từ Detail sang Risk Monitor. → Bằng chứng: nút “Mở Risk Monitor →” kèm `?trader=<id>`.
- [x] Không hiển thị open positions giả. → Bằng chứng: ghi chú “Binance không cung cấp open positions”; E2E assert.

### Bước 4.5 — QA & gate Phase 4

**Tham chiếu:** §14.5 Contract test (2749–2788) · §14.10 Acceptance MVP (2898–2918) · §13.11 Checklist UI (2599–2616)  
**→ đọc khi:** kiểm tra contract, UI, evidence.

- [x] Mỗi chỉ số có tooltip + nguồn + cửa sổ. → Bằng chứng: E2E đếm `[title*="nguồn:"]` = 10; card ghi source/window.
- [x] Compare 4 trader không vỡ layout. → Bằng chứng: E2E 1440px, overflow ngang ≤ 4px.
- [x] Risk event mở được evidence. → Bằng chứng: E2E click event → “Evidence” + JSON.
- [x] Không hiển thị open positions như thể có dữ liệu. → Bằng chứng: ghi chú “Binance không cung cấp”; API positions chỉ trả vị thế đã đóng.
- [x] Correlation có disclaimer “estimated”. → Bằng chứng: API disclaimer + badge UI; E2E assert.
- [x] Detail p95 < 300ms (cache) / < 1s (cold). → Bằng chứng: cold 78ms; warm p95 49ms, median 41ms (30 request).
- [x] Không có `undefined`/`NaN`/`null` lọt UI. → Bằng chứng: E2E assert trên Screener/Compare/Risk/Detail.

**Gate:** mỗi chỉ số có tooltip + nguồn; compare 4 trader không vỡ; risk evidence mở được.

> **Ghi chú phạm vi:** API + trang Ranking chưa nằm trong checklist 4.1–4.5 và đã được **chuyển sang Phase 5, bước 5.4**.
> Phase 3.5 đã có service/ranking snapshot; Phase 5 chỉ bổ sung API đọc snapshot + UI.

---

## Phase 5 — AI + Settings + Hardening + Ranking/Help — HOÀN THÀNH

**Mục tiêu:** AI report có kiểm soát, toàn bộ cấu hình chỉnh trên web, bảo mật cơ bản,
hoàn thiện trang Ranking và trang hướng dẫn cho người mới.  
**Thời lượng:** 7–9 ngày.

> **Phạm vi bổ sung (07/11/2026):** Ranking UI/API chuyển từ Phase 4 sang bước 5.4;
> trang hướng dẫn người mới là bước 5.5. Đây không phải màn hình lõi mới — vẫn giữ 4 màn hình MVP
> theo D02, Help là trang phụ trợ và Ranking dùng lại dữ liệu đã có từ Phase 3.5.

### Bước 5.1 — AI report có kiểm soát

**Tham chiếu:** §11.5 AI & settings API (2071–2084) · §13.7 Màn hình AI Report (2530–2543) · §3 D11 + D31 (277–316) · §15.2 Biến môi trường (2948–2996) · §16.3 Rủi ro sản phẩm (3169–3183)  
**→ đọc khi:** viết adapter/prompt/schema, evidence, cost control.

- [x] Cấu hình OpenRouter trong `.env`. → Bằng chứng: key + `AI_MODEL_PRIMARY=nvidia/nemotron-3.5-super-vl:free`, fallback `nemotron-3-ultra-550b-a55b:free` (đổi do gemma 429).
- [x] AI adapter gọi OpenRouter (OpenAI-compatible), dùng model chính. → Bằng chứng: `services/ai/openrouter.py`; live primary fail schema → fallback thành công.
- [x] Fallback: lỗi/timeout/JSON invalid → thử model dự phòng 1 lần → template. → Bằng chứng: test `primary_invalid_json_falls_back`, `both_fail_use_template`; live 44,3s.
- [x] Lưu model đã dùng (primary/fallback), cost, latency vào report metadata. → Bằng chứng: `ai_reports.model_role/model_used/cost_usd/latency_ms`; live role=fallback, cost=0.
- [x] Không log/không trả `OPENROUTER_API_KEY` về browser. → Bằng chứng: response chỉ có `ai_configured` boolean; không có key.
- [x] Prompt template + JSON schema. → Bằng chứng: `services/ai/prompt.py`, `schema.py` (Pydantic + chặn lời khuyên).
- [x] Evidence IDs bắt buộc cho mọi nhận định. → Bằng chứng: schema min_length=1 + allowlist; test evidence ngoài danh sách → template.
- [x] Chỉ nhận dữ liệu đã chuẩn hóa, không nhận raw trade. → Bằng chứng: `build_context` chỉ lấy metrics 90D + derived + risk events.
- [x] Cost tracking. → Bằng chứng: bảng `ai_usage` (day/model/tokens/cost); live cost 0.
- [x] Budget ngày/tháng. → Bằng chứng: `check_budget`; test vượt budget → 429 `AI_BUDGET_EXCEEDED`.
- [x] Cooldown 24h + dedupe input hash. → Bằng chứng: test gọi lần 2 → `cached=true`, cùng report id.
- [x] Fallback template cuối cùng khi cả 2 model đều lỗi. → Bằng chứng: template tất định; test 2 model lỗi.
- [x] AI Reports UI. → Bằng chứng: `AIReportPanel` trong Detail; E2E render badge + evidence.
- [x] Nút Analyze trên Detail. → Bằng chứng: chỉ admin thấy; E2E mock hiển thị.
- [x] AI không sửa score/ranking. → Bằng chứng: integration test so score trước/sau bằng nhau.

### Bước 5.2 — Settings & versioning

**Tham chiếu:** §9.6 Versioning (1537–1544) · §11.5 AI & settings API (2071–2084) · §13.6 Settings & Data Health (2490–2529)  
**→ đọc khi:** làm form cấu hình, preview impact, rollback.

- [x] Data Collection tab. → Bằng chứng: 4 chu kỳ lưu vào `app_settings`; worker đọc mỗi vòng 60s.
- [x] Data Health tab. → Bằng chứng: hiển thị collector status + raw archive + lần chạy từng tầng.
- [x] Scoring tab + preview impact. → Bằng chứng: sửa 7 trọng số, preview trả `traders/changed_band/top_changes`.
- [x] Risk Rules tab. → Bằng chứng: tab hiển thị HF01–HF06 + hard_filters của version hiện tại.
- [x] AI tab: OpenRouter key (masked), `AI_MODEL_PRIMARY`, `AI_MODEL_FALLBACK`, budget. → Bằng chứng: key masked `••••`, sửa model/budget/enabled, lưu `app_settings`.
- [x] Ranking tab. → Bằng chứng: tab mô tả 3 bảng dùng chung scoring version.
- [x] Version + audit + rollback. → Bằng chứng: PUT tạo version mới, rollback active, `audit_logs` ghi before/after (10 bản ghi).
- [x] Validation + confirm khi thay đổi ảnh hưởng ranking. → Bằng chứng: 422 khi trọng số lỗi; preview trước khi lưu; E2E preview → save → rollback.

### Bước 5.3 — Hardening

**Tham chiếu:** §15.3 Quy trình deploy (2997–3012) · §15.5 Backup & restore (3029–3043) · §15.6 Monitoring (3044–3059) · §15.8 Security checklist (3075–3095)  
**→ đọc khi:** mã hóa secret, rate limit, backup, alert.

- [x] Mã hóa API key at rest. → Bằng chứng: `services/crypto.py` Fernet derive từ `JWT_SECRET`; lưu `ai.openrouter_key`; test roundtrip.
- [x] Không trả API key về browser. → Bằng chứng: API chỉ trả `key_configured/key_masked`; test assert secret không có trong response/DB plaintext.
- [x] Rate limit login/API. → Bằng chứng: login 5/phút/IP; API 100/phút/user (test monkeypatch 3 → request 4 trả 429).
- [x] Backup script. → Bằng chứng: `infra/backup.sh`, `scripts/backup.ps1` (UTF-8 BOM); chạy thật tạo dump **65 MB** + env backup.
- [x] Restore test trên staging. → Bằng chứng: restore vào DB `restore_test` → 11.185 traders, alembic `0013_audit_logs`, sau đó drop DB.
- [x] Prometheus metrics. → Bằng chứng: `GET /metrics` trả `http_requests_total`, latency, `collector_last_scan_success_timestamp`.
- [x] Alert rules. → Bằng chứng: `infra/prometheus-alerts.yml` (collector stale, 5xx, latency).
- [x] Security headers + CORS production. → Bằng chứng: Nginx trả CSP, `X-Frame-Options=DENY`, `nosniff`, Referrer-Policy, Permissions-Policy; CORS đọc env `CORS_ORIGINS`.
- [x] Dependency scan (`pip-audit`, `npm audit`). → Bằng chứng: tách `requirements-dev.txt`; `pip-audit` **0 lỗi**, `npm audit` 0 lỗi; CI thêm bước scan.

### Bước 5.4 — Ranking UI (chuyển từ Phase 4)

**Tham chiếu:** §9.8 Ranking boards (1573–1584) · §9.9 Ví dụ trader mẫu (1585–1612) · §11.3 Ranking & compare (2050–2057)  
**→ đọc khi:** làm API/trang Ranking từ snapshot đã có.

- [x] API `GET /ranking?board=overall|low_risk|consistency` đọc snapshot mới nhất + `config_version`. → Bằng chứng: `api/v1/ranking.py`; board sai → 422.
- [x] Trả `rank`, trader id/nickname, score, band, confidence, tier, risk_level, ROI/MDD/Sharpe. → Bằng chứng: integration test contract; API thêm `rank`.
- [x] Trang `/ranking`: 3 tab (Overall / Low Risk / Consistency), bảng xếp hạng, link sang Detail. → Bằng chứng: `RankingPage.tsx`; E2E “Ranking render: OK”.
- [x] Ghi rõ nguồn “snapshot + config version”, thời điểm chụp; không trộn score version cũ. → Bằng chứng: dòng metadata `Snapshot … config v…`.
- [x] Nav bỏ badge “Phase 4”, link thật. → Bằng chứng: nav mở `/ranking`.
- [x] Empty state khi chưa có snapshot + nút chạy ranking cho admin. → Bằng chứng: panel “Chưa có snapshot” + nút “Chạy ranking”.
- [x] Ghi chú không có bảng “High Return” (tránh chase ROI). → Bằng chứng: mô tả đầu trang.
- [x] Test: contract API, E2E 3 tab render, snapshot cũ không bị ghi đè. → Bằng chứng: `test_ranking_api.py` pass; `/ranking/run` thêm snapshot, bản cũ giữ.

### Bước 5.5 — Trang hướng dẫn cho người mới

**Tham chiếu:** §13.1 Nguyên tắc thiết kế (2224–2234) · §13.11 Checklist UI (2599–2616) · §16.3 Rủi ro sản phẩm (3169–3183)  
**→ đọc khi:** viết nội dung onboarding, thuật ngữ, disclaimer.

- [x] Route `/help` (Hướng dẫn); link cố định ở sidebar + banner “Mới bắt đầu?” trên Screener (dismiss lưu localStorage). → Bằng chứng: `/help` + nav; banner dismiss được, reload không hiện lại (E2E).
- [x] Mục 1 — Copy trading là gì: cơ chế copy, rủi ro mất vốn, không phải đầu tư được bảo đảm. → Bằng chứng: mục 1 + sơ đồ luồng copy.
- [x] Mục 2 — Hệ thống làm gì/không làm gì. → Bằng chứng: mục 2.
- [x] Mục 3 — Cách đọc từng màn hình, kèm ảnh minh hoạ. → Bằng chứng: mục 3 + sơ đồ Risk evidence.
- [x] Mục 4 — Từ điển thuật ngữ. → Bằng chứng: mục 4 + sơ đồ cấu trúc metric card.
- [x] Mục 5 — Tier & reason codes. → Bằng chứng: mục 5 + sơ đồ phễu.
- [x] Mục 6 — Published vs Derived vs Estimated. → Bằng chứng: mục 6.
- [x] Mục 7 — Quy trình 5 bước + checklist. → Bằng chứng: mục 7 + sơ đồ workflow.
- [x] Mục 8 — FAQ + disclaimer. → Bằng chứng: mục 8.
- [x] Mục lục anchor, tìm kiếm nội bộ, responsive, print CSS. → Bằng chứng: TOC sticky + active highlight + progress + mobile drawer; search theo keyword; print CSS.
- [x] Hình minh hoạ dễ hiểu. → Bằng chứng: 5 SVG (Copy flow, Funnel, Metric anatomy, Risk evidence, Workflow) trong `HelpIllustrations.tsx`, dùng theme token, có caption.
- [x] Nội dung tĩnh: không gọi AI, không phụ thuộc dữ liệu live. → Bằng chứng: toàn bộ nội dung hardcode; số phễu ghi “minh hoạ”.
- [x] Nguồn nội dung `docs/huong-dan-nguoi-moi.md`. → Bằng chứng: file 8 mục; UI đồng bộ nội dung.
- [x] Test: route render, anchor, E2E Help, không `undefined`/`NaN`. → Bằng chứng: E2E Help render/search/anchor/banner pass.

### Bước 5.6 — QA & gate Phase 5

**Tham chiếu:** §14.9 Security checklist (2878–2897) · §14.10 Acceptance MVP (2898–2918) · §15.8 Security checklist (3075–3095)  
**→ đọc khi:** kiểm tra AI/evidence, settings rollback, bảo mật.

- [x] AI không sửa score. → Bằng chứng: integration test score trước/sau bằng nhau.
- [x] AI trả JSON hợp lệ hoặc fallback template. → Bằng chứng: 8 unit test; live fallback 44,3s.
- [x] Không có report nào không có evidence. → Bằng chứng: schema min 1 + allowlist; live 15 evidence.
- [x] Đổi trọng số tạo version mới; score cũ giữ nguyên. → Bằng chứng: 17 version; rebuild score theo version active.
- [x] API key không trả về browser/network response. → Bằng chứng: test secret không có trong response; DB mã hoá.
- [x] Rollback hoạt động + audit log. → Bằng chứng: 34 audit rows; rollback E2E pass.
- [x] Login sai 6 lần bị rate limit. → Bằng chứng: login 5/phút/IP; API 100/phút/user (test 429).
- [x] Backup restore thành công. → Bằng chứng: dump 65 MB; restore DB tạm 11.185 trader.
- [x] Ranking 3 bảng đọc đúng snapshot + `config_version`; không trộn version. → Bằng chứng: API contract + E2E.
- [x] Trang Help render đủ 8 mục, anchor hoạt động, không lỗi console. → Bằng chứng: E2E Help + 5 SVG.
- [x] Banner “Mới bắt đầu?” dismiss được và không hiện lại sau reload. → Bằng chứng: E2E banner persist.

**Gate:** AI không sửa score; settings version hóa; backup restore OK; Ranking dùng được; Help đủ nội dung cho người mới.

### Bước 5.7 — Việt hóa giao diện

**Mục tiêu:** UI 100% tiếng Việt; backend giữ mã tiếng Anh; CSV và AI cũng tiếng Việt.

- [x] Tạo `frontend/src/i18n/vi.ts` map tier/band/risk/severity/model role/job/source/layer/flag/reason/risk event/nhóm điểm. → Bằng chứng: build pass.
- [x] Menu, login, trang chủ, banner, title tiếng Việt. → Bằng chứng: E2E + screenshot.
- [x] Screener: heading, bộ lọc, cột, drawer, empty state. → Bằng chứng: E2E; không lọt `high_upper`, `excellent`, `hf0`.
- [x] Trader Detail: 10 metric, badge, cảnh báo, vị thế/giao dịch/nạp rút, nguồn dữ liệu. → Bằng chứng: E2E; không lọt mã thô.
- [x] AI panel: nhãn Việt, hiện điểm mạnh/cần lưu ý/rủi ro/bằng chứng. → Bằng chứng: E2E.
- [x] Compare + Risk Monitor. → Bằng chứng: E2E tương quan/bằng chứng.
- [x] Ranking + Data Health. → Bằng chứng: E2E bảng xếp hạng/sức khỏe dữ liệu.
- [x] Settings: 7 tab, nhóm trọng số, preview, phiên bản, khôi phục. → Bằng chứng: E2E preview/save/rollback.
- [x] Help + 5 hình minh hoạ + docs. → Bằng chứng: E2E help/search/anchor.
- [x] CSV header tiếng Việt. → Bằng chứng: `test_screener_api` assert `Mã trader`.
- [x] AI prompt v2: tiếng Việt, phân tích theo số liệu, bắt buộc số liệu; template v2. → Bằng chứng: 13 unit test; live fallback report có ROI/MDD/Sharpe/leverage và trade-off.
- [x] QA: backend 117 passed, ruff pass, E2E 13 checkpoint, check_refs 174/0. → Bằng chứng: log chạy ngày 07/11/2026.

**Gate:** không còn chuỗi UI tiếng Anh ngoài allowlist; không lọt mã enum; AI trả tiếng Việt và có số liệu.

### Bước 5.8 — Trang Tài liệu kỹ thuật

**Mục tiêu:** trang `/technical` có mục lục 20 mục, nội dung kỹ thuật đầy đủ, tách file docs và section TSX.

- [x] Tách `docs/ky-thuat/` thành 20 file + README. → Bằng chứng: `scripts/check_tech_docs.py` báo 20/20.
- [x] Tạo `manifest.ts`, 20 section TSX, index. → Bằng chứng: build pass.
- [x] Trang `/technical`: TOC 2 cấp, search, anchor, active, progress, mobile drawer, print. → Bằng chứng: E2E technical docs.
- [x] 3 hình SVG: kiến trúc, pipeline dữ liệu, scoring. → Bằng chứng: `TechIllustrations.tsx`.
- [x] Route + menu `Tài liệu kỹ thuật` + link từ Help. → Bằng chứng: E2E.
- [x] Lazy-load route để không làm nặng bundle chính. → Bằng chứng: chunk `TechnicalDocsPage` riêng.
- [x] QA: build pass, E2E 14 checkpoint, check_tech_docs 20/20. → Bằng chứng: log 07/11/2026.

---

## Phase 6 — Testing + Deploy + Beta

**Mục tiêu:** MVP chạy VPS, có monitoring, có beta user; **Playwright E2E phủ toàn bộ use case thực tế**.  
**Thời lượng:** 6–8 ngày.

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

### Bước 6.2 — Playwright E2E toàn bộ use case

**Tham chiếu:** §14.1 Test pyramid (2619–2631) · §14.5 Contract test (2749–2788) · §14.6 Integration test (2789–2821) · §14.10 Acceptance MVP (2898–2918)  
**→ đọc khi:** dựng bộ E2E thật, kiểm tra auth/screener/detail/compare/risk/ranking/help/theme/mobile/lỗi mạng.
**Kế hoạch chi tiết:** `docs/kehoach/E2E-TEST-PLAN.md` (ma trận A/S/D/C/R/K/H/T/N/X).

- [ ] Chuyển từ `frontend/scripts/e2e.mjs` sang `@playwright/test` (`frontend/e2e/*.spec.ts`).
- [ ] Cấu hình 3 project: desktop 1440, desktop 1280, mobile 390.
- [ ] Global setup: `storageState` cho admin + viewer, lấy trader id qua API, seed saved view test.
- [ ] Tag `@smoke` (PR) và `@full` (nightly/gate); report HTML + JUnit; trace/video khi fail.
- [ ] Auth: login đúng/sai, rate limit 429, logout, deep link khi chưa login, 401 hết phiên, RBAC viewer.
- [ ] Screener: search, 4 tier, include excluded, toàn bộ filter số, sort, phân trang, saved view, CSV, drawer, reset, empty state.
- [ ] Detail: 10 metric + tooltip nguồn, 3 chart, breakdown, risk, excluded banner, 404, API 500, copy AUM = 0.
- [ ] Compare: 2/3/4 trader, chặn >4, deep link, `?ids` sai, correlation “estimated”, xóa chip.
- [ ] Risk Monitor: summary, filter severity/trader, evidence, phân trang, empty, không open positions giả.
- [ ] Ranking + Help (sau 5.4/5.5): 3 tab, snapshot metadata, 8 mục help, mục lục, banner dismiss.
- [ ] Theme: sáng/tối/hệ thống, reload giữ lựa chọn, emulateMedia, chart đổi màu.
- [ ] Responsive 390/1280/1440, keyboard tab, zoom 200%.
- [ ] Mock lỗi: 401, 500, timeout, 429, empty; assert error state không trắng trang.
- [ ] Cross-cutting: 0 console error, không `undefined`/`NaN`/`null`, không secret, tiếng Việt đúng.
- [ ] Chạy `--repeat-each=3`: 0 flaky; gate P0 100%, P1 ≥ 95%.
- [ ] Xử lý/ghi nhận gap G1–G6 trong `E2E-TEST-PLAN.md` (mobile drawer, URL state, silent refresh, stale banner, ranking/help, admin UI).
- [ ] Lưu bằng chứng vào `docs/kehoach/PHASE6-REPORT.md`.

### Bước 6.3 — Deploy VPS

**Tham chiếu:** §15.1 Topology (2921–2947) · §15.2 Biến môi trường (2948–2996) · §15.3 Quy trình deploy (2997–3012) · §15.4 Lịch chạy (3013–3028)  
**→ đọc khi:** dựng VPS, Nginx, TLS, migration, rollback.

- [ ] Deploy VPS.
- [ ] Nginx + TLS + HSTS.
- [ ] Firewall chỉ 22/80/443.
- [ ] `alembic upgrade head` + smoke test.
- [ ] Rollback image hoạt động.
- [ ] Log dashboard.

### Bước 6.4 — Monitoring & vận hành

**Tham chiếu:** §15.5 Backup & restore (3029–3043) · §15.6 Monitoring & alert (3044–3059) · §15.7 Runbook sự cố (3060–3074) · §15.10 Tài liệu vận hành (3107–3115)  
**→ đọc khi:** đặt alert, viết runbook, kiểm tra backup.

- [ ] Alert collector fail/stale/disk/AI budget/5xx.
- [ ] Backup daily + retention 7 daily/4 weekly.
- [ ] Test restore < 30 phút.
- [ ] Viết runbook.
- [ ] Viết deployment doc.
- [ ] Viết data-quality doc.

### Bước 6.5 — Beta & feedback

**Tham chiếu:** §4.4 Tiêu chí thành công MVP (356–384) · §21 Việc cần làm ngay (3385–3483) · §18 Backlog v1.1 (3291–3319)  
**→ đọc khi:** chuẩn bị beta, thu feedback, chốt backlog.

- [ ] Beta 3–5 user.
- [ ] Thu feedback có cấu trúc.
- [ ] Chốt backlog v1.1 từ feedback.
- [ ] Cập nhật `SESSION.md`.
- [ ] Ghi lại bug/khác biệt phát hiện trong beta.

### Bước 6.6 — Gate Phase 6

**Tham chiếu:** §14.10 Acceptance MVP (2898–2918) · §15.8 Security checklist (3075–3095)  
**→ đọc khi:** nghiệm thu cuối.

- [ ] Uptime 7 ngày không crash nghiêm trọng.
- [ ] Collector chạy đủ 7 ngày, freshness < 150 phút.
- [ ] Backup restore thành công.
- [ ] Không có lỗi bảo mật nghiêm trọng.
- [ ] ≥ 3 người dùng thử và phản hồi.
- [ ] Playwright `@full` pass: P0 100%, P1 ≥ 95%, 0 flaky sau 3 lần.
- [ ] Không còn `[!]` blocking trong mục 20.

**Gate:** uptime 7 ngày, collector đủ 7 ngày, beta feedback, E2E full matrix pass.

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

---

## Risk V2 — spec only (07/11/2026, ngoài MVP)

> Kế hoạch: `docs/0/02-ke-hoach-risk-v2.md`. Spec: `docs/kehoach/RISK-V2-SPEC.md`. Đã implement code + migration.

- [x] T1. Chốt spec Sharpe (âm/null/thang veto). → Bằng chứng: `RISK-V2-SPEC.md §1`.
- [x] T2. Chốt ma trận R01–R17 + evidence. → Bằng chứng: `RISK-V2-SPEC.md §2`.
- [x] T3. Chốt công thức risk_score + map level + 3 ví dụ (90 điểm Sharpe âm → high). → Bằng chứng: `RISK-V2-SPEC.md §3`.
- [x] T4. Chốt tương thích enum + rollout + gate spec. → Bằng chứng: `RISK-V2-SPEC.md §4`; `docs/0/02-ke-hoach-risk-v2.md`.
- [x] T5. Implement Risk V2. → Bằng chứng: `risk_rules.py` R01–R19 + score/veto; migration `0014_risk_v2`; `risk_service/ranking/trader_detail/vi.ts` cập nhật; pytest 94 pass + build OK.

---

## Phase 6b — AI Agent chat (07/11/2026, docs/0/03-ke-hoach-ai-agent.md)

> Chỉ admin. Icon chat nổi góc phải dưới. Tool DB + SQL read-only + Tavily + code/docs RAG. Citation + verifier.

- [x] B1. Schema agent + migration 0015. → Bằng chứng: `backend/app/models/agent.py` (5 bảng), migration `0015_agent_tables` (+`ai_usage.feature`); `test_agent_schema.py` 4 pass; alembic downgrade -1/upgrade head OK.
- [x] B2. Agent core + model + SSE skeleton. → Bằng chứng: `services/agent/` 5 module + `api/v1/agent.py` (admin-only); `test_agent_core.py` 11 pass (container, gồm RBAC viewer 403 + SSE done/citation); reasoning auto dùng chung; `docs/api.md` + `12-ai.md` + section TSX.
- [x] B3. DB tools (search/profile/compare/ranking/risk/health). → Bằng chứng: `services/agent/db_tools.py` + `test_agent_db_tools.py` 4 pass (container); regression screener/compare/ranking/core 14 pass; top-10 sort deterministic; unknown/empty có cấu trúc; risk_score chưa backfill → rỗng đúng.
- [x] B4. Read-only SQL + views. → Bằng chứng: migration `0016_agent_views` (5 view); `sql_tools.py` (chỉ SELECT/WITH, chặn DDL/DML/multi-statement/bảng secret, limit 200/500, timeout 5s, transaction READ ONLY); `test_agent_sql.py` 4 pass.
- [x] B5. Floating chat UI. → Bằng chứng: `AgentLauncher/Panel` + `lib/agent.ts` (SSE flush buffer); chỉ admin; E2E full PASS (agent mock SSE + viewer ẩn icon, 0 console error).
- [x] B6. QA Phase 1 agent. → Bằng chứng: full suite 145 pass, ruff pass, build pass, E2E PASS, check_refs 174/0, không secret trong agent code.
- [x] B7. Tavily web search + cache. → Bằng chứng: `web_tools.py` (mock Tavily, cache Redis 24h, timeout 10s, tắt khi thiếu key); `test_agent_web.py` 2 pass (gồm prompt-injection snippet chỉ là dữ liệu).
- [x] B8. Knowledge index code/docs. → Bằng chứng: migration `0017_knowledge_chunks` + `knowledge.py`/`knowledge_cli.py`; dry-run 204 file → 996 chunk; `test_agent_knowledge.py` 3 pass (path/line).
- [x] B9. Citation + verifier hardening. → Bằng chứng: `verifier.py` (số/đơn vị/trader_id/advice + contract confidence) + citation UI nhóm nguồn; `test_agent_verifier.py` 6 pass; E2E citation PASS.
- [x] B10. Portfolio fit + vốn 100$. → Bằng chứng: `portfolio.py` (`evaluate_fit` thuần + tool); unit 3 case dưới/bằng/trên min + unknown; integration trader thật; E2E $100 mock ở B12.
- [x] B11. Search tự nhiên trong Screener. → Bằng chứng: `nl_search.py` (10 case), `/agent/search`, Screener `min_score`/`max_min_copy_usd`, UI ô mô tả + chips + Áp dụng/Xóa, E2E PASS.
- [x] B12. QA Phase 3. → Bằng chứng: full backend 166 pass, ruff/build/E2E/check_refs pass; fix regression `min_confidence` trong search_traders.
- [x] B13. Eval + security + cost + retention. → Bằng chứng: eval 50 câu pass, retention + template fallback + feedback UI test pass, E2E feedback PASS.
- [x] B14. Final QA + báo cáo. → Bằng chứng: full 218 pass, E2E PASS, head `0017_knowledge_chunks`, check_refs 174/0, check_tech_docs 20/20, commit hash đủ B1–B13.

---

## Phase 6c — Screener đa khung + giữ trạng thái (docs/0/04-ke-hoach-screener-da-khung.md)

- [x] B4.0.1 URL state Screener + giữ vị trí. → Bằng chứng: `lib/screenerQuery.ts`; E2E "Screener giữ trạng thái" PASS.
- [x] B4.0.2 Migration `0018_metric_windows`. → Bằng chứng: 15 cột + 6 index; up/down OK; `test_models` 4 pass.
- [x] B4.0.3 Builder ghi đa khung. → Bằng chứng: `WINDOW_COLUMN_MAP`; backfill 531 trader/501 có đa khung; `test_metric_windows` 2 pass.
- [x] B4.0.4 Screener API đa khung + filter mở rộng. → Bằng chứng: `window` + 17 filter; `test_screener_api` 6 pass.
- [x] B4.0.5 UI Screener đa khung. → Bằng chứng: selector khung + 3 nhóm filter + badge; E2E đa khung/mobile PASS.
- [x] B4.0.6 Detail hiển thị 4 khung. → Bằng chứng: bảng 4 dòng × 7 cột từ `performance.windows`; E2E PASS.
- [x] B4.0.7 Agent trả đủ dữ liệu trader. → Bằng chứng: `detail=full/summary`, 4 khung × 8 field + 38 derived + 10 profile; test 6 pass.
- [x] B4.0.8 Orchestrator JSON compact. → Bằng chứng: `compact_observation` + test 3 pass; tokens 4000.
- [x] B4.0.9 Eval agent đa use case (15 case phân tích/đánh giá). → Bằng chứng: 15/15 pass; scorecard trong plan 04.
- [x] B4.0.10 QA cuối kế hoạch 04. → Bằng chứng: 249 pass, ruff/build/E2E 20 checkpoint, head `0018`, check_refs 174/0, check_tech_docs 20/20.

---

## Phase 6d — Độ tươi dữ liệu & Data Health (docs/0/05-ke-hoach-do-tuoi-du-lieu-va-data-health.md)

> Bổ sung V7–V9 ngày 08/11/2026 sau khi kiểm tra sai lệch số 7D của trader `5076854789130646529`.

- [x] B5.0.1 Chốt spec + migration manifest. → Bằng chứng: `RAW-ARCHIVE-SPEC.md`; migration `0019` + 2 index; `test_models` 5 pass.
- [x] B5.0.2 Refactor RawArchive (`latest_previous`, gzip, atomic). → Bằng chứng: 2 bundle/lần scan; rotate latest/previous; `test_raw_archive` 4 pass.
- [x] B5.0.3 Retention + CLI dry-run. → Bằng chứng: `test_raw_retention` 2 pass; CLI `archive-retention --dry-run` chạy được.
- [x] B5.0.4 API status nhanh + archive-stats. → Bằng chứng: p95 76ms; `test_collector_status` 4 pass.
- [x] B5.0.5 Scheduler freshness (last_success từ DB, không `last_run = now`). → Bằng chứng: `test_scheduler_freshness` 7 pass; worker log đọc last_success thật.
- [x] B5.0.6 Job thủ công lưu DB. → Bằng chứng: migration `0020`; job queued→success thật; RBAC + kill switch test pass.
- [x] B5.0.7 UI loading/progress. → Bằng chứng: skeleton + elapsed + countdown; E2E route chậm/500 PASS.
- [ ] B5.0.8 Freshness hiển thị + cảnh báo AI (V7): ngưỡng 150/1440 phút, chip/banner, `warning` agent.
- [ ] B5.0.9 `as_of` = `provenance.performance_at`, tách khỏi `computed_at` (V8).
- [ ] B5.0.10 Backfill `risk_score` 531/531 + `meta.risk_score_missing` khi thiếu (V9).
- [ ] B5.0.11 QA + docs.
