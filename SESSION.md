# SESSION â€” Phase 0 & Phase 1

> **NgĂ y:** 2026-11-06  
> **Tráº¡ng thĂ¡i:** Phase 0 hoĂ n táº¥t â€” **GO CĂ“ ÄIá»€U KIá»†N**  
> **Sáº£n pháº©m:** Binance Copy Trader Screener & Risk Analytics (khĂ´ng auto-trade)

---

## 1. Má»¥c tiĂªu phiĂªn

1. XĂ¡c minh 6 endpoint BAPI báº±ng dá»¯ liá»‡u tháº­t.
2. Chá»‘t universe PUBLIC + SIGNAL vĂ  phá»…u C/B/A/Excluded.
3. Äo false negative cá»§a bá»™ lá»c.
4. Kiá»ƒm chá»©ng cĂ¡c báº«y chá»‰ sá»‘ (MDD, WinRate, Sharpe, AUM, Copier PnL, fee).
5. Ra quyáº¿t Ä‘á»‹nh go/no-go cho Phase 1.

---

## 2. Káº¿t quáº£ chĂ­nh

| Háº¡ng má»¥c | Káº¿t quáº£ |
|---|---|
| Universe | **11.124** = 8.970 PUBLIC + 2.154 SIGNAL, coverage 100% |
| Watch (C, gá»“m B/A) | **515** (457 PUBLIC + 58 SIGNAL) |
| Qualified gá»“m High (B+A) | **109** (99 + 10) |
| High (A) | **13** (13 + 0) |
| Excluded | **10.609** |
| Máº«u deep fetch | **63** (A=13, B=20, C=20, excluded=10) |
| Deep fetch | 63/63 OK, 153,34s, 0 lá»—i |
| False negative thá»±c | **0/50 = 0%** (`fn_watch_eligible`) |
| False negative literal | 12/50 = 24% (do thiáº¿u AUM/MDD trong Ä‘á»‹nh nghÄ©a) |
| Activity proxy | 60/63 khá»›p (95,2%), 3 FP, 0 FN |
| Rate limit | 32 request, 0 bá»‹ cháº·n, 0 lá»—i |

---

## 3. Quyáº¿t Ä‘á»‹nh quan trá»ng

### D-MDD â€” Nguá»“n MDD

- **Hiá»ƒn thá»‹/xáº¿p háº¡ng:** `performance.mdd` (published).
- **Audit:** `equity = 1 + chartItems.value / 100`, khá»›p published **63/63**, sai sá»‘ max **4,9 Ă— 10â»â· pp**.
- Con sá»‘ **88,67%** cÅ© lĂ  **lá»—i cĂ´ng thá»©c** (coi ROI lÅ©y káº¿ lĂ  equity), khĂ´ng pháº£i lá»—i `chartItems`.
- MDD **phá»¥ thuá»™c window**: chá»‰ 6/63 trader giá»‘ng nhau á»Ÿ 4 window; chĂªnh tá»‘i Ä‘a 70,26 pp.

### D-ACT â€” Activity

- List payload **khĂ´ng cĂ³** `lastTradeTime`.
- Proxy `traded_last_7d` khĂ´ng bá» sĂ³t trader Ä‘ang trade (0 FN) nhÆ°ng cĂ³ thá»ƒ giá»¯ trader Ä‘Ă£ ngá»«ng (3 FP).
- Báº¯t buá»™c xĂ¡c minh `detail.lastTradeTime` trÆ°á»›c khi ranking.

### D-WR â€” WinRate

- `winRate` = theo order; khĂ¡c position-level.
- 59/63 so sĂ¡nh Ä‘Æ°á»£c; median lá»‡ch 2,52 pp; 18 ca lá»‡ch > 5 pp; max 33,33 pp.
- Pháº£i hiá»ƒn thá»‹ tĂ¡ch biá»‡t.

### D-NULL â€” Sharpe

- Null 34,9% universe, 4,8% sample.
- Hiá»ƒn thá»‹ `N/A`, khĂ´ng cháº¥m 0.

### D-FEES â€” Fee

- 56/58 trader cĂ³ fee Ă¢m; tá»•ng page 1 = âˆ’5.835,4656.
- Rebate lĂ  bĂ¬nh thÆ°á»ng; khĂ´ng cá»™ng fee nhÆ° chi phĂ­ dÆ°Æ¡ng.

### D-SCOPE â€” Endpoint thiáº¿u

- 6/6 probe tráº£ 404: open positions, copier list, funding.
- KhĂ´ng cam káº¿t cĂ¡c tĂ­nh nÄƒng nĂ y trong MVP.

---

## 4. Artifact

- `phase0/PHASE0_REPORT.md` â€” bĂ¡o cĂ¡o Ä‘áº§y Ä‘á»§.
- `phase0/data/universe_90d.jsonl` â€” 11.124 trader.
- `phase0/data/tier_summary.csv` â€” phá»…u theo nguá»“n.
- `phase0/data/sample_manifest.csv` â€” 63 trader máº«u.
- `phase0/data/audit_summary.json` â€” false negative.
- `phase0/data/indicator_quality_summary.json` â€” kiá»ƒm chá»©ng chá»‰ sá»‘.
- `phase0/data/rate_limit_summary.json` â€” rate limit.
- `phase0/data/raw/` â€” raw bundle.

**Giá»›i háº¡n dá»¯ liá»‡u Ä‘Ă£ fetch:** positions 13.589/22.641 dĂ²ng (7 trader bá»‹ cap 1.000 vá»‹ tháº¿ gáº§n nháº¥t); trades chá»‰ page 1 (10.967/112.759 dĂ²ng); transfers Ä‘áº§y Ä‘á»§ 2.063/2.063.

Scripts:

- `phase0/fetch.py`, `tiering.py`, `scan_universe.py`, `recompute_summary.py`
- `phase0/sample.py`, `deep_fetch.py`, `activity_check.py`
- `phase0/audit_excluded.py`, `indicator_checks.py`, `rate_limit_test.py`

---

## 5. TĂ i liá»‡u Ä‘Ă£ sá»­a

- `docs/kehoach/02-data-contract-binance.md` â€” Ä‘Ă­nh chĂ­nh MDD, thĂªm quy táº¯c audit.
- `docs/kehoach/03-bo-chi-so-va-scoring.md` â€” sá»­a cáº£nh bĂ¡o cĂ´ng thá»©c MDD.
- `docs/kehoach/06-kiem-thu-van-hanh-bao-mat.md` â€” acceptance test MDD.
- `docs/kehoach/07-rui-ro-phap-ly-va-du-phong.md` â€” mĂ´ táº£ flow distortion Ä‘Ăºng.
- `docs/kehoach/08-nhat-ky-quyet-dinh.md` â€” sá»­a D06 + phĂ¡t hiá»‡n #6.
- `docs/kehoach/data-availability-matrix.csv` â€” thĂªm giá»›i háº¡n list/detail, audit MDD.
- `docs/kehoach/TASKS.md` â€” cáº­p nháº­t tráº¡ng thĂ¡i Phase 0.

---

## 6. Viá»‡c tiáº¿p theo (Phase 1)

1. Dá»±ng backend + model theo contract Ä‘Ă£ chá»‘t.
2. Collector 2 táº§ng: list 90D â†’ detail/performance cho Watch.
3. LÆ°u `timeRange` cĂ¹ng má»i metric.
4. Hiá»ƒn thá»‹ MDD published + nhĂ£n window.
5. Hiá»ƒn thá»‹ WinRate order vĂ  position tĂ¡ch biá»‡t.
6. Sharpe null â†’ `N/A` + confidence.
7. KhĂ´ng Ä‘Æ°a open positions/per-copier/funding vĂ o MVP.

---

## 7. Cáº£nh bĂ¡o váº­n hĂ nh

- `performance` chá»‰ dĂ¹ng `BASE_P`.
- List page size tá»‘i Ä‘a 30; trade tá»‘i Ä‘a 200.
- Giá»¯ 5â€“6 worker; backoff khi 429/418.
- `total` cĂ³ thá»ƒ Ä‘á»•i giá»¯a cĂ¡c trang â†’ luĂ´n dedupe theo `leadPortfolioId`.
- `positionShow=false` **khĂ´ng** cháº·n position-history.
- Young portfolio: khĂ´ng giáº£ Ä‘á»‹nh 4 window giá»‘ng nhau; Ä‘Ă£ tháº¥y ca 29,98 ngĂ y khĂ¡c window.

---

## 8. Phase 1 â€” Foundation + vertical slice

### 8.1. Quyáº¿t Ä‘á»‹nh ká»¹ thuáº­t

- Backend: Python 3.12+, FastAPI async, SQLAlchemy 2.x async, Alembic.
- DB URL dĂ¹ng `postgresql+asyncpg://` cho app vĂ  migration.
- Frontend: React 18 + Vite 6 + TypeScript + Tailwind 3.
- Reverse proxy: Nginx, cá»•ng ngoĂ i **8080** (trĂ¡nh xung Ä‘á»™t cá»•ng 80).
- Compose gá»“m `db`, `backend`, `frontend`, `nginx`; volume `pgdata`.
- CI: GitHub Actions, backend ruff + pytest, frontend `npm ci && npm run build`.

### 8.2. Tráº¡ng thĂ¡i bÆ°á»›c

| BÆ°á»›c | Tráº¡ng thĂ¡i | Báº±ng chá»©ng |
|---|---|---|
| 1.1 Khá»Ÿi táº¡o repo & háº¡ táº§ng | `[x]` | compose up OK, `/health` OK, alembic OK, CI file cĂ³ |
| 1.2 Database & model | `[x]` | 4 báº£ng + migration `0001_core_tables`; downgrade/upgrade OK |
| 1.3 Auth & RBAC | `[x]` | JWT access/refresh, Argon2id, RBAC, rate limit 429 láº§n 6 |
| 1.4 Adapter + seed | `[x]`* | DemoAdapter 2 fixture; CSV stub; seed idempotent 2 traders/8 metrics/2 snapshots; *API null kiá»ƒm á»Ÿ 1.5 |
| 1.5 API trader detail | `[x]` | `/traders/{id}`: 10 metrics, tier, reasons, confidence, provenance; null giá»¯ null |
| 1.6 Frontend tá»‘i giáº£n | `[x]` | Login, layout, detail 10 metrics, excluded badge; E2E Playwright pass |
| 1.7 QA & gate | `[x]` | 12 test pass; clean compose; E2E; secret scan; downgrade OK |

### 8.3. Lá»‡nh kiá»ƒm tra 1.1

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

- 4 báº£ng lĂµi: `users`, `traders`, `portfolio_snapshots`, `performance_metrics`.
- `users.id` UUID; `traders.lead_portfolio_id` lĂ  text PK; snapshot/metric dĂ¹ng bigserial.
- `portfolio_snapshots.raw` vĂ  `performance_metrics.raw` dĂ¹ng JSONB.
- Unique: snapshot theo giá» + source; performance theo `(lead, time_range, collected_at)`.
- Migration `0001_core_tables`; Ä‘Ă£ test `downgrade base` â†’ `upgrade head`.

### 8.5. Auth 1.3

- Password hash: Argon2id (`argon2-cffi`).
- JWT HS256: access 15 phĂºt, refresh 7 ngĂ y; refresh rotate vĂ  lÆ°u hash trong `sessions`.
- Endpoint: `/api/v1/auth/login`, `/refresh`, `/logout`, `/me`; admin check `/api/v1/admin/ping`.
- Rate limit login 5/phĂºt/IP báº±ng SlowAPI (in-memory Phase 1; Redis á»Ÿ Phase 2).
- Seed: `python -m app.seed all` táº¡o `admin@example.com` vĂ  `viewer@example.com`.
- Smoke test: `scripts/smoke_auth.ps1`; rate limit: `scripts/test_rate_limit.ps1`.
- LÆ°u Ă½: script `.ps1` lÆ°u UTF-8 BOM, Ä‘áº·t `chcp 65001` Ä‘á»ƒ hiá»ƒn thá»‹ tiáº¿ng Viá»‡t.

### 8.6. Adapter & seed 1.4

- `DataSourceAdapter` Protocol, `DemoAdapter`, `CsvImportAdapter` stub.
- Fixture excluded: `5296057151807357697` (runtime 4,11 ngĂ y, AUM 1.200).
- Fixture qualified: `4520644381136785152` (B tier, ROI 19,19%, MDD 8,54%, Sharpe 2,84).
- ThĂªm báº£ng `trader_universe` (migration `0003`) lÆ°u tier/reason/pre_score.
- Seed idempotent: cháº¡y 2 láº§n váº«n 2 traders / 8 metrics / 2 snapshots.
- Null Ä‘Æ°á»£c giá»¯ nguyĂªn: excluded 90D cĂ³ `mdd=NULL`, `sharpe=NULL`.

### 8.7. API trader detail 1.5

- `GET /api/v1/traders/{id}` (báº¯t buá»™c access token).
- Tráº£ 10 chá»‰ sá»‘, `tier`, `reasons`, `pre_score`, `profile`, `confidence`, `flags`, `provenance`, `disclaimer`.
- Null giá»¯ null: excluded cĂ³ `mdd=null`, `sharpe=null`, flags `missing_sharpe`/`missing_mdd`.
- Derived chÆ°a cĂ³ dá»¯ liá»‡u (profit factor, avg holding) tráº£ `null` + flag `derived_unavailable`.
- 404 wrapper `TRADER_NOT_FOUND`; thiáº¿u token 401.
- Test: `scripts/smoke_trader.ps1` â†’ PASS.
- TĂ i liá»‡u API: `docs/api.md`.

### 8.8. Frontend 1.6

- React 18 + Vite + TypeScript + Tailwind; TanStack Query.
- Trang: `/login`, `/` (2 fixture), `/traders/:id`.
- Layout sidebar/topbar; hiá»ƒn thá»‹ user/role, nĂºt Ä‘Äƒng xuáº¥t, freshness demo.
- Detail: 10 metric cards, tier badge, excluded banner + reasons, risk flags, what's missing, provenance.
- Null hiá»ƒn thá»‹ `N/A`; copy AUM = 0 ghi â€œKhĂ´ng cĂ³ copierâ€.
- E2E: `cd frontend; npm run test:e2e` â†’ Ä‘Äƒng nháº­p, qualified, excluded, Ä‘Äƒng xuáº¥t, khĂ´ng console error.

### 8.9. QA & gate 1.7

| Kiá»ƒm tra | Káº¿t quáº£ |
|---|---|
| Backend test trong container | **12 passed** (11 unit + 1 integration) |
| Compose tá»« mĂ¡y sáº¡ch | `down -v` â†’ `up -d --build` OK, 4 service cháº¡y |
| Auth/RBAC | smoke PASS; viewer â†’ admin 403 |
| Trader qualified | tier qualified; ROI 19,19%; MDD 8,54%; Sharpe 2,84 |
| Trader excluded | banner + reason; MDD/Sharpe null |
| Null â‰  0 | API/UI giá»¯ `null` / `N/A` |
| Rate limit | láº§n 6 â†’ 429 |
| Migration | downgrade base â†’ upgrade head trĂªn volume má»›i |
| Secret scan | khĂ´ng track `.env`; khĂ´ng match pattern secret |
| Dependency scan | `npm audit --audit-level=high` â†’ 0 vulnerability |
| E2E frontend | Playwright PASS, 0 console error |

**Gate Phase 1: Äáº T.** Vertical slice cháº¡y end-to-end vá»›i 2 fixture.

---

## 9. Phase 2 â€” Collector 2 táº§ng + raw storage

### 9.1. Adapter 2.1

- `collector/http.py`: timeout 20s, retry `11012005`/5xx/timeout (tá»‘i Ä‘a 4, backoff 2â†’16s + jitter), circuit breaker 5 lá»—i liĂªn tiáº¿p/60s.
- `collector/binance.py`: 6 endpoint; list 30/trang, positions 50, trades 200, transfers 50; performance dĂ¹ng `BASE_P`.
- Test mock 9 ca (retry, 404 khĂ´ng retry, breaker) + smoke live 6 endpoint PASS.

### 9.2. Universe scan 2.2

- Live: 372 trang, PUBLIC 8.966 + SIGNAL 2.164 = **11.130**, duplicates 0, 129â€“139s.
- LÆ°u 11.130 `portfolio_snapshots(source='list')` + 372 file JSONL trong `data/raw/`.
- Redis lock `lock:collector:scan`, fallback `pg_try_advisory_lock`.
- Cháº¡y láº¡i trong cĂ¹ng giá»: snapshot khĂ´ng tÄƒng (idempotent theo giá»).

### 9.3. Tier & pre-score 2.3

- Q02: pre_score percentile trĂªn **má»™t cohort chung** `all` (PUBLIC+SIGNAL).
- TrÆ°á»›c khi cĂ³ `totalOrder`: watch 398, qualified_upper 97, high_upper 14, excluded 10.621; Watch tá»•ng 509.
- `tier_history` ghi khi tier Ä‘á»•i; recompute láº§n 2 `changed=0`.
- API `/universe/summary`, `/universe/traders`, `/universe/recompute` (admin).

### 9.4. Performance 4 window 2.4

- Live 509 trader Ă— 4 window = 2.036 metric, 0 lá»—i.
- HF04 háº¡ tier theo `totalOrder` 90D: **38 trader** bá»‹ háº¡ â†’ watch 429, qualified 73, high 7 (Qualified+High = 80).
- Sharpe null giá»¯ `NULL` (90D: 9 trader), mdd null giá»¯ `NULL` (1 trader).
- Upsert theo `(lead, time_range, collected_at)` vá»›i `collected_at` cáº¯t vá» giá» â†’ cháº¡y láº¡i khĂ´ng nhĂ¢n báº£n.

### 9.5. Detail + positions + transfers 2.5

- Target: 80 Qualified/High + top 200 Watch = **280 trader**; 0 ineligible.
- Live: **71.026 vá»‹ tháº¿**, **8.267 transfer**, 0 lá»—i.
- Position page size 50, tá»‘i Ä‘a 20 trang/trader (1.000 vá»‹ tháº¿) Ä‘á»ƒ cháº·n chi phĂ­.
- `positionShow=false` khĂ´ng cháº·n position-history (D25).
- LÆ°u `positions` unique `(lead, position_id)`, `transfers` unique `(lead, transfer_hash)`.
- Detail lÆ°u snapshot `source='detail'` theo giá».

### 9.6. Full trade history 2.6

- Target: 7 high + top 50 qualified = **57 trader**; 0 lá»—i.
- Fetch: 130.962 fill, lÆ°u **120.595** trade unique; 10.367 báº£n ghi trĂ¹ng bá»‹ hash loáº¡i.
- Pagination dá»«ng theo `total`, khĂ´ng break sá»›m; cap an toĂ n 500 trang/trader.
- Chá»‰ high/qualified cĂ³ trades; **watch/excluded = 0** (query kiá»ƒm chá»©ng).
- Gáº·p `11012005` tháº­t khi cháº¡y full trades: backoff 2â†’16s xá»­ lĂ½ háº¿t, 0 request tháº¥t báº¡i.
- Giáº£m burst: giá»›i háº¡n 3 trader Ä‘á»“ng thá»i cho trade-history (semaphore riĂªng).

### 9.7. Storage, scheduler, váº­n hĂ nh 2.7

- `worker` container cháº¡y `app.worker.scheduler`: scan 60 phĂºt, perf 6h, detail 12h, trades 24h.
- Lock Redis `lock:collector:scan|deep` (TTL 30 phĂºt) + fallback advisory lock; job trĂ¹ng bá»‹ `skipped`.
- API: `/collector/status`, `/run-scan`, `/run-deep` (202 + job_id), `/jobs/{id}`, `/kill-switch`.
- Kill switch: env `COLLECTOR_KILL_SWITCH` hoáº·c `app_settings['collector.enabled']`; táº¯t â†’ 409.
- LÆ°u Ă½ váº­n hĂ nh: náº¿u process cháº¿t giá»¯a chá»«ng, xĂ³a khĂ³a báº±ng `redis-cli DEL lock:collector:scan lock:collector:deep`.
- Raw archive: 372 file / 144 MB; nĂ©n sau 7 ngĂ y, xĂ³a sau 90 ngĂ y (`compress_older_than`, `purge_older_than`).
- `data_quality_flags`: `missing_sharpe`, `missing_mdd`, `low_sample` ghi tá»« L2.
- UI `/data-health`: tier cards, báº£ng láº§n cháº¡y 4 táº§ng, raw archive, job gáº§n nháº¥t; E2E pass.
- BAPI rate limit: gáº·p `11012005` (HTTP 200) vĂ  `429` tháº­t; Ä‘Ă£ thĂªm cooldown toĂ n cá»¥c + backoff 30â€“180s, trades cháº¡y 1 trader/láº§n, nghá»‰ 0,4s/trang.
- `recompute_universe` Ă¡p dá»¥ng láº¡i HF04 `totalOrder` Ä‘á»ƒ khĂ´ng xĂ³a demotion sau má»—i vĂ²ng scan.

### 9.8. QA & gate 2.8

| Kiá»ƒm tra | Káº¿t quáº£ |
|---|---|
| Coverage 1 run | 11.132 / 11.124 = **100,07%**, 372 trang, 0 lá»—i |
| Watch | **511** (watch 425 + qualified 76 + high 10) |
| Excluded deep fetch | 0 táº¡i thá»i Ä‘iá»ƒm chá»n; cĂ³ test riĂªng |
| Cháº¡y láº¡i 3 láº§n | counts giá»‘ng há»‡t, khĂ´ng duplicate |
| Resume sau restart | kill 35s â†’ cháº¡y láº¡i Ä‘á»§, duplicate trong giá» = 0 |
| Rate limit | mock 11012005/429/Retry-After + live 0 lá»—i |
| Chu ká»³ scan + shortlist | **181,3s** (< 15 phĂºt) |
| Full deep | 511 perf 38,7s + 278 detail 77,9s + 57 trades 134,2s = **250,8s** |
| Backend test (container) | **41 passed** |
| Build + E2E + audit + secret scan | Pass / 0 lá»—i |
| BĂ¡o cĂ¡o | `docs/kehoach/PHASE2-REPORT.md` |

**Gate Phase 2: Äáº T.**
