# SESSION — Phase 0 & Phase 1

> **Ngày:** 2026-11-06  
> **Trạng thái:** Phase 0 hoàn tất — **GO CÓ ĐIỀU KIỆN**  
> **Sản phẩm:** Binance Copy Trader Screener & Risk Analytics (không auto-trade)

---

## 1. Mục tiêu phiên

1. Xác minh 6 endpoint BAPI bằng dữ liệu thật.
2. Chốt universe PUBLIC + SIGNAL và phễu C/B/A/Excluded.
3. Đo false negative của bộ lọc.
4. Kiểm chứng các bẫy chỉ số (MDD, WinRate, Sharpe, AUM, Copier PnL, fee).
5. Ra quyết định go/no-go cho Phase 1.

---

## 2. Kết quả chính

| Hạng mục | Kết quả |
|---|---|
| Universe | **11.124** = 8.970 PUBLIC + 2.154 SIGNAL, coverage 100% |
| Watch (C, gồm B/A) | **515** (457 PUBLIC + 58 SIGNAL) |
| Qualified gồm High (B+A) | **109** (99 + 10) |
| High (A) | **13** (13 + 0) |
| Excluded | **10.609** |
| Mẫu deep fetch | **63** (A=13, B=20, C=20, excluded=10) |
| Deep fetch | 63/63 OK, 153,34s, 0 lỗi |
| False negative thực | **0/50 = 0%** (`fn_watch_eligible`) |
| False negative literal | 12/50 = 24% (do thiếu AUM/MDD trong định nghĩa) |
| Activity proxy | 60/63 khớp (95,2%), 3 FP, 0 FN |
| Rate limit | 32 request, 0 bị chặn, 0 lỗi |

---

## 3. Quyết định quan trọng

### D-MDD — Nguồn MDD

- **Hiển thị/xếp hạng:** `performance.mdd` (published).
- **Audit:** `equity = 1 + chartItems.value / 100`, khớp published **63/63**, sai số max **4,9 × 10⁻⁷ pp**.
- Con số **88,67%** cũ là **lỗi công thức** (coi ROI lũy kế là equity), không phải lỗi `chartItems`.
- MDD **phụ thuộc window**: chỉ 6/63 trader giống nhau ở 4 window; chênh tối đa 70,26 pp.

### D-ACT — Activity

- List payload **không có** `lastTradeTime`.
- Proxy `traded_last_7d` không bỏ sót trader đang trade (0 FN) nhưng có thể giữ trader đã ngừng (3 FP).
- Bắt buộc xác minh `detail.lastTradeTime` trước khi ranking.

### D-WR — WinRate

- `winRate` = theo order; khác position-level.
- 59/63 so sánh được; median lệch 2,52 pp; 18 ca lệch > 5 pp; max 33,33 pp.
- Phải hiển thị tách biệt.

### D-NULL — Sharpe

- Null 34,9% universe, 4,8% sample.
- Hiển thị `N/A`, không chấm 0.

### D-FEES — Fee

- 56/58 trader có fee âm; tổng page 1 = −5.835,4656.
- Rebate là bình thường; không cộng fee như chi phí dương.

### D-SCOPE — Endpoint thiếu

- 6/6 probe trả 404: open positions, copier list, funding.
- Không cam kết các tính năng này trong MVP.

---

## 4. Artifact

- `phase0/PHASE0_REPORT.md` — báo cáo đầy đủ.
- `phase0/data/universe_90d.jsonl` — 11.124 trader.
- `phase0/data/tier_summary.csv` — phễu theo nguồn.
- `phase0/data/sample_manifest.csv` — 63 trader mẫu.
- `phase0/data/audit_summary.json` — false negative.
- `phase0/data/indicator_quality_summary.json` — kiểm chứng chỉ số.
- `phase0/data/rate_limit_summary.json` — rate limit.
- `phase0/data/raw/` — raw bundle.

**Giới hạn dữ liệu đã fetch:** positions 13.589/22.641 dòng (7 trader bị cap 1.000 vị thế gần nhất); trades chỉ page 1 (10.967/112.759 dòng); transfers đầy đủ 2.063/2.063.

Scripts:

- `phase0/fetch.py`, `tiering.py`, `scan_universe.py`, `recompute_summary.py`
- `phase0/sample.py`, `deep_fetch.py`, `activity_check.py`
- `phase0/audit_excluded.py`, `indicator_checks.py`, `rate_limit_test.py`

---

## 5. Tài liệu đã sửa

- `docs/kehoach/02-data-contract-binance.md` — đính chính MDD, thêm quy tắc audit.
- `docs/kehoach/03-bo-chi-so-va-scoring.md` — sửa cảnh báo công thức MDD.
- `docs/kehoach/06-kiem-thu-van-hanh-bao-mat.md` — acceptance test MDD.
- `docs/kehoach/07-rui-ro-phap-ly-va-du-phong.md` — mô tả flow distortion đúng.
- `docs/kehoach/08-nhat-ky-quyet-dinh.md` — sửa D06 + phát hiện #6.
- `docs/kehoach/data-availability-matrix.csv` — thêm giới hạn list/detail, audit MDD.
- `docs/kehoach/TASKS.md` — cập nhật trạng thái Phase 0.

---

## 6. Việc tiếp theo (Phase 1)

1. Dựng backend + model theo contract đã chốt.
2. Collector 2 tầng: list 90D → detail/performance cho Watch.
3. Lưu `timeRange` cùng mọi metric.
4. Hiển thị MDD published + nhãn window.
5. Hiển thị WinRate order và position tách biệt.
6. Sharpe null → `N/A` + confidence.
7. Không đưa open positions/per-copier/funding vào MVP.

---

## 7. Cảnh báo vận hành

- `performance` chỉ dùng `BASE_P`.
- List page size tối đa 30; trade tối đa 200.
- Giữ 5–6 worker; backoff khi 429/418.
- `total` có thể đổi giữa các trang → luôn dedupe theo `leadPortfolioId`.
- `positionShow=false` **không** chặn position-history.
- Young portfolio: không giả định 4 window giống nhau; đã thấy ca 29,98 ngày khác window.

---

## 8. Phase 1 — Foundation + vertical slice

### 8.1. Quyết định kỹ thuật

- Backend: Python 3.12+, FastAPI async, SQLAlchemy 2.x async, Alembic.
- DB URL dùng `postgresql+asyncpg://` cho app và migration.
- Frontend: React 18 + Vite 6 + TypeScript + Tailwind 3.
- Reverse proxy: Nginx, cổng ngoài **8080** (tránh xung đột cổng 80).
- Compose gồm `db`, `backend`, `frontend`, `nginx`; volume `pgdata`.
- CI: GitHub Actions, backend ruff + pytest, frontend `npm ci && npm run build`.

### 8.2. Trạng thái bước

| Bước | Trạng thái | Bằng chứng |
|---|---|---|
| 1.1 Khởi tạo repo & hạ tầng | `[x]` | compose up OK, `/health` OK, alembic OK, CI file có |
| 1.2 Database & model | `[x]` | 4 bảng + migration `0001_core_tables`; downgrade/upgrade OK |
| 1.3 Auth & RBAC | `[x]` | JWT access/refresh, Argon2id, RBAC, rate limit 429 lần 6 |
| 1.4 Adapter + seed | `[x]`* | DemoAdapter 2 fixture; CSV stub; seed idempotent 2 traders/8 metrics/2 snapshots; *API null kiểm ở 1.5 |
| 1.5 API trader detail | `[x]` | `/traders/{id}`: 10 metrics, tier, reasons, confidence, provenance; null giữ null |
| 1.6 Frontend tối giản | `[x]` | Login, layout, detail 10 metrics, excluded badge; E2E Playwright pass |
| 1.7 QA & gate | `[x]` | 12 test pass; clean compose; E2E; secret scan; downgrade OK |

### 8.3. Lệnh kiểm tra 1.1

```powershell
docker compose config
docker compose up -d --build
Invoke-WebRequest -UseBasicParsing http://localhost:8000/health
Invoke-WebRequest -UseBasicParsing http://localhost:8080/api/v1/health/db
.\.venv\Scripts\ruff.exe check backend
.\.venv\Scripts\pytest.exe backend\tests -q
cd frontend; npm run build
```

### 8.4. Database 1.2

- 4 bảng lõi: `users`, `traders`, `portfolio_snapshots`, `performance_metrics`.
- `users.id` UUID; `traders.lead_portfolio_id` là text PK; snapshot/metric dùng bigserial.
- `portfolio_snapshots.raw` và `performance_metrics.raw` dùng JSONB.
- Unique: snapshot theo giờ + source; performance theo `(lead, time_range, collected_at)`.
- Migration `0001_core_tables`; đã test `downgrade base` → `upgrade head`.

### 8.5. Auth 1.3

- Password hash: Argon2id (`argon2-cffi`).
- JWT HS256: access 15 phút, refresh 7 ngày; refresh rotate và lưu hash trong `sessions`.
- Endpoint: `/api/v1/auth/login`, `/refresh`, `/logout`, `/me`; admin check `/api/v1/admin/ping`.
- Rate limit login 5/phút/IP bằng SlowAPI (in-memory Phase 1; Redis ở Phase 2).
- Seed: `python -m app.seed all` tạo `admin@example.com` và `viewer@example.com`.
- Smoke test: `scripts/smoke_auth.ps1`; rate limit: `scripts/test_rate_limit.ps1`.
- Lưu ý: script `.ps1` lưu UTF-8 BOM, đặt `chcp 65001` để hiển thị tiếng Việt.

### 8.6. Adapter & seed 1.4

- `DataSourceAdapter` Protocol, `DemoAdapter`, `CsvImportAdapter` stub.
- Fixture excluded: `5296057151807357697` (runtime 4,11 ngày, AUM 1.200).
- Fixture qualified: `4520644381136785152` (B tier, ROI 19,19%, MDD 8,54%, Sharpe 2,84).
- Thêm bảng `trader_universe` (migration `0003`) lưu tier/reason/pre_score.
- Seed idempotent: chạy 2 lần vẫn 2 traders / 8 metrics / 2 snapshots.
- Null được giữ nguyên: excluded 90D có `mdd=NULL`, `sharpe=NULL`.

### 8.7. API trader detail 1.5

- `GET /api/v1/traders/{id}` (bắt buộc access token).
- Trả 10 chỉ số, `tier`, `reasons`, `pre_score`, `profile`, `confidence`, `flags`, `provenance`, `disclaimer`.
- Null giữ null: excluded có `mdd=null`, `sharpe=null`, flags `missing_sharpe`/`missing_mdd`.
- Derived chưa có dữ liệu (profit factor, avg holding) trả `null` + flag `derived_unavailable`.
- 404 wrapper `TRADER_NOT_FOUND`; thiếu token 401.
- Test: `scripts/smoke_trader.ps1` → PASS.
- Tài liệu API: `docs/api.md`.

### 8.8. Frontend 1.6

- React 18 + Vite + TypeScript + Tailwind; TanStack Query.
- Trang: `/login`, `/` (2 fixture), `/traders/:id`.
- Layout sidebar/topbar; hiển thị user/role, nút đăng xuất, freshness demo.
- Detail: 10 metric cards, tier badge, excluded banner + reasons, risk flags, what's missing, provenance.
- Null hiển thị `N/A`; copy AUM = 0 ghi “Không có copier”.
- E2E: `cd frontend; npm run test:e2e` → đăng nhập, qualified, excluded, đăng xuất, không console error.

### 8.9. QA & gate 1.7

| Kiểm tra | Kết quả |
|---|---|
| Backend test trong container | **12 passed** (11 unit + 1 integration) |
| Compose từ máy sạch | `down -v` → `up -d --build` OK, 4 service chạy |
| Auth/RBAC | smoke PASS; viewer → admin 403 |
| Trader qualified | tier qualified; ROI 19,19%; MDD 8,54%; Sharpe 2,84 |
| Trader excluded | banner + reason; MDD/Sharpe null |
| Null ≠ 0 | API/UI giữ `null` / `N/A` |
| Rate limit | lần 6 → 429 |
| Migration | downgrade base → upgrade head trên volume mới |
| Secret scan | không track `.env`; không match pattern secret |
| Dependency scan | `npm audit --audit-level=high` → 0 vulnerability |
| E2E frontend | Playwright PASS, 0 console error |

**Gate Phase 1: ĐẠT.** Vertical slice chạy end-to-end với 2 fixture.

---

## 9. Phase 2 — Collector 2 tầng + raw storage

### 9.1. Adapter 2.1

- `collector/http.py`: timeout 20s, retry `11012005`/5xx/timeout (tối đa 4, backoff 2→16s + jitter), circuit breaker 5 lỗi liên tiếp/60s.
- `collector/binance.py`: 6 endpoint; list 30/trang, positions 50, trades 200, transfers 50; performance dùng `BASE_P`.
- Test mock 9 ca (retry, 404 không retry, breaker) + smoke live 6 endpoint PASS.

### 9.2. Universe scan 2.2

- Live: 372 trang, PUBLIC 8.966 + SIGNAL 2.164 = **11.130**, duplicates 0, 129–139s.
- Lưu 11.130 `portfolio_snapshots(source='list')` + 372 file JSONL trong `data/raw/`.
- Redis lock `lock:collector:scan`, fallback `pg_try_advisory_lock`.
- Chạy lại trong cùng giờ: snapshot không tăng (idempotent theo giờ).

### 9.3. Tier & pre-score 2.3

- Q02: pre_score percentile trên **một cohort chung** `all` (PUBLIC+SIGNAL).
- Trước khi có `totalOrder`: watch 398, qualified_upper 97, high_upper 14, excluded 10.621; Watch tổng 509.
- `tier_history` ghi khi tier đổi; recompute lần 2 `changed=0`.
- API `/universe/summary`, `/universe/traders`, `/universe/recompute` (admin).

### 9.4. Performance 4 window 2.4

- Live 509 trader × 4 window = 2.036 metric, 0 lỗi.
- HF04 hạ tier theo `totalOrder` 90D: **38 trader** bị hạ → watch 429, qualified 73, high 7 (Qualified+High = 80).
- Sharpe null giữ `NULL` (90D: 9 trader), mdd null giữ `NULL` (1 trader).
- Upsert theo `(lead, time_range, collected_at)` với `collected_at` cắt về giờ → chạy lại không nhân bản.
