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

> Cổng host đã đổi 07/11/2026: backend `8010`, web `8090` (tránh trùng dự án `cors-mvp` đang chạy). Cổng nội bộ container vẫn `8000/80`.

```powershell
docker compose config
docker compose up -d --build
Invoke-WebRequest -UseBasicParsing http://localhost:8010/health
Invoke-WebRequest -UseBasicParsing http://localhost:8090/api/v1/health/db
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

### 9.5. Detail + positions + transfers 2.5

- Target: 80 Qualified/High + top 200 Watch = **280 trader**; 0 ineligible.
- Live: **71.026 vị thế**, **8.267 transfer**, 0 lỗi.
- Position page size 50, tối đa 20 trang/trader (1.000 vị thế) để chặn chi phí.
- `positionShow=false` không chặn position-history (D25).
- Lưu `positions` unique `(lead, position_id)`, `transfers` unique `(lead, transfer_hash)`.
- Detail lưu snapshot `source='detail'` theo giờ.

### 9.6. Full trade history 2.6

- Target: 7 high + top 50 qualified = **57 trader**; 0 lỗi.
- Fetch: 130.962 fill, lưu **120.595** trade unique; 10.367 bản ghi trùng bị hash loại.
- Pagination dừng theo `total`, không break sớm; cap an toàn 500 trang/trader.
- Chỉ high/qualified có trades; **watch/excluded = 0** (query kiểm chứng).
- Gặp `11012005` thật khi chạy full trades: backoff 2→16s xử lý hết, 0 request thất bại.
- Giảm burst: giới hạn 3 trader đồng thời cho trade-history (semaphore riêng).

### 9.7. Storage, scheduler, vận hành 2.7

- `worker` chạy scheduler: scan 60 phút, perf 6h, detail 12h, trades 24h.
- Lock Redis + fallback advisory; job trùng bị `skipped`.
- API `/collector/status`, `/run-scan`, `/run-deep` (202 + job), `/kill-switch`.
- Kill switch env hoặc `app_settings`; tắt → 409 `COLLECTOR_DISABLED`.
- UI `/data-health`; E2E pass.
- Xử lý `11012005`/429: cooldown toàn cục 30–180s, 5 retry, trades tuần tự 0,4s/trang.
- `recompute_universe` áp dụng lại HF04 để không xóa demotion sau mỗi vòng scan.

### 9.8. QA & gate 2.8

| Kiểm tra | Kết quả |
|---|---|
| Coverage 1 run | 11.132 / 11.124 = 100,07% |
| Watch | 511 (watch 425 + qualified 76 + high 10) |
| Excluded deep fetch | 0 tại thời điểm chọn |
| Chạy lại 3 lần | counts giống hệt |
| Resume | kill 35s → chạy lại đủ, duplicate = 0 |
| Chu kỳ scan + shortlist | 181,3s |
| Full deep | 511 perf 38,7s + 278 detail 77,9s + 57 trades 134,2s = 250,8s |
| Test container | 41 passed |
| Báo cáo | `docs/kehoach/PHASE2-REPORT.md` |

**Gate Phase 2: ĐẠT.**

---

## 10. Phase 3 — Quant + Scoring + Screener

### 10.1. Quant metrics 3.1

- `services/quant/metrics.py` (thuần) + `confidence.py` + `builder.py` (đọc DB).
- Bảng `trader_metrics` (migration 0008): 1 dòng/trader, cột scalar cho screener + `metrics` JSONB.
- Published giữ nguyên 4 window; WinRate order và position tách riêng.
- Derived: leverage, margin mode, holding (avg/median/max), profit factor, payoff, concentration,
  fee drag (rebate âm), worst ROI, near-liquidation, fills, fees, net flow, calmar.
- Confidence §8.8; benchmark chưa có nguồn → null + `missing_benchmark`.
- Live: 511 trader, 3,61s; avg confidence 0,847; 9 sharpe null; 0 mdd null.
- Lệnh: `docker compose exec backend python -m app.collector_cli metrics`.

### 10.2. Funnel audit 3.2

- Tier/pre_score/reasons/history đã có từ Phase 2; bổ sung test excluded luôn có reason và history chỉ ghi khi đổi.
- Audit 50 excluded: `audit_excluded()` gọi detail + performance 90D, đánh giá đủ điều kiện Watch
  (ACTIVE, không paused, runtime ≥ 30, ROI/PnL > 0, WR ≥ 40, MDD ≤ 40, AUM ≥ 5k, totalOrder ≥ 20, còn slot, trade 7D).
- Kết quả live: 50/50 đánh giá, **0 false negative (0%)**, 0 lỗi; lưu `collection_logs.layer='A1'`.
- Q01/Q02 giữ nguyên: mdd null + `missing_mdd`; pre_score cohort `all`.

### 10.3. Risk rules 3.3

- `services/risk_rules.py` (R01–R11) + `risk_service.py` ghi `risk_events` và `trader_metrics.risk_level`.
- Mỗi event có evidence JSON `{field, value, threshold, rule}`; thiếu dữ liệu → `unknown`, không tạo event sai.
- Live: 511 trader → 1.100 event; critical 280, high 501, medium 219, low_sample 91, penalty 9.
- Risk level: critical 214, high 164, medium 55, low 13, none 38, unknown 27.
- Lệnh: `docker compose exec backend python -m app.collector_cli risk`.

### 10.4. Scoring & versioning 3.4

- `services/scoring.py` (thuần) + `scoring_service.py`; bảng `scoring_config_versions`, `trader_scores`, `ranking_snapshots` (migration 0010).
- Trọng số 7 nhóm §9.1; percentile trong cohort, winsorize 2,5–97,5, đảo chiều MDD/leverage/ROI stability.
- Missing → loại nhóm, renormalize; không gán 0; breakdown có `score/weight/contribution/missing`.
- Hard filter HF01–HF06 (HF04 theo tier 20/50/100); `rankable` = score + không hard flag.
- Seed config v1 active; score lưu theo `(lead, config_version)`, không ghi đè version cũ.
- Live: 511 scored, **236 rankable**; band good 14 / average 145 / weak 240 / high_risk 112;
  sai số breakdown ≤ **0,0051**.
- Lệnh: `python -m app.collector_cli score`.

### 10.5. Ranking 3 bảng 3.5

- `services/ranking.py`: Overall (score), Low Risk (runtime ≥ 90, MDD ≤ 20, lev ≤ 5, confidence ≥ 0.8),
  Consistency (theo điểm consistency, runtime ≥ 90). Không có bảng High Return.
- Snapshot `ranking_snapshots` theo `config_version`; live: overall 50, low_risk 38, consistency 50.
- Test: loại not-rankable, loại leverage/MDD/runtime/confidence, consistency không phụ thuộc ROI.
- Lệnh: `python -m app.collector_cli rank`.

### 10.6. Screener API + UI 3.6

- Backend `services/screener.py` + `api/v1/screener.py` + `saved_views.py`; bảng `saved_views` (migration 0011).
- GET `/traders` đủ filter/sort/pagination, outer join để excluded vẫn hiện khi bật toggle.
- `/traders/funnel-summary`, `/traders/export.csv`, CRUD `/saved-views`.
- UI `/screener`: filter bar, funnel badge, count preview, bảng 13 cột, sort, phân trang,
  breakdown drawer, saved views, CSV, empty state, toggle excluded.
- Test: 4 integration test pass; E2E “Screener render: OK”.

### 10.7. QA & gate Phase 3

| Kiểm tra | Kết quả |
|---|---|
| Golden dataset | 12 archetype, 2 excluded; 5 test pass |
| Excluded không lọt top | top 5 không chứa archetype excluded |
| Missing không chấm 0 | score vẫn có, breakdown ghi missing |
| Hard filter tier | 20/50/100 đúng |
| Audit false negative | 50 excluded → **0%** |
| p95 shortlist | **97ms** (median 78ms, page_size 100) |
| Breakdown vs score | max diff **0,0051** |
| MDD ≤ 15 | 10/10 dòng khớp SQL |
| Full suite container | **81 passed** |
| Build + E2E | Pass |
| Báo cáo | `docs/kehoach/PHASE3-REPORT.md` |

**Gate Phase 3: ĐẠT.**

---

## 11. Phase 4 — Detail + Compare + Risk Monitor

### 11.1. API detail mở rộng 4.1

- `api/v1/trader_detail.py`: performance, positions, trades, transfers, risk, score.
- Positions/trades phân trang + filter symbol/side; 404 wrapper thống nhất.
- Performance trả chartItems từ list snapshot + note flow; benchmark null có ghi chú.
- Test contract + 404 + phân trang: 3 test pass.

### 11.2. Trader Detail UI 4.2

- Trang detail dùng 6 endpoint mới + `recharts` (Line ROI, Area drawdown estimated, Bar PnL histogram).
- Header score/confidence/risk; 10 metric card kèm tooltip định nghĩa + nguồn + cửa sổ.
- Score breakdown 7 nhóm; risk chips có evidence; “what’s missing”; positions table; trades; transfers.
- Fix dữ liệu: API detail convert chuỗi số từ JSONB sang number (tránh `.toFixed` crash).
- E2E pass, không console error.

### 11.3. Compare 2–4 trader 4.3

- `services/compare.py` + `api/v1/compare.py`: validate 2–4 id, trả metrics, series chartItems, correlation.
- Correlation = Pearson trên sai phân ROI theo ngày, cần ≥ 30 điểm chung; disclaimer “estimated”.
- UI `/compare`: picker tìm trader, chip tối đa 4, bảng 15 chỉ số, chart nhiều đường,
  ma trận correlation, deep link `?ids=`.
- Test: 5 unit + 2 integration pass; E2E “Compare render: OK”.

### 11.4. Risk Monitor 4.4

- `api/v1/risk.py`: `/risk/summary`, `/risk/events` filter severity/status/trader + phân trang.
- UI `/risk`: summary chip, filter, danh sách event, mở evidence JSON, link sang trader.
- Detail có link `?trader=<id>` sang Risk Monitor.
- Không hiển thị open positions giả; ghi rõ Binance không cung cấp.
- Test: integration risk API pass; E2E “Risk Monitor render: OK”.

### 11.5. QA & gate Phase 4

| Kiểm tra | Kết quả |
|---|---|
| Tooltip nguồn + cửa sổ | 10/10 card, E2E đếm ≥ 10 |
| Compare 4 trader | 1440px, overflow ≤ 4px |
| Risk evidence | mở JSON evidence, E2E pass |
| Open positions giả | không hiển thị, có ghi chú |
| Correlation disclaimer | “estimated” trong API + UI |
| Detail p95 | cold 78ms · warm p95 49ms |
| undefined/NaN/null | E2E assert sạch |
| Full suite container | **97 passed** |
| npm audit | 0 lỗi |
| Báo cáo | `docs/kehoach/PHASE4-REPORT.md` |

**Gate Phase 4: ĐẠT.**

---

## 12. Giao diện sáng/tối (07/11/2026)

- Thêm 3 chế độ Sáng / Tối / Hệ thống; mặc định theo OS, lưu `ct_theme_mode`.
- Token màu semantic (`bg-app/panel/elevated`, `text-strong/body/muted/faint`, `accent/info/warn/danger`)
  khai báo trong `index.css` + `tailwind.config.js`; thay toàn bộ màu slate cứng trong 8 file UI.
- Chart dùng CSS var; nút chuyển ở topbar và trang login.
- Tài liệu: `docs/ui-theme.md`; E2E kiểm tra light/dark/system.

---

## 13. Phạm vi bổ sung Phase 5 (07/11/2026)

Lý do: Phase 4 hoàn thành nhưng trang `/ranking` vẫn là placeholder vì checklist 4.1–4.5 không có
task API/UI Ranking; Phase 3.5 mới chỉ có service + snapshot.

Đã cập nhật tài liệu (không sửa mã nguồn):

- `TASKS.md` Phase 5:
  - **Bước 5.4 — Ranking UI** (chuyển từ Phase 4): API `/ranking?board=`, 3 tab, đọc snapshot + config version.
  - **Bước 5.5 — Trang hướng dẫn người mới**: 8 mục từ “copy trading là gì” đến FAQ/disclaimer,
    banner onboarding, mục lục anchor, nội dung tĩnh.
  - QA cũ đổi thành **5.6**, bổ sung check Ranking/Help; thời lượng Phase 5: **7–9 ngày**.
- `05-ui-ux-va-trang.md`: thêm màn hình 6b Ranking và 6c Hướng dẫn + component `HelpToc`, `OnboardingBanner`.
- `PHASE4-REPORT.md`: ghi nhận Ranking UI chuyển sang 5.4.

Không thay đổi quyết định D02 (4 màn hình lõi): Ranking dùng lại dữ liệu Phase 3.5, Help là trang phụ trợ.

---

## 14. Phase 6 — Playwright E2E toàn bộ use case (07/11/2026)

Yêu cầu: chắc chắn hệ thống chạy đúng với use case thực tế, không chỉ happy path.

Đã cập nhật tài liệu (không sửa mã nguồn):

- `TASKS.md` Phase 6:
  - **Bước 6.2 — Playwright E2E toàn bộ use case** (mới), deploy/monitoring/beta/gate dời thành 6.3–6.6.
  - Checklist: chuyển sang `@playwright/test`, 3 project (1440/1280/390), storageState admin/viewer,
    tag smoke/full, mock lỗi 401/500/timeout/429, theme, keyboard, flaky 3 lần, báo cáo `PHASE6-REPORT.md`.
  - Thời lượng Phase 6: 4–6 → **6–8 ngày**; tổng 33–47 → **37–51 ngày** (+buffer 44–61).
  - Gate bổ sung: P0 100%, P1 ≥ 95%, 0 flaky.
- `docs/kehoach/E2E-TEST-PLAN.md` (mới): ma trận **78 case** (A/S/D/C/R/K/H/T/N/X),
  cấu hình runner, dữ liệu test, mock, CI, quy tắc flaky và 6 gap cần xử lý (G1–G6).
- `06-kiem-thu-van-hanh-bao-mat.md`: thêm mục 5.6 tổng hợp Playwright theo nhóm + gate E2E.

Lưu ý: ranking/help cases (K/H) chỉ chạy được sau khi hoàn thành bước 5.4/5.5.

---

## 15. Phase 5 — triển khai

### 15.1. AI report 5.1

- Bảng `ai_reports` + `ai_usage` (migration 0012); prompt v1, schema Pydantic chặn lời khuyên đầu tư.
- Adapter OpenRouter: primary → fallback 1 lần → template; evidence_ids phải nằm trong allowlist.
- Budget ngày/tháng + cooldown 24h + dedupe `input_hash`; API admin analyze, user đọc report.
- **Quyết định:** đổi `.env` do gemma free bị 429:
  `AI_MODEL_PRIMARY=nvidia/nemotron-3.5-super-vl:free`,
  `AI_MODEL_FALLBACK=nvidia/nemotron-3-ultra-550b-a55b:free`.
- Live 1 call: 44,3s, primary fail schema → **fallback thành công**, cost 0, evidence đủ.
- UI: panel AI trong Trader Detail (badge primary/fallback/template, cost, latency, evidence).
- Test: 8 unit OpenRouter/schema/template + 2 integration API; E2E mock AI pass.

### 15.2. Settings & versioning 5.2

- `services/settings_service.py`: snapshot, tạo version scoring mới, preview impact, rollback, audit.
- API: `GET/PUT /settings`, `POST /settings/preview`, `GET /settings/versions`, `POST /settings/rollback/{v}`.
- Lưu AI override (model/budget/enabled) và chu kỳ collector vào `app_settings`; worker đọc lại mỗi vòng 60s.
- `audit_logs` (migration 0013): 10 bản ghi từ test/E2E; before/after JSON.
- UI `/settings`: 6 tab; admin sửa, viewer read-only; preview top thay đổi; versions + rollback.
- Test: 2 unit validation + 2 integration (version/preview/rollback/audit/RBAC); E2E preview/save/rollback pass.
- Bug đã sửa: preview thiếu key `metrics`; test giả định version tăng 1 (thực tế max+1).

### 15.3. Hardening 5.3

- `services/crypto.py`: Fernet key derive SHA-256 từ `JWT_SECRET`; API key lưu mã hoá, chỉ trả masked.
- Rate limit API 100/phút/user (middleware theo JWT sub, fallback IP); login giữ 5/phút/IP.
- `/metrics` Prometheus: request count/latency + collector last success; `infra/prometheus-alerts.yml`.
- Nginx: CSP, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy (đã kiểm header thật).
- Backup: `infra/backup.sh` + `scripts/backup.ps1`; dump thật 65 MB; restore sang DB tạm 11.185 trader OK.
- Tách `backend/requirements-dev.txt` để pip-audit production sạch; nâng cryptography lên 50.x.
- `pip-audit` 0 lỗi; `npm audit` 0 lỗi; CI thêm scan.
- Bug đã sửa: `param()` phải đứng trước mọi lệnh trong script PowerShell.

### 15.4. Ranking UI 5.4

- API `GET /ranking?board=...` đọc snapshot mới nhất + `config_version`; `POST /ranking/run` (admin).
- Tự rebuild score nếu version active chưa có `trader_scores` (tránh bảng rỗng sau khi đổi config).
- UI `/ranking`: 3 tab, metadata snapshot, bảng 9 cột, link Detail, empty + nút chạy (admin).
- Test: 1 integration contract (3 board + 422 + RBAC + run); E2E render 2 tab.
- Bug đã sửa: E2E 502 do Nginx cache DNS khi backend recreate → restart nginx.

### 15.5. Trang hướng dẫn 5.5

- Nội dung: `docs/huong-dan-nguoi-moi.md` (8 mục), render tại `/help`, không dùng dữ liệu live.
- Mục lục: sticky, active highlight theo scroll, thanh tiến độ đọc, drawer mobile, nút về đầu trang.
- Tìm kiếm client-side theo tiêu đề + keyword (sharpe, mdd, tier, risk…); print CSS + nút In/PDF.
- **5 hình minh hoạ SVG** (`HelpIllustrations.tsx`): luồng copy trading, phễu tier, cấu trúc metric card,
  risk event + evidence, quy trình 5 bước; dùng theme token, caption tiếng Việt.
- Banner “Mới bắt đầu?” trên Screener, dismiss lưu `ct_help_banner_dismissed` (E2E kiểm reload).
- Mobile: thêm menu drawer cho toàn app (giải quyết gap G1); header gọn lại.
- E2E: Help 8 mục, ≥4 figure, TOC ≥8 link, anchor `#glossary`, search, banner persist.

### 15.6. QA & gate Phase 5

| Kiểm tra | Kết quả |
|---|---|
| Backend container | **114 passed** |
| ruff / build / check_refs | Pass / Pass / 174-0 |
| E2E full | 13 checkpoint PASS |
| AI live | 44,3s, fallback, cost 0, 15 evidence |
| Settings versions / audit | 17 version · 34 audit rows |
| Rate limit API | 429 đúng ngưỡng (test) |
| Key at-rest | Fernet; không lộ trong response/DB |
| Backup / restore | 65 MB · 11.185 trader |
| Ranking / Help | 3 board · 8 mục + 5 SVG |
| pip-audit / npm audit | 0 / 0 |
| Báo cáo | `docs/kehoach/PHASE5-REPORT.md` |

**Gate Phase 5: ĐẠT.**

### 15.7. Việt hóa giao diện 5.7

- Quyết định: UI 100% tiếng Việt; backend giữ mã tiếng Anh; giữ “Trader”; tier UI `Cao (A)/Đạt (B)/Theo dõi (C)/Bị loại`.
- Nhãn tập trung tại `frontend/src/i18n/vi.ts`: tier, band, risk, severity, model role, job, source,
  layer, hard flag, filter reason, R01–R11, nhóm điểm, board, metric.
- Đã Việt hóa Layout/Login/Home/Banner/Screener/Detail/AI/Compare/Risk/Ranking/Data Health/Settings/Help.
- CSV header đổi sang tiếng Việt (`Mã trader`…); test `test_screener_api` cập nhật.
- AI prompt **v2** + template **v2**: trả tiếng Việt, mỗi nhận định có chỉ số + giá trị + ý nghĩa/ngưỡng;
  template fallback cũng phân tích, không liệt kê chung chung.
- `parse_json` đọc được JSON kèm text phía sau; tắt reasoning để model free trả content.
- Validator yêu cầu summary ≥2 số, mỗi danh sách strengths/weaknesses có ít nhất 1 số.
- AI live: fallback `nemotron-3-ultra` trả report v2 tiếng Việt, có ROI/MDD/Sharpe/leverage, trade-off,
  không có lời khuyên đầu tư; primary vẫn có lúc thiếu field → fallback.
- Test: backend **117 passed**; ruff pass; E2E 13 checkpoint; check_refs 174/0.
- Chưa push.

### 15.8. Trang Tài liệu kỹ thuật 5.8

- Route `/technical`, menu `Tài liệu kỹ thuật`, lazy-load để tách chunk khỏi bundle chính.
- Nội dung tách 20 file `docs/ky-thuat/*.md` + 20 section TSX; `manifest.ts` là nguồn cấu trúc.
- `scripts/check_tech_docs.py` kiểm tra 20 ID/thứ tự/title/group khớp docs và đủ section TSX.
- TOC 2 cấp tự sinh từ heading, search, group filter, anchor, active, progress, mobile drawer, print.
- 3 SVG kỹ thuật: kiến trúc, pipeline dữ liệu, scoring.
- E2E: technical docs render, TOC ≥ 20, anchor `#tier`, search, mobile drawer, không overflow ngang.

## 16. Risk V2 spec-only (07/11/2026)

- Vấn đề: scoring v1 không có `sharpe` trong components → 90 điểm + Sharpe âm vẫn `low_risk` được.
- Quyết định: veto Sharpe âm → `>=high` + cấm `low_risk` + cap score `<=54`; giữ enum UI; `risk_score = 30*MDD+20*Lev+15*Sharpe+15*Conc+10*Qual+10*Copy`.
- Artifact: `docs/0/02-ke-hoach-risk-v2.md`, `docs/kehoach/RISK-V2-SPEC.md`; `TASKS.md` bổ sung mục Risk V2.
- Đã implement 07/11/2026: `risk_rules.py` R01–R19 + `risk_score/veto/low_risk_eligible`; migration `0014_risk_v2` (`risk_score`, `risk_veto`); `risk_service` lưu score/veto; `ranking.low_risk` cấm Sharpe âm/null (ngoại lệ Sharpe 0–0.5 chỉ khi mdd≤15+lev≤3+runtime≥180); `trader_detail/risk` trả score/veto; `vi.ts` + Settings R12–R19; test `test_risk_v2` 9 pass, full backend 94 pass, frontend build OK.
- Chưa chạy backfill live; cần `alembic upgrade head` + `collector_cli risk/rank` ở bước vận hành.
