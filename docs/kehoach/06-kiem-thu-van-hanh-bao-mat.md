# 06 — KIỂM THỬ, VẬN HÀNH & BẢO MẬT

> Mục tiêu: không chỉ “web chạy”, mà **dữ liệu đúng, chỉ số đúng, và hệ thống chịu được lỗi**.

---

## 1. Test pyramid

| Tầng | Số lượng | Mục tiêu | Công cụ |
|---|---:|---|---|
| Unit | 60–80 | Công thức, normalize, scoring, parser | pytest |
| Contract | 15–25 | Schema endpoint, field, null, cap | pytest + respx |
| Integration | 15–20 | Collector → DB → API | pytest + test DB |
| E2E | 5–10 | Luồng người dùng | Playwright (optional) |
| Data quality | 10–15 | Null, duplicate, stale, anomaly | pytest + SQL |
| Performance | 5 | Shortlist ~700, dashboard | locust/k6 |
| Security | 5–10 | Auth, RBAC, secrets | manual + OWASP checklist |
| Recovery | 5 | Restart, backup, resume | manual script |

---

## 2. Golden dataset

Tạo bộ fixture cố định, không phụ thuộc mạng.

### 2.1. 12 trader archetype

| # | Archetype | Đặc điểm | Kỳ vọng |
|---|---|---|---|
| 1 | Good low risk | ROI 30%, MDD 8%, Sharpe 1.8, 200 orders | Score cao |
| 2 | High return, high risk | ROI 200%, MDD 60%, lev 20x | Không top |
| 3 | High win rate, big loss | WR 90%, profit factor 0.5 | Không top |
| 4 | Martingale suspected | Size tăng sau lỗ | Risk flag |
| 5 | DCA suspected | Nhiều fill cùng hướng | Risk flag |
| 6 | Profit concentrated | 1 position chiếm 80% PnL | Risk flag |
| 7 | Missing data | Sharpe null, MDD null | Confidence thấp |
| 8 | Stale data | last collection 24h | Không top |
| 9 | ROI anomaly | ROI 7000%, MDD 1% | Flag kiểm tra |
| 10 | Stable | 12 tháng, positive months 75% | Consistency cao |
| 11 | Excluded — new | Runtime 4 ngày, ROI 59% | **Không deep fetch** |
| 12 | Excluded — no slots / no trade | Full slot, không trade 7D | **Không deep fetch** |

### 2.2. Trader thật làm regression fixture

`5296057151807357697` — SIGNAL, 4 ngày, ROI 59,23%, MDD 31,34%, Sharpe null, 5.292 fills, 8 positions.

Kỳ vọng:

- `runtime_days` ~4.
- `roi_90d = 59.23`.
- `mdd_90d = 31.34`.
- `sharpe = null`.
- `win_rate_order = 50`.
- `position_win_rate = 62.5`.
- `profit_factor ~ 1.64`.
- `max_leverage = 15`.
- `worst_position_roi = -97.8`.
- `potential_tier = excluded`.
- `confidence < 0.4`.
- `score = null` hoặc bị loại khỏi ranking (tùy implementation; không được lọt top).
- Collector **không gọi** detail/position/trade cho trader này trong run bình thường.
- `risk_flags` chứa R03, R04, R06, R07, R08, R10, R11.

> Đây là test quan trọng nhất: hệ thống phải **không** xếp trader này vào top dù ROI 59%.

---

## 3. Unit test — công thức

### 3.1. MDD

```python
def test_mdd_basic():
    equity = [100, 120, 90, 110, 80]
    assert mdd(equity) == pytest.approx(33.333, rel=1e-3)
```

- MDD = (120 − 80) / 120 = 33.33%.

### 3.2. Không tính MDD từ chartItems

Test bắt buộc:

```python
def test_mdd_from_chart_items_not_used():
    chart = [54.66, 6.19, 59.23]
    with pytest.raises(ValueError):
        compute_mdd_from_roi_chart(chart)
```

Hoặc nếu vẫn cho phép, phải trả `estimated=True` và cảnh báo.

### 3.3. Sharpe

- < 30 observations → `None`.
- std = 0 → `None`.
- annualization đúng.

### 3.4. Profit factor

- Không có lỗ → `None`, không `inf`.
- < 5 positions → `low_sample=True`.

### 3.5. WinRate

- `total_orders = 0` → `None`, không 0.
- `win_orders > total_orders` → lỗi dữ liệu.

### 3.6. Normalize & score

- Missing component → renormalize.
- Tất cả missing → `None`.
- Direction đảo đúng.
- Percentile rank đúng cohort.

### 3.7. Confidence

- Runtime 4 ngày → history ~0.044.
- Sharpe null → coverage giảm.
- Freshness 24h → 0.

### 3.8. Pre-filter & tier

```python
def test_excluded_new_trader():
    assert tier_of(runtime_days=4, roi=59, pnl=583_000, ...) == "excluded"

def test_excluded_no_trade_7d():
    assert tier_of(traded_last_7d=False, ...) == "excluded"

def test_excluded_negative_roi():
    assert tier_of(roi=-5, ...) == "excluded"

def test_excluded_full_slots():
    assert tier_of(current_copy=200, max_copy=200, ...) == "excluded"

def test_excluded_low_aum():
    assert tier_of(aum=1_000, min_aum=5_000, ...) == "excluded"

def test_watch_valid():
    assert tier_of(runtime=45, roi=12, pnl=1000, wr=50, mdd=25, aum=8000, ...) == "watch"

def test_qualified_thresholds():
    assert tier_of(runtime=100, roi=12, wr=50, mdd=25, aum=15000, sharpe=0.8, orders=60) == "qualified"

def test_high_thresholds():
    assert tier_of(runtime=200, roi=25, wr=55, mdd=15, aum=25000, sharpe=1.2, orders=120) == "high"

def test_pre_score_missing_sharpe_neutral():
    assert pre_score(sharpe=None, ...) uses 50, not 0
```

**Test bắt buộc:** trader `5296057151807357697` phải trả `excluded`, và collector **không được gọi** detail/position/trade cho trader này trong run bình thường.

---

## 4. Contract test — endpoint

### 4.1. List

- `pageSize=30` → trả ≤ 30.
- `pageSize=100` → trả 30.
- `portfolioType=ALL` → có PUBLIC/SIGNAL/PRIVATE.
- `total` > 0.
- Mỗi item có 22 field.
- `chartItems` length = 90 cho 90D.

### 4.2. Detail

- `portfolioId` string, không number.
- Trả 67 field.
- `status` thuộc enum.
- Field null không bị parse thành 0.

### 4.3. Performance

- Dùng `BASE_P`, không phải `BASE_F`.
- 4 timeRange trả đúng.
- `winOrders <= totalOrder`.
- `sharpRatio` có thể null.

### 4.4. Position history

- `positionId` unique.
- `opened < closed`.
- `roi` có thể âm.
- `leverage > 0`.

### 4.5. Trade history

- `pageSize=200` → trả ≤ 200.
- `pageSize=500` → trả 200.
- Tổng fetch đủ `total`.
- `fee` có thể âm.
- Không có `trade_id` → hash ổn định.

### 4.6. Transfer history

- `transType` thuộc enum.
- `amount > 0`.
- Hash ổn định.

---

## 5. Integration test — luồng chính

### 5.1. Collector → DB

- Chạy 1 page list → insert đúng.
- Chạy pre-filter → `trader_universe` có tier + reasons.
- Chạy deep fetch → chỉ trader Watch/Qualified/High.
- Chạy lại → không duplicate.
- Chạy lại giữa chừng → resume.
- Raw JSON lưu nguyên vẹn.

### 5.2. Quant

- Từ raw mẫu → metrics đúng.
- Position/trade aggregate đúng.
- Không ghi đè snapshot cũ.

### 5.3. Scoring

- Config version 1 → score.
- Đổi config → version 2, score cũ giữ nguyên.
- Hard filter loại đúng.

### 5.4. API

- `/traders` filter/sort/pagination.
- `/traders/{id}` trả 404 nếu không có.
- `/compare` max 4.
- `/settings` chỉ admin.

### 5.5. Frontend

- Screener load shortlist ~700 → p95 < 1s.
- Filter → count đúng.
- Compare 4 trader → không vỡ.
- Empty state.
- Error state.

---

## 6. Data quality test

| Test | Kỳ vọng |
|---|---|
| Duplicate snapshot | Unique constraint chặn |
| Duplicate position | Unique `(portfolio_id, position_id)` |
| Duplicate trade | Hash unique |
| Null Sharpe | Không chấm 0 |
| Zero copyAum | Không coi là missing |
| Stale > 150 phút | Flag |
| Total list thay đổi | Dedupe, không crash |
| ChartItems flow | Không dùng tính MDD |
| ROI 7000% | Flag anomaly, không auto reject |
| WinRate 100% + 5 orders | Low sample |
| Pre-filter counts | Watch ~517, Qualified ~113, High ~13 (snapshot 06/11) |
| Excluded không bị deep fetch | Không có request detail/position/trade |
| False negative | Sample 50 excluded, < 5% thực sự đủ điều kiện |
| Tier thay đổi | Trader chuyển tier khi đủ ngày/order |
| Pre-score missing Sharpe | Dùng 50 neutral, không 0 |

### Query kiểm tra định kỳ

```sql
-- duplicate snapshot
SELECT lead_portfolio_id, collected_hour, count(*)
FROM portfolio_snapshots
GROUP BY 1,2 HAVING count(*) > 1;

-- trader thiếu performance
SELECT t.lead_portfolio_id
FROM traders t
LEFT JOIN performance_metrics p
  ON p.lead_portfolio_id = t.lead_portfolio_id
 AND p.time_range = '90D'
WHERE p.id IS NULL;

-- stale
SELECT count(*) FROM traders
WHERE last_collected_at < now() - interval '150 minutes';
```

---

## 7. Performance test

| Kịch bản | Mục tiêu |
|---|---|
| `GET /traders?page=1&page_size=50` | p95 < 500ms |
| `GET /traders` với shortlist ~700 + filter | p95 < 1s |
| `GET /traders/{id}` | p95 < 300ms |
| Dashboard overview | p95 < 1s |
| Screener render 100 rows | < 1s |
| Scan 11.130 list (90D) | < 5 phút |
| Deep fetch 517 performance | < 5 phút |
| Deep fetch 113–313 detail/positions | < 10 phút |
| Full trade history 13 trader | < 5 phút |
| 1 chu kỳ đầy đủ | < 15 phút |

### Index bắt buộc

```sql
CREATE INDEX idx_traders_type_status ON traders(portfolio_type, status);
CREATE INDEX idx_perf_lookup ON performance_metrics(lead_portfolio_id, time_range, collected_at DESC);
CREATE INDEX idx_snap_hour ON portfolio_snapshots(collected_hour DESC);
CREATE INDEX idx_scores_lookup ON trader_scores(config_version, score DESC);
CREATE INDEX idx_positions_trader ON position_history(lead_portfolio_id, closed_at DESC);
CREATE INDEX idx_trades_trader ON trade_history(lead_portfolio_id, traded_at DESC);
```

Partition `portfolio_snapshots` theo tháng.

---

## 8. Security checklist

- [ ] Password hash Argon2id/bcrypt ≥ 12.
- [ ] JWT access 15 phút, refresh 7 ngày, rotate.
- [ ] RBAC admin/viewer.
- [ ] API key AI mã hóa at rest.
- [ ] Không trả API key về browser.
- [ ] CORS chỉ domain frontend.
- [ ] Rate limit login 5/phút/IP.
- [ ] Rate limit API 100/phút/user.
- [ ] Audit log settings/scoring/risk.
- [ ] Không log token/password/API key.
- [ ] SQL parameterized.
- [ ] Không `dangerouslySetInnerHTML`.
- [ ] Dependency scan (`pip-audit`, `npm audit`).
- [ ] HTTPS + HSTS.
- [ ] Backup mã hóa.
- [ ] Không mở PostgreSQL ra internet.
- [ ] Không dùng API key Binance có quyền giao dịch.

---

## 9. Recovery & vận hành

### 9.1. Restart giữa crawl

- JSONL append-only.
- DB transaction theo batch.
- Chạy lại: đọc JSONL, bỏ qua trader đã có.
- Không mất snapshot đã ghi.

### 9.2. Backup

```bash
pg_dump -Fc copytrade > backup_$(date +%F).dump
```

- Daily 02:00 UTC.
- Giữ 7 daily + 4 weekly.
- Test restore hàng tháng.
- JSONL sync daily.

### 9.3. Monitoring

| Metric | Alert |
|---|---|
| Collector success | Fail 2 lần liên tiếp |
| Data freshness | > 150 phút |
| API 5xx | > 1% trong 5 phút |
| API p95 | > 2s |
| Disk | > 80% |
| AI cost | > 80% budget |
| DB connections | > 80% pool |

### 9.4. Runbook sự cố

| Sự cố | Hành động |
|---|---|
| BAPI 403/404 | Kiểm tra path/header; tạm dừng collector; bật CSV fallback |
| Rate limit 11012005 | Giảm concurrency, tăng backoff, chờ |
| List total giảm mạnh | Kiểm tra thay đổi API; không xóa dữ liệu cũ |
| DB đầy | Partition/archive snapshot cũ; tăng disk |
| AI lỗi | Tắt AI, hệ thống vẫn chạy |
| Score bất thường | So sánh config version; rollback |
| Data stale | Chạy collector thủ công; kiểm tra network |

---

## 10. Acceptance test cho toàn MVP

- [ ] Scan 11.130 trader PUBLIC + SIGNAL đủ ≥ 99%.
- [ ] Shortlist Watch nằm trong 400–700.
- [ ] Không có trader excluded nào bị deep fetch.
- [ ] Không duplicate sau 3 lần chạy.
- [ ] Restart giữa crawl không mất dữ liệu.
- [ ] Trader mẫu ra “Excluded”, không top, không deep fetch.
- [ ] MDD hiển thị = published, không phải 88,67%.
- [ ] Sharpe null hiển thị `N/A`, không 0.
- [ ] WinRate order và position hiển thị tách biệt.
- [ ] AUM và Copy AUM hiển thị tách biệt.
- [ ] Filter/sort/pagination đúng.
- [ ] Compare max 4.
- [ ] Settings tạo version, rollback được.
- [ ] AI không sửa score.
- [ ] Backup restore thành công.
- [ ] Không có secret trong repo.
- [ ] p95 API đạt mục tiêu.
- [ ] Có 3–5 beta user phản hồi.

---

## 11. Tài liệu vận hành cần viết

- `docs/runbook.md` — sự cố, restart, backup.
- `docs/api.md` — OpenAPI + ví dụ.
- `docs/deployment.md` — VPS, Nginx, TLS, cron.
- `docs/data-quality.md` — định nghĩa flag, query kiểm tra.
- `SESSION.md` — nhật ký quyết định.
