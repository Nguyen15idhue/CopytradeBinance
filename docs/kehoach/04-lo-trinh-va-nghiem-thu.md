# 04 — LỘ TRÌNH & NGHIỆM THU

> Nguyên tắc: **không chuyển phase nếu acceptance criteria chưa đạt**.  
> Mỗi phase phải có: file thay đổi, test, cập nhật `SESSION.md`, review.

---

## 1. Tổng quan

| Phase | Tên | Thời lượng | Đầu ra chính | Gate |
|---|---|---|---:|---|
| 0 | Data spike & pre-filter spec | 3–5 ngày | Data contract + tiêu chí phễu + go/no-go | Bắt buộc |
| 1 | Foundation + vertical slice | 5–7 ngày | 1 trader excluded + 1 trader qualified chạy end-to-end | Bắt buộc |
| 2 | Collector 2 tầng + raw storage | 4–6 ngày | List scan 11k + shortlist 517 | Bắt buộc |
| 3 | Quant + Scoring + Screener | 7–9 ngày | Screener dùng được, có tier | Bắt buộc |
| 4 | Detail + Compare + Risk | 5–7 ngày | Trang chi tiết, so sánh, risk monitor | Bắt buộc |
| 5 | AI + Settings + Hardening | 5–7 ngày | AI report, cấu hình web | Bắt buộc |
| 6 | Testing + Deploy + Beta | 4–6 ngày | MVP chạy VPS | Bắt buộc |
| | **Tổng** | **33–47 ngày** | | |

**Buffer:** cộng 20% → **40–56 ngày làm việc**.  
**Thực tế 1 dev full-time:** 7–9 tuần.  
**Part-time:** nhân 2.

---

## 2. Phase 0 — Data spike & pre-filter spec (3–5 ngày)

### Mục tiêu

Chứng minh dữ liệu lấy được, và **chốt phễu lọc tiềm năng** trước khi viết collector. Đây là phase **go/no-go**, không phải phase code.

### Công việc

- [ ] Gọi lại 6 endpoint, lưu raw JSON cho **20 trader mỗi tier**, không phải 20 trader ngẫu nhiên:
  - 20 trader **C — Watch** (vượt pre-filter).
  - 20 trader **B — Qualified**.
  - 20 trader **A — High**.
  - 10 trader **Excluded** (để kiểm tra false negative).
- [ ] Xác nhận `performance` dùng `BASE_P`.
- [ ] Xác nhận page size 30/200.
- [ ] Xác nhận universe PUBLIC + SIGNAL = 11.130; `PRIVATE` không quét.
- [ ] Xác nhận trader mẫu `5296057151807357697` là SIGNAL và **bị loại** vì runtime < 30.
- [ ] Chốt tiêu chí pre-filter và preset AUM (1k/5k/10k/20k).
- [ ] Chốt `traded_last_7d` từ `chartItems`; so sánh với `lastTradeTime` thật trên 20 mẫu.
- [ ] Chốt `pre_score` và thứ tự deep fetch.
- [ ] Đo tỷ lệ false negative: lấy 50 trader bị loại, gọi performance/detail, xem bao nhiêu thực sự có `totalOrder ≥ 20` và ROI > 0.
- [ ] Đo rate limit: bao nhiêu request/phút trước khi `11012005`.
- [ ] Đo thời gian: scan 11k list, fetch performance 517, detail 113–313, full trades 13.
- [ ] Viết `02-data-contract-binance.md` bản cuối.
- [ ] Tạo/cập nhật `data-availability-matrix.csv`.
- [ ] Quyết định: tiếp tục BAPI, hay chuyển CSV/Demo.

### Go/No-Go

| Kết quả | Hành động |
|---|---|
| 6 endpoint ổn định, pre-filter false negative < 5% | Go — tiếp tục Phase 1 |
| Có dữ liệu nhưng rate limit/không ổn định | Go có điều kiện — cache dài, giảm tần suất, kill-switch |
| Pre-filter false negative > 10% | Chỉnh ngưỡng trước khi làm collector |
| Không lấy được list/detail | No-Go — chuyển CSV import / demo data / pivot |

### Acceptance criteria

- [ ] Có **70 file raw JSON** (20 C + 20 B + 20 A + 10 excluded).
- [ ] Có bảng field ↔ metric mapping cho ít nhất 30 chỉ số.
- [ ] Có tài liệu tiêu chí phễu C/B/A/Excluded.
- [ ] Có số đo false negative của pre-filter.
- [ ] Có ước lượng thời gian scan 11k + deep fetch shortlist.
- [ ] Có quyết định go/no-go bằng văn bản.
- [ ] Không có endpoint nào được dùng mà chưa kiểm chứng.

---

## 3. Phase 1 — Foundation + vertical slice (5–7 ngày)

### Mục tiêu

Một trader chạy end-to-end: collect → raw → quant → API → UI.

### Công việc

- [ ] Khởi tạo repo, `docker-compose.yml`, `.env.example`.
- [ ] PostgreSQL + Alembic migration đầu tiên.
- [ ] FastAPI skeleton, `/health`, `/api/v1`.
- [ ] React + Vite + Tailwind + layout.
- [ ] Auth cơ bản: login, JWT, role admin/viewer.
- [ ] Model `traders`, `portfolio_snapshots`, `performance_metrics`.
- [ ] Collector adapter interface + `DemoAdapter`.
- [ ] Script seed **2 trader**: 1 excluded (`5296057151807357697`) + 1 qualified từ shortlist.
- [ ] API `/traders/{id}` trả dữ liệu.
- [ ] Trang Trader Detail tối giản hiển thị 10 chỉ số + tier.
- [ ] `SESSION.md` ghi lại quyết định.

### Acceptance criteria

- [ ] `docker compose up` chạy được.
- [ ] Đăng nhập được.
- [ ] Mở trader qualified thấy dữ liệu thật.
- [ ] Mở trader excluded thấy badge “Excluded” + lý do.
- [ ] Không có secret trong repo.
- [ ] Có ít nhất 3 unit test + 1 integration test.
- [ ] API trả `null` đúng cho field thiếu, không trả 0.

---

## 4. Phase 2 — Collector 2 tầng + raw storage (4–6 ngày)

### Mục tiêu

Quét universe 11.130 trader, tạo shortlist ~517, chỉ deep-fetch trader có tiềm năng. Không crawl lịch sử của trader bị loại.

### Công việc

- [ ] `BinanceBapiAdapter` đầy đủ 6 endpoint.
- [ ] Scan list **90D** với `portfolioType=PUBLIC` + `SIGNAL`.
- [ ] Dedupe theo `leadPortfolioId`.
- [ ] Pre-filter + gán tier + tính `pre_score`.
- [ ] Bảng `trader_universe` + `filter_reasons`.
- [ ] Gọi performance 4 windows cho toàn bộ Watch (~517).
- [ ] Gọi detail/positions/transfers cho Qualified (~113) + top Watch (tối đa ~200) = ~113–313.
- [ ] Gọi full trade-history cho High (~13) + top 30–50 Qualified.
- [ ] Lưu raw JSONB + JSONL archive.
- [ ] Parse detail/performance/position/trade/transfer.
- [ ] Hash trade/transfer chống trùng.
- [ ] `collection_logs` + `data_quality_flags`.
- [ ] Scheduler 60 phút cho list scan; deep fetch theo tần suất riêng.
- [ ] Retry/backoff 11012005.
- [ ] Nút “Run scan” và “Run deep fetch” riêng trên Settings.
- [ ] Trang Data Health: lần chạy cuối, số trader theo tier, số deep fetch, lỗi, stale.

### Acceptance criteria

- [ ] Scan đủ ≥ 99% của 11.130 trader trong 1 run.
- [ ] Shortlist Watch nằm trong khoảng **400–700**.
- [ ] Không có trader `excluded` nào bị deep fetch.
- [ ] `trader_universe` có đủ tier + `filter_reasons`.
- [ ] Chạy lại không tạo duplicate.
- [ ] Restart giữa chừng vẫn resume được.
- [ ] Có log cho từng run và từng tầng.
- [ ] Data freshness hiển thị đúng.
- [ ] Không có request nào vượt page size.
- [ ] Có test rate limit/backoff.
- [ ] 1 chu kỳ list scan + deep fetch shortlist < 15 phút.

---

## 5. Phase 3 — Quant + Scoring + Screener (7–9 ngày)

### Mục tiêu

Tính đủ chỉ số MVP, scoring v1.0, và màn hình Screener dùng được.

### Công việc

- [ ] Quant: ROI/PnL/MDD/Sharpe/WinRate/CopierPnl/AUM/CopyAum.
- [ ] Derived: leverage, holding time, position win rate, profit factor, payoff, symbol concentration, fee drag.
- [ ] Data Confidence formula.
- [ ] Potential tier + `pre_score` + `filter_reasons`.
- [ ] Risk events v1 (R01–R11).
- [ ] Scoring v1.0 + `scoring_config_versions`.
- [ ] Hard filters theo tier.
- [ ] Ranking 3 bảng + `ranking_snapshots`.
- [ ] API `/traders` filter/sort/pagination + filter `potential_tier`.
- [ ] API `/universe/summary` + `/universe/traders`.
- [ ] Screener UI: bảng, filter, saved views, count preview, tier column.
- [ ] Score breakdown UI.
- [ ] Export CSV.

### Acceptance criteria

- [ ] Trader mẫu bị đánh “Excluded”, không lọt top và không deep fetch.
- [ ] Filter MDD ≤ 15 trả về đúng.
- [ ] Filter tier `qualified` chỉ trả trader đủ điều kiện.
- [ ] Không có trader nào top chỉ vì ROI.
- [ ] Score breakdown khớp tổng điểm.
- [ ] Missing data không bị chấm 0.
- [ ] Screener shortlist (~700) tải p95 < 1s.
- [ ] Có audit sample 50 trader excluded để kiểm tra false negative.
- [ ] Có golden dataset test.

---

## 6. Phase 4 — Detail + Compare + Risk Monitor (5–7 ngày)

### Mục tiêu

Trang chi tiết đủ sâu, so sánh 2–4 trader, risk monitor.

### Công việc

- [ ] Trader Detail: header, score, confidence, 10 chỉ số, equity/drawdown, positions, trades summary, risk flags.
- [ ] “What’s missing” panel.
- [ ] Compare 2–4 trader: bảng + chart + correlation.
- [ ] Risk Monitor: list event, filter severity/status, evidence.
- [ ] Benchmark BTC/ETH trên chart ROI.
- [ ] Tooltip giải thích từng chỉ số.
- [ ] Empty/loading/error states.
- [ ] Responsive.

### Acceptance criteria

- [ ] Mỗi chỉ số có tooltip định nghĩa + nguồn.
- [ ] So sánh 4 trader không vỡ layout.
- [ ] Risk event mở được evidence.
- [ ] Không hiển thị open positions như thể có dữ liệu.
- [ ] Correlation có disclaimer “estimated”.

---

## 7. Phase 5 — AI + Settings + Hardening (5–7 ngày)

### Mục tiêu

AI report có kiểm soát, toàn bộ cấu hình chỉnh trên web, bảo mật cơ bản.

### Công việc

- [ ] AI adapter + prompt template + JSON schema.
- [ ] AI chỉ nhận dữ liệu đã chuẩn hóa, không nhận raw trade.
- [ ] Bắt buộc evidence IDs cho mọi nhận định.
- [ ] Cost tracking + budget ngày/tháng.
- [ ] Cooldown/dedupe report.
- [ ] AI Reports UI.
- [ ] Settings: Data Collection, Scoring, Risk, AI, Ranking.
- [ ] Version + audit log + rollback.
- [ ] Mã hóa API key.
- [ ] Rate limit login/API.
- [ ] Backup script + restore test.

### Acceptance criteria

- [ ] AI không sửa score.
- [ ] AI trả JSON hợp lệ hoặc fallback template.
- [ ] Không có report nào không có evidence.
- [ ] Đổi trọng số tạo version mới, score cũ giữ nguyên.
- [ ] API key không trả về browser.
- [ ] Rollback hoạt động.

---

## 8. Phase 6 — Testing + Deploy + Beta (4–6 ngày)

### Mục tiêu

MVP chạy VPS, có monitoring, có beta user.

### Công việc

- [ ] Chạy full test suite.
- [ ] Test tải shortlist ~700 trader.
- [ ] Test backup/restore.
- [ ] Test restart giữa crawl.
- [ ] Deploy VPS + Nginx + TLS.
- [ ] Prometheus/Grafana hoặc log dashboard.
- [ ] Alert: collector fail, stale, disk, AI budget.
- [ ] Viết README vận hành.
- [ ] Beta 3–5 người dùng.
- [ ] Thu feedback, chốt backlog v1.1.

### Acceptance criteria

- [ ] Uptime 7 ngày không crash.
- [ ] Collector chạy đủ 7 ngày.
- [ ] Backup restore thành công.
- [ ] Không có lỗi bảo mật nghiêm trọng.
- [ ] Có ít nhất 3 người dùng thử và phản hồi.
- [ ] `SESSION.md` cập nhật đầy đủ.

---

## 9. Definition of Done cho mỗi phase

Một phase chỉ được coi là xong khi:

- [ ] Code chạy được, không lỗi nghiêm trọng.
- [ ] Unit test cho logic mới.
- [ ] Integration test cho luồng chính.
- [ ] Không có TODO nghiêm trọng trong code.
- [ ] API/schema được cập nhật trong docs.
- [ ] `SESSION.md` ghi quyết định + việc còn lại.
- [ ] Không có secret/API key trong repo.
- [ ] Acceptance criteria của phase đạt.
- [ ] Có ít nhất 1 người review (hoặc self-review checklist).

---

## 10. Backlog v1.1 (sau MVP)

- AI report nâng cao: so sánh 2 báo cáo, phản biện.
- Watchlist + alert trong web.
- Correlation/portfolio allocator nâng cao.
- Export PDF.
- Benchmark theo ETH/SOL.
- Lịch sử ranking theo thời gian.
- Cải thiện DCA/martingale detection.
- Paper Copy (chỉ khi có dữ liệu đủ tốt, và ghi rõ “estimated”).

---

## 11. Rủi ro timeline

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|---|---|---|
| BAPI đổi/block | Trễ 1–2 tuần | Adapter + CSV/Demo fallback |
| Rate limit nặng | Crawl chậm | Giảm concurrency, cache, crawl theo shortlist |
| Dữ liệu bẩn | Scoring sai | Golden dataset + test |
| Pre-filter loại nhầm trader tốt | Sót ứng viên | Audit 50 excluded + preset + ngưỡng configurable |
| Pre-filter quá lỏng | Deep fetch nhiều | Giới hạn max deep fetch/ngày |
| Scope creep | Trễ | Quyết định khóa + cắt Paper Copy |
| AI cost vượt | Tốn tiền | Budget + cooldown + manual default |
| Một dev ốm/bận | Trễ | Buffer 20% + task nhỏ |

---

## 12. Lịch tuần gợi ý (full-time)

| Tuần | Việc |
|---|---|
| 1 | Phase 0 + Phase 1 |
| 2 | Phase 2 |
| 3 | Phase 3 |
| 4 | Phase 3 + Phase 4 |
| 5 | Phase 4 + Phase 5 |
| 6 | Phase 5 + Phase 6 |
| 7 | Beta + sửa lỗi |
| 8 | Buffer / v1.1 |

Nếu part-time: mỗi tuần tương ứng 2 tuần thực tế.
