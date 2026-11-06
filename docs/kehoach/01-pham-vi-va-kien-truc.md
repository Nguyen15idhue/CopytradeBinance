# 01 — PHẠM VI & KIẾN TRÚC HỆ THỐNG

> Thuộc bộ kế hoạch `docs/kehoach/`  
> Đọc kèm: `README.md`, `02-data-contract-binance.md`

---

## 1. Kiến trúc logic

```
┌──────────────────────────────────────────────────────────────┐
│                        NGƯỜI DÙNG                            │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼──────────────────────────────────┐
│  Nginx (reverse proxy, TLS, static frontend, rate limit)      │
└───────────────┬──────────────────────────────┬───────────────┘
                │ /api/v1                      │ /*
┌───────────────▼──────────────┐   ┌───────────▼───────────────┐
│  FastAPI Backend             │   │  React SPA (Vite build)   │
│  - API Layer                 │   │  - Screener               │
│  - Services                  │   │  - Trader Detail          │
│  - Scheduler                 │   │  - Compare                │
│  - AI Orchestrator           │   │  - Settings/Data Health   │
└───────┬──────────────┬───────┘   └───────────────────────────┘
        │              │
┌───────▼───────┐  ┌───▼──────────────────────┐
│ PostgreSQL    │  │ Binance BAPI (external)  │
│ raw + derived │  │ 6 endpoint groups        │
└───────┬───────┘  └──────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│ JSONL Archive (append-only, filesystem/S3-compatible)        │
│ Mỗi trader 1 dòng sau khi crawl xong → resume/idempotent      │
└──────────────────────────────────────────────────────────────┘
```

### Nguyên tắc

1. **Raw trước, derived sau.**
   Snapshot thô từ Binance không bị sửa. Quant Engine đọc raw, ghi derived.
2. **Append-only.**
   Không update đè snapshot cũ. Mọi thay đổi lịch sử là một bản ghi mới.
3. **Idempotent.**
   Chạy lại collector không tạo bản ghi trùng.
4. **Versioned.**
   Scoring config, metric formula, prompt đều có version.
5. **Fail-soft.**
   AI lỗi không làm dừng collector/quant/scoring.
6. **Phễu trước, deep-fetch sau.**
   List scan rộng và rẻ; chỉ deep-fetch trader có tiềm năng. Không crawl lịch sử của trader không giao dịch, quá mới, lỗ, ít lệnh, hoặc không còn slot copy.

---

## 2. Stack

| Thành phần | Công nghệ | Ghi chú |
|---|---|---|
| Frontend | React + Vite + TypeScript | SPA |
| UI | Tailwind CSS + shadcn/ui hoặc Radix | Không tự viết design system |
| Chart | ECharts | Equity, drawdown, ROI, distribution |
| Data fetching | TanStack Query | Cache, loading, error, retry |
| Table | TanStack Table | Virtualized cho shortlist ~700; universe 11k khi cần |
| Backend | Python 3.12+ + FastAPI | Async |
| HTTP client | httpx | Async, timeout, retry |
| ORM | SQLAlchemy 2.x | Async session |
| Migration | Alembic | Versioned schema |
| Validation | Pydantic v2 | Request/response + AI JSON |
| Scheduler | APScheduler | 60 phút/lần |
| Database | PostgreSQL 16 | JSONB cho raw |
| Retry | tenacity | Backoff 11012005 |
| Logging | structlog | JSON logs |
| Metrics | prometheus-fastapi-instrumentator | /metrics |
| Test | pytest + respx | Unit + contract |
| Deploy | Docker Compose + Nginx | 1 VPS |
| AI | LLM API (OpenAI/Anthropic/khác) | Adapter pattern |

---

## 3. Cấu trúc repository

```
copytrade-binance/
├── AGENTS.md
├── TASKS.md
├── SESSION.md
├── README.md
├── docker-compose.yml
├── .env.example
│
├── docs/
│   └── kehoach/                 # bộ tài liệu này
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── dashboard.py
│   │   │   │   ├── traders.py
│   │   │   │   ├── ranking.py
│   │   │   │   ├── compare.py
│   │   │   │   ├── ai.py
│   │   │   │   ├── risk.py
│   │   │   │   ├── settings.py
│   │   │   │   ├── collector.py
│   │   │   │   └── data_quality.py
│   │   ├── services/
│   │   │   ├── collector/
│   │   │   │   ├── base.py          # Adapter interface
│   │   │   │   ├── binance_bapi.py  # Adapter chính
│   │   │   │   ├── csv_import.py    # Fallback
│   │   │   │   └── demo.py          # Fixture
│   │   │   ├── quant/
│   │   │   ├── risk/
│   │   │   ├── scoring/
│   │   │   ├── ranking/
│   │   │   ├── ai/
│   │   │   └── data_quality/
│   │   ├── repositories/
│   │   └── scheduler/
│   ├── migrations/
│   ├── tests/
│   │   ├── unit/
│   │   ├── contract/
│   │   ├── integration/
│   │   └── fixtures/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── features/
│   │   │   ├── screener/
│   │   │   ├── trader-detail/
│   │   │   ├── compare/
│   │   │   ├── settings/
│   │   │   └── ai-report/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   ├── Dockerfile
│   └── package.json
│
└── infra/
    └── nginx/
        └── nginx.conf
```

---

## 4. Module backend

| Module | Trách nhiệm | Không làm |
|---|---|---|
| **Collector** | Gọi BAPI, validate, lưu raw, ghi log | Không tính điểm |
| **Universe** | Pre-filter, tier, `pre_score`, quyết định deep fetch | Không chấm score cuối |
| **Quant** | Tính metrics từ raw | Không quyết định ranking |
| **Risk** | Sinh risk events, hard filters | Không sửa score |
| **Scoring** | Tính score theo config version | Không gọi AI |
| **Ranking** | Xếp hạng theo bảng + snapshot | Không tự đổi filter |
| **AI** | Giải thích, phản biện, evidence | Không sửa score |
| **Data Quality** | Confidence, missing, stale, anomaly | Không chặn collector |
| **Settings** | CRUD config, version, audit | Không lưu secret dạng plaintext |

### Luồng xử lý

```
[Scheduler 60']
    → Collector.scan_list(PUBLIC + SIGNAL)
    → RawSnapshot (JSONB + JSONL)
    → Universe.prefilter()  → tier + pre_score
    → Collector.deep_fetch(shortlist)
    → Quant.compute()
    → DataQuality.evaluate()
    → Risk.evaluate()
    → Scoring.compute(config_version)
    → Ranking.snapshot()
    → (optional) AI.analyze()
    → API / Frontend
```

Nếu AI lỗi: bỏ qua AI, các bước trước vẫn hoàn tất.

---

## 5. Database schema

### 5.1. Nhóm danh tính & cấu hình

```sql
users (
  id uuid pk,
  email text unique not null,
  password_hash text not null,
  role text not null check (role in ('admin','viewer')),
  is_active boolean default true,
  created_at timestamptz,
  last_login_at timestamptz
)

sessions (
  id uuid pk,
  user_id uuid fk,
  refresh_token_hash text,
  expires_at timestamptz,
  revoked_at timestamptz
)

app_settings (
  id uuid pk,
  key text unique not null,
  value jsonb not null,
  version int not null,
  updated_by uuid,
  updated_at timestamptz
)

scoring_config_versions (
  id uuid pk,
  version int unique not null,
  weights jsonb not null,
  normalization jsonb not null,
  hard_filters jsonb not null,
  created_by uuid,
  created_at timestamptz,
  is_active boolean default false
)

audit_logs (
  id bigserial pk,
  user_id uuid,
  action text not null,
  entity text not null,
  entity_id text,
  before jsonb,
  after jsonb,
  created_at timestamptz
)
```

### 5.2. Nhóm trader & snapshot

```sql
traders (
  lead_portfolio_id text pk,
  nickname text,
  nickname_translate text,
  avatar_url text,
  portfolio_type text,            -- PUBLIC | SIGNAL | PRIVATE
  status text,                    -- ACTIVE | CLOSED | ...
  description text,
  start_time timestamptz,
  last_trade_time timestamptz,
  futures_type text,
  init_invest_asset text,
  created_at timestamptz,
  updated_at timestamptz
)

trader_universe (
  lead_portfolio_id text pk references traders(lead_portfolio_id),
  potential_tier text not null,      -- excluded | watch | qualified | high
  pre_score numeric,
  filter_reasons jsonb,              -- lý do bị loại / thiếu dữ liệu
  last_list_seen_at timestamptz,
  last_performance_fetch_at timestamptz,
  last_detail_fetch_at timestamptz,
  last_positions_fetch_at timestamptz,
  last_trades_fetch_at timestamptz,
  deep_fetch_status text not null default 'pending',
  updated_at timestamptz
)

portfolio_snapshots (
  id bigserial pk,
  lead_portfolio_id text fk,
  collected_at timestamptz not null,
  collected_hour timestamptz not null,  -- truncate hour, dùng cho unique
  source text not null,                 -- bapi | csv | demo
  raw jsonb not null,
  schema_version int not null,
  created_at timestamptz,
  unique (lead_portfolio_id, collected_hour, source)
)
-- partition by range (collected_hour), mỗi tháng 1 partition

performance_metrics (
  id bigserial pk,
  lead_portfolio_id text fk,
  time_range text not null,        -- 7D | 30D | 90D | 180D
  collected_at timestamptz not null,
  roi numeric,
  pnl numeric,
  mdd numeric,
  copier_pnl numeric,
  win_rate numeric,
  win_orders int,
  total_orders int,
  sharpe numeric,
  raw jsonb,
  unique (lead_portfolio_id, time_range, collected_at)
)

trader_metrics_daily (
  id bigserial pk,
  lead_portfolio_id text fk,
  metric_date date not null,
  roi_cumulative numeric,
  source text,
  raw jsonb,
  unique (lead_portfolio_id, metric_date, source)
)
-- lấy từ chartItems; chỉ dùng cho shape, không dùng tính MDD tuyệt đối
```

### 5.3. Nhóm lịch sử giao dịch

```sql
position_history (
  id bigserial pk,
  lead_portfolio_id text fk,
  position_id text not null,
  symbol text,
  side text,
  leverage numeric,
  isolated text,                  -- Isolated | Cross
  opened_at timestamptz,
  closed_at timestamptz,
  avg_cost numeric,
  avg_close_price numeric,
  closing_pnl numeric,
  max_open_interest numeric,
  closed_volume numeric,
  roi numeric,
  status text,
  raw jsonb,
  unique (lead_portfolio_id, position_id)
)

trade_history (
  id bigserial pk,
  lead_portfolio_id text fk,
  trade_hash text not null,       -- hash vì API không có trade_id
  traded_at timestamptz,
  symbol text,
  side text,
  price numeric,
  fee numeric,
  fee_asset text,
  quantity numeric,
  quantity_asset text,
  realized_profit numeric,
  realized_profit_asset text,
  base_asset text,
  qty numeric,
  position_side text,
  active_buy boolean,
  raw jsonb,
  unique (lead_portfolio_id, trade_hash)
)

transfer_history (
  id bigserial pk,
  lead_portfolio_id text fk,
  transfer_hash text not null,
  transferred_at timestamptz,
  coin text,
  amount numeric,
  from_account text,
  to_account text,
  trans_type text,
  raw jsonb,
  unique (lead_portfolio_id, transfer_hash)
)
```

### 5.4. Nhóm phân tích & vận hành

```sql
risk_metrics (
  id bigserial pk,
  lead_portfolio_id text fk,
  computed_at timestamptz,
  max_leverage numeric,
  avg_leverage numeric,
  margin_mode text,
  avg_holding_hours numeric,
  max_holding_hours numeric,
  position_win_rate numeric,
  profit_factor numeric,
  payoff_ratio numeric,
  symbol_concentration numeric,
  fee_drag numeric,
  max_position_roi_negative numeric,
  unique (lead_portfolio_id, computed_at)
)

risk_events (
  id bigserial pk,
  lead_portfolio_id text fk,
  rule_id text not null,
  severity text not null,          -- critical | high | medium | low
  status text not null default 'open',
  evidence jsonb not null,
  detected_at timestamptz,
  resolved_at timestamptz
)

trader_scores (
  id bigserial pk,
  lead_portfolio_id text fk,
  config_version int not null,
  score numeric not null,
  component_scores jsonb not null,
  confidence numeric not null,
  computed_at timestamptz,
  unique (lead_portfolio_id, config_version, computed_at)
)

ranking_snapshots (
  id bigserial pk,
  ranking_type text not null,      -- overall | low_risk | consistency
  config_version int not null,
  time_range text not null,
  captured_at timestamptz,
  rows jsonb not null
)

data_quality_flags (
  id bigserial pk,
  lead_portfolio_id text fk,
  flag text not null,              -- stale | insufficient_history | missing_sharpe ...
  severity text,
  details jsonb,
  detected_at timestamptz
)

trader_labels (
  id bigserial pk,
  lead_portfolio_id text fk,
  label text not null,             -- suspicious_dca | high_leverage | tradfi ...
  confidence numeric,
  evidence jsonb,
  detected_at timestamptz
)

ai_reports (
  id uuid pk,
  lead_portfolio_id text fk,
  time_range text,
  model text,
  prompt_version text,
  input_hash text,
  report jsonb not null,
  cost_usd numeric,
  created_at timestamptz
)

ai_usage (
  id bigserial pk,
  report_id uuid,
  provider text,
  model text,
  input_tokens int,
  output_tokens int,
  cost_usd numeric,
  created_at timestamptz
)

benchmark_prices (
  id bigserial pk,
  symbol text not null,            -- BTCUSDT | ETHUSDT
  price_date date not null,
  close numeric not null,
  unique (symbol, price_date)
)

collection_logs (
  id bigserial pk,
  run_id uuid,
  started_at timestamptz,
  finished_at timestamptz,
  status text,                     -- success | partial | failed
  total_traders int,
  fetched int,
  inserted int,
  updated int,
  errors int,
  details jsonb
)
```

### 5.5. Bảng defer (không làm MVP)

- `paper_copy_sessions`
- `paper_copy_equity`
- `ai_agents` (không cần multi-agent)

---

## 6. API v1

Tất cả dưới `/api/v1`. Response wrapper:

```json
{
  "data": {},
  "meta": { "request_id": "...", "generated_at": "..." },
  "error": null
}
```

Lỗi:

```json
{
  "data": null,
  "error": { "code": "TRADER_NOT_FOUND", "message": "...", "details": {} }
}
```

### 6.1. Trader & screener

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/traders` | Danh sách + filter + sort + pagination |
| GET | `/traders/{id}` | Hồ sơ trader |
| GET | `/traders/{id}/performance` | Metrics theo 7D/30D/90D/180D |
| GET | `/traders/{id}/positions` | Position history (paginated) |
| GET | `/traders/{id}/trades` | Trade history (paginated) |
| GET | `/traders/{id}/transfers` | Transfer history |
| GET | `/traders/{id}/risk` | Risk metrics + events + flags |
| GET | `/traders/{id}/score` | Score + breakdown + confidence |

Query params cho `/traders`:

```
q, portfolio_type, status,
potential_tier,                  -- excluded | watch | qualified | high
min_pre_score,
min_roi_90d, max_roi_90d,
max_mdd_90d,
min_sharpe, max_sharpe,
min_win_rate, max_win_rate,
min_runtime_days,
min_total_orders,
min_copiers, min_copy_aum,
max_leverage,
risk_level,
include_excluded,                -- false mặc định
sort_by, sort_dir,
page, page_size (max 100)
```

Endpoint bổ sung:

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/universe/summary` | Số lượng theo tier, lý do loại, lần chạy cuối |
| GET | `/universe/traders` | Danh sách trader trong phễu, kể cả excluded |
| POST | `/universe/recompute` | Tính lại tier/pre_score (admin) |

Response phải trả kèm `total`, `page`, `page_size`, `filter_summary`.

### 6.2. Ranking & compare

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/ranking?type=overall&time_range=90D` | Bảng xếp hạng |
| POST | `/compare` | So sánh 2–4 trader |
| GET | `/compare/correlation?ids=...` | Correlation matrix |

### 6.3. Dashboard & data health

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/dashboard/overview` | KPIs + chart data |
| GET | `/data-quality/summary` | Coverage, null rates, stale |
| GET | `/data-quality/traders/{id}` | Flags của 1 trader |
| GET | `/collector/status` | Lần chạy cuối, trạng thái |
| POST | `/collector/run` | Chạy thủ công (admin) |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus |

### 6.4. AI & settings

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/ai/analyze/{id}` | Tạo báo cáo (admin) |
| GET | `/ai/reports/{id}` | Danh sách báo cáo |
| GET | `/ai/reports/{id}/{report_id}` | Chi tiết |
| GET | `/settings` | Đọc config |
| PUT | `/settings` | Cập nhật config (admin, tạo version) |
| GET | `/settings/versions` | Lịch sử version |
| POST | `/settings/rollback/{version}` | Rollback (admin) |

---

## 7. Collector design

### 7.1. Adapter interface

```python
class DataSourceAdapter(Protocol):
    async def list_traders(self, time_range: str, page: int) -> Page
    async def get_detail(self, portfolio_id: str) -> dict
    async def get_performance(self, portfolio_id: str, time_range: str) -> dict
    async def get_positions(self, portfolio_id: str, page: int) -> Page
    async def get_trades(self, portfolio_id: str, page: int) -> Page
    async def get_transfers(self, portfolio_id: str, page: int) -> Page
```

Implementations:

- `BinanceBapiAdapter` — chính.
- `CsvImportAdapter` — fallback khi BAPI chết.
- `DemoAdapter` — fixture cho test/dev.

### 7.2. Chu kỳ thu thập — phễu 3 tầng

**Không deep-fetch toàn bộ.** Collector chạy theo phễu:

| Tầng | Việc | Tần suất | Khối lượng |
|---|---|---|---|
| **L0 — Universe scan** | Quét list PUBLIC + SIGNAL, **chỉ 90D** | 60 phút | 11.130 trader, ~371 trang |
| **L1 — Pre-filter** | Lọc trên field list, tính `pre_score`, gán tier | Sau L0 | ~517 Watch |
| **L2 — Performance** | Gọi `/performance` cho Watch | 2–6 giờ/lần | ~517 |
| **L3 — Detail + positions + transfers** | Chỉ Qualified + Watch nổi bật | 6–24 giờ/lần | ~113–313 |
| **L4 — Full trade history** | Chỉ High + top Qualified | 24 giờ/lần | ~13–50 |
| **L5 — Scoring/ranking** | Tính score, chụp ranking | Sau L2–L4 | Toàn bộ shortlist |
| **L6 — AI report** | Theo trigger | Manual / Significant Change | 0–20/ngày |

### 7.2.1. Quy tắc tier

| Tier | Điều kiện | Deep fetch |
|---|---|---|
| **Excluded** | Không có trade 7D, runtime < 30, ROI ≤ 0, PnL ≤ 0, WR < 40, MDD > 40, AUM < 5k, full slot | Không |
| **C — Watch** | Runtime ≥ 30, ROI > 0, PnL > 0, WR ≥ 40, MDD ≤ 40, AUM ≥ 5k, còn slot | Performance + detail giới hạn |
| **B — Qualified** | Runtime ≥ 90, ROI ≥ 10, WR ≥ 45, MDD ≤ 30, AUM ≥ 10k, Sharpe ≥ 0.5/null, orders ≥ 50 | Detail + positions + transfers |
| **A — High** | Runtime ≥ 180, ROI ≥ 20, WR ≥ 50, MDD ≤ 20, AUM ≥ 20k, Sharpe ≥ 1, orders ≥ 100 | Full trades + AI |

`pre_score` chỉ dùng để xếp thứ tự deep fetch, không phải score cuối.  
Công thức: xem `02-data-contract-binance.md` mục 3.1.7.

### 7.2.2. Trạng thái deep fetch

Mỗi trader trong `trader_universe` có:

- `potential_tier`: `excluded | watch | qualified | high`
- `pre_score`: numeric
- `filter_reasons`: jsonb (lý do bị loại)
- `last_list_seen_at`
- `last_performance_fetch_at`
- `last_detail_fetch_at`
- `last_positions_fetch_at`
- `last_trades_fetch_at`
- `deep_fetch_status`: `pending | partial | complete | failed`

> Trader bị loại vẫn lưu list record để audit và có thể xuất hiện lại ở chu kỳ sau. Không xóa.

### 7.3. Chống trùng & resume

- List: dedupe theo `leadPortfolioId`, lưu `collected_hour`.
- Universe: unique `lead_portfolio_id`; lưu `potential_tier`, `pre_score`, `filter_reasons`.
- Deep fetch: trạng thái riêng theo từng tầng (`performance`, `detail`, `positions`, `trades`).
- Detail: unique `(portfolio_id, collected_hour, source)`.
- Position: unique `(portfolio_id, position_id)`.
- Trade: hash `(time, symbol, side, price, qty, fee)` → `trade_hash`.
- Transfer: hash `(time, coin, amount, trans_type)` → `transfer_hash`.
- JSONL: ghi sau mỗi trader; chạy lại chỉ crawl trader chưa có.
- Nếu list total thay đổi giữa các trang: chấp nhận snapshot, dedupe, ghi log `partial` nếu thiếu > 1%.

### 7.4. Rate limit & retry

```
- list: 30/page
- trade-history: 200/page
- position-history: 50/page (khuyến nghị)
- transfer-history: 50/page
- concurrency: 6–8
- backoff: 2 → 4 → 8 → 16s
- mã rate limit: 11012005
- timeout: 20s/request
- retry tối đa: 5
```

### 7.5. Scheduler

- APScheduler chạy trong **một process duy nhất**.
- Nếu scale > 1 instance: dùng PostgreSQL advisory lock `pg_try_advisory_lock`.
- Không chạy scheduler trong mỗi uvicorn worker; tách container `scheduler` hoặc `--workers 1`.
- Job lock ghi vào `collection_logs`; job đang chạy thì bỏ qua lần tiếp theo.

---

## 8. Security

| Hạng mục | Yêu cầu |
|---|---|
| Password | Argon2id hoặc bcrypt cost ≥ 12 |
| Session | JWT access 15 phút + refresh 7 ngày, refresh rotate |
| RBAC | Admin (settings, collector run, AI) / Viewer (read-only) |
| API key AI | Mã hóa at rest (Fernet/KMS), không trả về browser |
| CORS | Chỉ domain frontend |
| Rate limit | Login 5/phút/IP; API 100/phút/user |
| Audit | Mọi thay đổi settings, scoring, risk rule |
| Secrets | `.env` + Docker secrets, không commit |
| SQL injection | SQLAlchemy parameterized, không raw string |
| XSS | React escape mặc định, không `dangerouslySetInnerHTML` |
| Backup | Daily, mã hóa, retention 30 ngày |
| Logs | Không log API key, token, password |

---

## 9. Deployment

### docker-compose services

```yaml
services:
  db:        postgres:16
  backend:   build ./backend
  scheduler: build ./backend, command: python -m app.scheduler
  frontend:  build ./frontend
  nginx:     nginx:alpine
```

### Yêu cầu VPS tối thiểu

| Thành phần | MVP | Ghi chú |
|---|---|---|
| CPU | 2 vCPU | Đủ cho list scan 11k + shortlist ~500 |
| RAM | 4 GB | PostgreSQL + backend |
| Disk | 50 GB SSD | Raw JSONL + DB + backup (giảm nhờ phễu) |
| Bandwidth | 2 TB/tháng | List scan 11k + deep fetch shortlist |

### Backup

- `pg_dump` daily 02:00 UTC.
- JSONL archive sync daily.
- Test restore mỗi tháng.
- Giữ 7 bản daily + 4 bản weekly.

---

## 10. Những điểm không làm trong MVP

- Không deep fetch trader `excluded`.
- Không gọi full trade-history cho toàn bộ shortlist.
- Không cache Redis; dùng PostgreSQL + in-memory cache ngắn hạn nếu cần.
- Không message queue; scheduler + DB lock là đủ.
- Không WebSocket; polling 60 giây ở frontend nếu cần.
- Không multi-tenant; 1 admin + vài viewer.
- Không mobile app; responsive web là đủ.
- Không auto trading; tuyệt đối không lưu API key có quyền giao dịch.
