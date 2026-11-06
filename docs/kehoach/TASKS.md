# TASKS — CHECKLIST THỰC HIỆN

> Cập nhật trạng thái: `[ ]` chưa làm, `[~]` đang làm, `[x]` xong.  
> Mỗi task nhỏ ≤ 1 ngày. Nếu lớn hơn, tách nhỏ.

---

## Phase 0 — Data spike & pre-filter spec

- [ ] Tạo thư mục `data/raw/` và script `spike_fetch.py`.
- [ ] Fetch list `PUBLIC` 1 trang, lưu raw.
- [ ] Fetch list `SIGNAL` 1 trang, lưu raw.
- [ ] Fetch detail trader `5296057151807357697` (audit fixture).
- [ ] Fetch performance 7D/30D/90D/180D bằng `BASE_P`.
- [ ] Fetch position-history (8 bản ghi).
- [ ] Fetch trade-history page 1 (200 bản ghi).
- [ ] Fetch transfer-history (17 bản ghi).
- [ ] Chốt universe = PUBLIC + SIGNAL (11.130), bỏ PRIVATE mặc định.
- [ ] Viết hàm `traded_last_7d` từ `chartItems`.
- [ ] Viết pre-filter + tier C/B/A/Excluded.
- [ ] Chốt preset AUM: Broad 1k / Balanced 5k / Strict 10k.
- [ ] Chốt `pre_score` và thứ tự deep fetch.
- [ ] Kiểm tra counts: Watch 460/57, Qualified 103/10, High 13/0.
- [ ] Fetch **20 trader C + 20 trader B + 20 trader A + 10 excluded**, lưu JSONL.
- [ ] So sánh `traded_last_7d` với `lastTradeTime` trên 20 mẫu.
- [ ] Audit false negative: 50 trader excluded → gọi performance/detail.
- [ ] Đo rate limit: 1, 5, 10 request đồng thời.
- [ ] Đo thời gian: scan 11k, performance 517, detail 113–313, full trades 13.
- [ ] Xác nhận page size 30/200.
- [ ] Xác nhận `performance` dùng `BASE_P`.
- [ ] Viết `02-data-contract-binance.md` bản cuối.
- [ ] Cập nhật `data-availability-matrix.csv`.
- [ ] Quyết định go/no-go.
- [ ] Cập nhật `SESSION.md`.

**Gate:** 6 endpoint ổn định + 70 raw file + tiêu chí phễu + false negative < 5%.

---

## Phase 1 — Foundation + vertical slice

### Backend

- [ ] Khởi tạo repo, `.gitignore`, `.env.example`.
- [ ] `docker-compose.yml` với db/backend/frontend/nginx.
- [ ] FastAPI app + `/health`.
- [ ] Config bằng Pydantic Settings.
- [ ] SQLAlchemy async engine.
- [ ] Alembic init + migration đầu.
- [ ] Model `traders`.
- [ ] Model `portfolio_snapshots`.
- [ ] Model `performance_metrics`.
- [ ] Auth: register admin seed, login, JWT.
- [ ] RBAC admin/viewer.
- [ ] API `/api/v1/traders/{id}`.
- [ ] Seed 1 trader excluded (`5296057151807357697`) + 1 trader qualified.
- [ ] Hiển thị tier + lý do excluded trên Detail.

### Frontend

- [ ] Vite + React + TS + Tailwind.
- [ ] Layout + sidebar + topbar.
- [ ] Login page.
- [ ] Trader Detail tối giản.
- [ ] API client + TanStack Query.
- [ ] Loading/error state.

### QA

- [ ] 3 unit test.
- [ ] 1 integration test.
- [ ] Docker compose up thành công.
- [ ] Không có secret trong repo.

**Gate:** mở được trader thật end-to-end.

---

## Phase 2 — Collector 2 tầng + raw storage

### Adapter

- [ ] `DataSourceAdapter` interface.
- [ ] `BinanceBapiAdapter` list.
- [ ] `BinanceBapiAdapter` detail.
- [ ] `BinanceBapiAdapter` performance (`BASE_P`).
- [ ] `BinanceBapiAdapter` position-history.
- [ ] `BinanceBapiAdapter` trade-history (200/page).
- [ ] `BinanceBapiAdapter` transfer-history.
- [ ] Retry/backoff `11012005`.
- [ ] Timeout 20s, retry 5.

### Tầng 0 — Universe scan

- [ ] Scan list PUBLIC + SIGNAL, **chỉ 90D**.
- [ ] Dedupe theo `leadPortfolioId`.
- [ ] Lưu list snapshot.
- [ ] Không gọi detail/position/trade ở tầng này.

### Tầng 1 — Pre-filter

- [ ] Hàm `traded_last_7d`.
- [ ] Hàm `potential_tier`.
- [ ] Hàm `pre_score`.
- [ ] Bảng `trader_universe` + `filter_reasons`.
- [ ] Lưu lịch sử đổi tier.
- [ ] API `/universe/summary`.
- [ ] API `/universe/traders`.
- [ ] API `/universe/recompute`.

### Tầng 2 — Performance

- [ ] Gọi performance 4 windows cho toàn bộ Watch (~517).
- [ ] Lọc `totalOrder` theo tier.
- [ ] Lưu `performance_metrics`.

### Tầng 3 — Detail + positions + transfers

- [ ] Gọi detail cho Qualified (~113) + top Watch (tối đa ~200) = ~113–313.
- [ ] Kiểm tra `status=ACTIVE`, `isPaused=false`.
- [ ] Kiểm tra `currentCopyCount < maxCopyCount`.
- [ ] Gọi position-history.
- [ ] Gọi transfer-history.
- [ ] Không gọi trade-history full ở tầng này.

### Tầng 4 — Full trade history

- [ ] Gọi full trade-history cho High (~13).
- [ ] Gọi full trade-history cho top 30–50 Qualified.
- [ ] Không gọi cho Watch/Excluded.

### Storage & vận hành

- [ ] JSONL archive append-only.
- [ ] Parser detail → DB.
- [ ] Parser performance → DB.
- [ ] Parser position → DB + hash.
- [ ] Parser trade → DB + hash.
- [ ] Parser transfer → DB + hash.
- [ ] `collection_logs` theo từng tầng.
- [ ] `data_quality_flags`.
- [ ] Scheduler 60 phút cho list scan.
- [ ] Deep fetch scheduler riêng (2–24h).
- [ ] Advisory lock.
- [ ] API `/collector/status`.
- [ ] API `/collector/run-scan` (admin).
- [ ] API `/collector/run-deep` (admin).
- [ ] UI Data Health theo tier.
- [ ] Test resume.
- [ ] Test duplicate.
- [ ] Test rate limit.
- [ ] Test excluded không bị deep fetch.

**Gate:** scan 11.130 ≥ 99%, shortlist 400–700, không deep fetch excluded, resume được.

---

## Phase 3 — Quant + Scoring + Screener

### Quant

- [ ] ROI wrapper.
- [ ] PnL wrapper.
- [ ] MDD wrapper (published only).
- [ ] Sharpe wrapper (null handling).
- [ ] WinRate order.
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

### Funnel

- [ ] `potential_tier` (excluded/watch/qualified/high).
- [ ] `pre_score`.
- [ ] `filter_reasons`.
- [ ] Tier history.
- [ ] Audit false negative.

### Risk

- [ ] R01–R11.
- [ ] Evidence JSON.
- [ ] Risk level mapping.

### Scoring

- [ ] `scoring_config_versions`.
- [ ] Normalize percentile.
- [ ] Winsorize.
- [ ] Missing renormalize.
- [ ] Weight config.
- [ ] Hard filters.
- [ ] Score breakdown.
- [ ] `trader_scores`.
- [ ] `ranking_snapshots`.

### Screener

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

### QA

- [ ] Golden dataset 12 archetype (gồm 2 excluded).
- [ ] Test trader mẫu → Excluded.
- [ ] Test missing data.
- [ ] Test hard filter theo tier.
- [ ] Test pre-filter false negative.
- [ ] Test p95.

**Gate:** Screener shortlist ~700 dùng được, trader mẫu excluded không top.

---

## Phase 4 — Detail + Compare + Risk Monitor

- [ ] API `/traders/{id}/performance`.
- [ ] API `/traders/{id}/positions`.
- [ ] API `/traders/{id}/trades`.
- [ ] API `/traders/{id}/transfers`.
- [ ] API `/traders/{id}/risk`.
- [ ] API `/traders/{id}/score`.
- [ ] Trader Detail header.
- [ ] 10 metric cards.
- [ ] ROI vs benchmark chart.
- [ ] Drawdown chart (có disclaimer).
- [ ] Position PnL distribution.
- [ ] Score breakdown.
- [ ] Risk flags + evidence.
- [ ] What’s missing.
- [ ] Positions table.
- [ ] Trades summary.
- [ ] Transfers timeline.
- [ ] Compare page.
- [ ] Correlation matrix.
- [ ] Risk Monitor page.
- [ ] Tooltip definitions.
- [ ] Empty/loading/error.
- [ ] Responsive.

**Gate:** mỗi chỉ số có tooltip + nguồn; compare 4 trader không vỡ.

---

## Phase 5 — AI + Settings + Hardening

### AI

- [ ] AI adapter.
- [ ] Prompt template.
- [ ] JSON schema.
- [ ] Evidence IDs.
- [ ] Cost tracking.
- [ ] Budget ngày/tháng.
- [ ] Cooldown 24h.
- [ ] Dedupe input hash.
- [ ] Fallback template.
- [ ] AI Reports UI.
- [ ] Nút Analyze trên Detail.

### Settings

- [ ] Data Collection tab.
- [ ] Data Health tab.
- [ ] Scoring tab + preview impact.
- [ ] Risk Rules tab.
- [ ] AI tab.
- [ ] Ranking tab.
- [ ] Version + audit + rollback.

### Hardening

- [ ] Mã hóa API key.
- [ ] Rate limit login/API.
- [ ] Backup script.
- [ ] Restore test.
- [ ] Prometheus metrics.
- [ ] Alert rules.

**Gate:** AI không sửa score; settings version hóa; backup restore OK.

---

## Phase 6 — Testing + Deploy + Beta

- [ ] Chạy full test suite.
- [ ] Load test shortlist ~700.
- [ ] Test restart giữa crawl.
- [ ] Test backup/restore.
- [ ] Deploy VPS.
- [ ] Nginx + TLS.
- [ ] Log dashboard.
- [ ] Alert collector/stale/disk/AI.
- [ ] Viết runbook.
- [ ] Viết deployment doc.
- [ ] Beta 3–5 user.
- [ ] Thu feedback.
- [ ] Chốt backlog v1.1.
- [ ] Cập nhật `SESSION.md`.

**Gate:** uptime 7 ngày, collector đủ 7 ngày, beta feedback.

---

## Backlog v1.1

- [ ] AI compare 2 report.
- [ ] Watchlist.
- [ ] Alert trong web.
- [ ] Correlation/portfolio allocator nâng cao.
- [ ] Export PDF.
- [ ] Benchmark ETH/SOL.
- [ ] Ranking history chart.
- [ ] DCA/martingale detection nâng cao.
- [ ] Paper Copy (chỉ khi dữ liệu đủ tốt).

---

## Việc không làm (ghi rõ để tránh scope creep)

- [ ] Không auto trading.
- [ ] Không realtime WebSocket.
- [ ] Không Telegram.
- [ ] Không mobile app.
- [ ] Không microservices.
- [ ] Không Redis/Kafka/Celery.
- [ ] Không per-copier analytics.
- [ ] Không open positions giả.
- [ ] Không Paper Copy trong MVP.
- [ ] Không 6 bảng ranking.
