# 03 — BỘ CHỈ SỐ, SCORING & RISK RULES

> Mọi chỉ số phải có: **định nghĩa, nguồn, cửa sổ thời gian, độ tin cậy, cách xử lý khi thiếu dữ liệu**.  
> Đọc kèm: `02-data-contract-binance.md`

---

## 1. Phân tầng chỉ số

| Tầng | Tên | Nguồn | Cách dùng |
|---|---|---|---|
| **T0** | Metadata & Quality | detail/list | Hiển thị, filter, confidence |
| **T1** | Published | performance/detail | Hiển thị trực tiếp, scoring |
| **T2** | Derived | position/trade/transfer | Hiển thị kèm nhãn “tính toán” |
| **T3** | Unavailable | — | Hiển thị “N/A”, không ước lượng |

### Quy tắc hiển thị

- T1: không cần tooltip dài, nhưng phải ghi cửa sổ (30D/90D/180D).
- T2: có badge “Derived” + tooltip công thức.
- T3: hiển thị `N/A` + lý do, không hiển thị 0.
- T0: có badge confidence.

---

## 1.1. Phễu tiềm năng & pre-score

Trước khi chấm score, trader phải vượt qua phễu. Đây là **hard filter ở tầng dữ liệu**, không phải scoring.

### Tier

| Tier | Điều kiện | Mục đích |
|---|---|---|
| **Excluded** | Không trade 7D, runtime < 30, ROI ≤ 0, PnL ≤ 0, WR < 40, MDD > 40, AUM < 5k, full slot | Không deep fetch |
| **C — Watch** | Runtime ≥ 30, ROI > 0, PnL > 0, WR ≥ 40, MDD ≤ 40, AUM ≥ 5k, còn slot | Theo dõi |
| **B — Qualified** | Runtime ≥ 90, ROI ≥ 10, WR ≥ 45, MDD ≤ 30, AUM ≥ 10k, Sharpe ≥ 0.5/null, orders ≥ 50 | Đánh giá |
| **A — High** | Runtime ≥ 180, ROI ≥ 20, WR ≥ 50, MDD ≤ 20, AUM ≥ 20k, Sharpe ≥ 1, orders ≥ 100 | Ưu tiên |

### Pre-score (chỉ để xếp thứ tự deep fetch)

```
pre_score = 0.30 × norm(roi_90d)
          + 0.30 × norm(−mdd_90d)
          + 0.20 × norm(sharpe_90d, missing = 50)
          + 0.10 × norm(win_rate_90d)
          + 0.10 × norm(min(runtime_days / 180, 1))
```

Quy tắc:

- `norm()` = percentile rank trong cohort PUBLIC/SIGNAL.
- Sharpe null → 50 neutral, không phải 0.
- Pre-score **không phải score cuối**; không hiển thị như điểm chất lượng.
- Dùng để sort deep fetch: High → Medium → Low.

### Kết quả thực đo (06/11/2026)

| Tier | PUBLIC | SIGNAL | Tổng |
|---|---:|---:|---:|
| Universe | 8.976 | 2.154 | 11.130 |
| C — Watch | 460 | 57 | 517 |
| B — Qualified (upper bound) | 103 | 10 | 113 |
| A — High (upper bound) | 13 | 0 | 13 |

> Đây là upper bound trước `totalOrder` và `status`.  
> **B và A là subset của C**, không cộng dồn. Union deep-fetch = **517**.  
> Sau performance/detail, shortlist thực tế thường còn 300–450.

### Preset

| Preset | AUM min | Watch (PUBLIC) | Dùng khi |
|---|---:|---:|---|
| Broad | 1.000 | ~1.021 | Muốn nhiều ứng viên |
| **Balanced** | **5.000** | **460** | Mặc định |
| Strict | 10.000 | ~314 | Ít nhiễu |

---

## 2. Danh mục chỉ số MVP

### 2.1. T0 — Metadata & Quality

| Chỉ số | Định nghĩa | Nguồn |
|---|---|---|
| `potential_tier` | excluded / watch / qualified / high | phễu |
| `pre_score` | 0–100, chỉ để xếp thứ tự deep fetch | phễu |
| `filter_reasons` | Danh sách lý do bị loại | phễu |
| `runtime_days` | (now − startTime) / 86400 | detail.startTime |
| `portfolio_type` | PUBLIC / SIGNAL / PRIVATE | list |
| `status` | ACTIVE / CLOSED / PAUSED | detail |
| `last_trade_age_hours` | (now − lastTradeTime) / 3600 | detail |
| `data_freshness_minutes` | now − collected_at | collector |
| `data_confidence` | 0–1, xem mục 5 | tổng hợp |
| `total_orders` | Số order đóng | performance |
| `missing_fields` | Danh sách field null | detail/performance |

### 2.2. T1 — Published metrics

| Chỉ số | Định nghĩa | Cửa sổ | Nguồn |
|---|---|---|---|
| `roi` | ROI (%) | 7/30/90/180D | performance.roi |
| `pnl` | PnL (USDT) | 7/30/90/180D | performance.pnl |
| `mdd` | Max drawdown (%) | 7/30/90/180D | performance.mdd |
| `sharpe` | Sharpe ratio | 7/30/90/180D | performance.sharpRatio |
| `win_rate_order` | winOrders / totalOrder × 100 | 7/30/90/180D | performance |
| `win_orders` | Số order thắng | 7/30/90/180D | performance |
| `total_orders` | Tổng order đóng | 7/30/90/180D | performance |
| `copier_pnl` | PnL của copier | 7/30/90/180D | performance.copierPnl |
| `aum` | Tổng AUM | hiện tại | detail.aumAmount |
| `copy_aum` | Vốn copier | hiện tại | detail.copyAum |
| `margin_balance` | Vốn lead | hiện tại | detail.marginBalance |
| `current_copiers` | Copier hiện tại | hiện tại | detail.currentCopyCount |
| `max_copiers` | Slot tối đa | hiện tại | detail.maxCopyCount |
| `total_copiers` | Tổng từng copy | hiện tại | detail.totalCopyCount |
| `profit_sharing_rate` | % chia lợi nhuận | hiện tại | detail.profitSharingRate |
| `min_copy_fixed_ratio` | Min copy fixed ratio | hiện tại | detail.fixedRadioMinCopyUsd |
| `min_copy_fixed_amount` | Min copy fixed amount | hiện tại | detail.fixedAmountMinCopyUsd |
| `favorite_count` | Lượt favorite | hiện tại | detail.favoriteCount |
| `tags` | Leverage/TradFi/API | hiện tại | detail.tagItemVos |
| `badge` | Badge | hiện tại | detail.badgeName |
| `ai_summary` | AI summary của Binance | hiện tại | detail.aiSummary |

### 2.3. T2 — Derived metrics

| Chỉ số | Công thức | Nguồn | Độ tin cậy |
|---|---|---|---|
| `max_leverage` | max(position.leverage) | position | Cao |
| `avg_leverage` | mean(position.leverage) | position | Cao |
| `margin_mode` | mode(position.isolated) | position | Cao |
| `avg_holding_hours` | mean((closed−opened)/3600) | position | Cao |
| `median_holding_hours` | median(...) | position | Cao |
| `max_holding_hours` | max(...) | position | Cao |
| `position_win_rate` | wins / positions × 100 | position | Cao |
| `profit_factor` | gross_win / abs(gross_loss) | position | Cao |
| `payoff_ratio` | avg_win / abs(avg_loss) | position | Cao |
| `best_position_pnl` | max(closingPnl) | position | Cao |
| `worst_position_pnl` | min(closingPnl) | position | Cao |
| `worst_position_roi` | min(position.roi) × 100 | position | Cao |
| `near_liquidation_count` | count(position.roi ≤ −0.8) | position | Cao |
| `long_short_ratio` | count(Long) / count(Short) | position | Cao |
| `symbol_concentration` | max(symbol notional) / total notional | position/trade | Trung bình |
| `total_fills` | count(trades) | trade | Cao |
| `fills_per_day` | total_fills / active_days | trade | Cao |
| `avg_fill_notional` | mean(trade.quantity) | trade | Cao |
| `max_fill_notional` | max(trade.quantity) | trade | Cao |
| `total_fees` | sum(trade.fee) | trade | Cao |
| `fee_drag_pct` | total_fees / abs(gross_pnl) × 100 | trade | Trung bình |
| `realized_pnl_fills` | sum(trade.realizedProfit) | trade | Cao |
| `net_flow` | deposits − withdrawals | transfer | Cao |
| `copy_aum_ratio` | copy_aum / aum × 100 | detail | Cao |
| `copier_pnl_per_copier` | copier_pnl / max(current_copiers,1) | detail | Trung bình |
| `calmar` | roi_90d / mdd_90d | derived | Trung bình |
| `benchmark_return` | BTC return cùng window | klines | Cao |
| `excess_return` | roi − benchmark_return | derived | Cao |
| `positive_days_pct` | count(daily_return > 0) / days | chartItems | Thấp (flow) |
| `volatility_daily` | std(daily_return) | chartItems | Thấp (flow) |
| `dca_suspected` | ≥3 fill cùng symbol/side + size tăng | trade | Heuristic |
| `martingale_suspected` | size vị thế sau lỗ ≥1.5× vị thế trước, lặp ≥3 | position/trade | Heuristic |
| `open_position_inferred` | net(qty) theo symbol từ trade | trade | Rất thấp |

### 2.4. T3 — Unavailable

| Chỉ số | Lý do |
|---|---|
| Open positions | Không có endpoint |
| Per-copier PnL | Không có endpoint |
| Funding fee | Không có trong trade-history |
| Liquidation price | Cần open positions |
| Margin ratio hiện tại | Cần open positions |
| Copy fill rate | Cần tài khoản copier |
| Copy slippage | Cần tài khoản copier |
| Lock-up period thực tế | Thường null |

---

## 3. Công thức quan trọng

### 3.1. ROI

**Hiển thị:** dùng `performance.roi`.

Nếu tự tính:

```
TWR = Π(1 + r_t) − 1
r_t = (NAV_t − NAV_{t-1} − flow_t) / NAV_{t-1}
```

Không dùng `PnL / balance` đơn giản vì bỏ qua nạp/rút.

### 3.2. MDD

**Hiển thị:** dùng `performance.mdd`.

Nếu tự tính trên equity đã điều chỉnh:

```
peak_t = max(NAV_0..NAV_t)
dd_t   = (peak_t − NAV_t) / peak_t
MDD    = max(dd_t)
```

**Cấm:** tính MDD trực tiếp từ `chartItems` mà không điều chỉnh dòng tiền.

### 3.3. Sharpe

**Hiển thị:** `performance.sharpRatio` nếu khác null.

Nếu tự tính:

```
Sharpe = mean(r_daily − rf_daily) / std(r_daily) × sqrt(365)
```

- `rf` mặc định 0; ghi rõ trong tooltip.
- Tối thiểu **30 daily observations**.
- Nếu < 30 → `null`, không hiển thị số.
- Nếu std = 0 → `null`.

### 3.4. WinRate

```
win_rate_order = win_orders / total_orders × 100
position_win_rate = winning_positions / closed_positions × 100
```

- Hiển thị cả hai, ghi rõ nhãn.
- Nếu `total_orders < 20` → badge “low sample”.

### 3.5. Profit Factor

```
profit_factor = Σ(positive closingPnl) / abs(Σ(negative closingPnl))
```

- Nếu không có lỗ → `null` hoặc `∞`, không hiển thị ∞.
- Nếu < 5 vị thế → “insufficient sample”.

### 3.6. Calmar

```
calmar = roi_90d / mdd_90d
```

- Chỉ tính khi `mdd_90d > 0`.
- Nếu MDD > 100 → cắt hoặc null.

### 3.7. Fee Drag

```
fee_drag_pct = total_fees / abs(gross_pnl) × 100
```

- `total_fees` có thể âm (rebate) → fee drag âm = được hoàn phí.
- Nếu `gross_pnl = 0` → null.

### 3.8. Symbol Concentration

```
top_symbol_share = notional(symbol lớn nhất) / total_notional × 100
```

Hoặc HHI:

```
HHI = Σ(share_i²)
```

- HHI > 0.4 → tập trung cao.
- Hiển thị top 3 symbol.

### 3.9. DCA / Martingale (heuristic)

**DCA suspected** nếu:

- ≥ 3 fill cùng `symbol` + cùng `positionSide` trong 1 vị thế.
- Giá vào trung bình di chuyển ngược hướng.
- Size tăng dần.

**Martingale suspected** nếu:

- Sau một vị thế lỗ, notional vị thế tiếp theo ≥ 1.5×.
- Lặp lại ≥ 3 lần.
- Cùng symbol hoặc cùng nhóm.

**Nhãn:** `suspected_dca`, `suspected_martingale`. Không khẳng định tuyệt đối.

---

## 4. Data Confidence

### 4.1. Công thức

```
confidence = 0.40 × coverage
           + 0.30 × history
           + 0.20 × freshness
           + 0.10 × continuity
```

| Thành phần | Cách tính |
|---|---|
| `coverage` | Tỷ lệ field bắt buộc non-null / tổng field bắt buộc |
| `history` | min(runtime_days / 90, 1) |
| `freshness` | 1 nếu ≤ 60 phút; giảm tuyến tính đến 0 ở 24 giờ |
| `continuity` | Tỷ lệ snapshot có mặt trong 7 ngày gần nhất |

### 4.2. Nhãn

| Confidence | Nhãn | Hành vi |
|---|---|---|
| ≥ 0.80 | High | Được vào ranking |
| 0.60–0.79 | Medium | Vào ranking, hiển thị badge |
| 0.40–0.59 | Low | Không vào top, hiển thị cảnh báo |
| < 0.40 | Insufficient | Không chấm điểm, chỉ hiển thị hồ sơ |

### 4.3. Ví dụ trader mẫu

- Runtime 4 ngày → `history = 4/90 = 0.044`.
- Sharpe null → coverage giảm.
- Confidence ước tính < 0.4 → **không được xếp hạng**, dù ROI 59,23%.
- Đồng thời **bị Excluded ở Stage 0** vì runtime < 30 → không deep fetch.

---

## 5. Scoring v1.0

### 5.1. Trọng số đề xuất

| Nhóm | Trọng số | Thành phần |
|---|---:|---|
| **Risk Management** | 25 | MDD 10, Calmar 5, max leverage 5, worst position ROI 5 |
| **Consistency** | 20 | Positive months/days 8, recovery 6, ROI stability 6 |
| **Profitability** | 15 | ROI 90D 8, excess return vs BTC 4, PnL scale 3 |
| **Trading Quality** | 15 | Profit factor 6, payoff ratio 4, win rate 5 |
| **Copy Performance** | 10 | Copier PnL 4, copy AUM ratio 3, copiers 3 |
| **Capital Efficiency** | 5 | PnL/AUM 3, AUM trend 2 |
| **Data Reliability** | 10 | Confidence 6, sample size 4 |
| **Tổng** | **100** | |

### 5.2. Chuẩn hóa

1. Chia cohort: cùng `portfolio_type` + cùng `time_range`.
2. Winsorize 5–95 percentile.
3. Chuyển sang **percentile rank** trong cohort (0–100).
4. Đảo chiều với chỉ số “càng thấp càng tốt” (MDD, leverage, fee drag).
5. Missing → loại thành phần, **renormalize** trọng số còn lại.
6. Không bao giờ gán 0 cho missing.

```python
def normalize(value, cohort, direction="higher_is_better"):
    if value is None:
        return None
    p = percentile_rank(value, cohort)  # 0..100
    return p if direction == "higher_is_better" else 100 - p

def score(components, weights):
    total_w = sum(w for k, w in weights.items() if components.get(k) is not None)
    if total_w == 0:
        return None
    return sum(components[k] * w for k, w in weights.items() if components.get(k) is not None) / total_w
```

### 5.3. Hard filters (tách khỏi score)

| ID | Điều kiện | Hành vi |
|---|---|---|
| HF01 | `status != ACTIVE` | Loại |
| HF02 | `potential_tier = excluded` | Không xếp hạng |
| HF03 | `runtime_days < 30` | Không xếp hạng |
| HF04 | `total_orders < 20` (Watch) / `< 50` (Qualified) / `< 100` (High) | Không xếp hạng tier tương ứng |
| HF05 | `data_freshness > 150 phút` | Loại khỏi top |
| HF06 | `confidence < 0.5` | Không xếp hạng |
| HF07 | `isPaused = true` | Không xếp hạng |
| HF08 | `mdd_90d` null | Không xếp hạng Low Risk |
| HF09 | Low Risk: `runtime < 90` hoặc `mdd > 20` hoặc `max_leverage > 5` | Loại khỏi Low Risk |

### 5.4. Score bands

| Score | Nhãn | Ý nghĩa |
|---|---|---|
| 85–100 | Excellent | Rất tốt, vẫn cần kiểm tra risk flags |
| 70–84 | Good | Tốt |
| 55–69 | Average | Trung bình |
| 40–54 | Weak | Yếu |
| < 40 | High Risk | Rủi ro cao / thiếu dữ liệu |

### 5.5. Score breakdown

API trả:

```json
{
  "score": 72.4,
  "confidence": 0.83,
  "components": {
    "risk_management": { "score": 61.2, "weight": 25, "contribution": 15.3 },
    "consistency":     { "score": 78.0, "weight": 20, "contribution": 15.6 },
    "profitability":   { "score": 85.1, "weight": 15, "contribution": 12.8 },
    "trading_quality": { "score": 70.2, "weight": 15, "contribution": 10.5 },
    "copy_performance":{ "score": 55.0, "weight": 10, "contribution": 5.5 },
    "capital_efficiency": { "score": 60.0, "weight": 5, "contribution": 3.0 },
    "data_reliability":{ "score": 80.0, "weight": 10, "contribution": 8.0 }
  },
  "missing": ["sharpe"],
  "warnings": ["low_sample_copy_pnl"]
}
```

UI hiển thị thanh đóng góp từng thành phần. Đây là cách “giải thích điểm” rẻ và hiệu quả nhất.

---

## 6. Risk Rules

| ID | Rule | Ngưỡng | Severity |
|---|---|---|---|
| R01 | Runtime thấp | < 30 ngày | Insufficient |
| R02 | MDD cao | > 20% | High |
| R03 | MDD nghiêm trọng | > 30% | Critical |
| R04 | Leverage cao | max > 10x | High |
| R05 | Leverage rất cao | max > 20x | Critical |
| R06 | Position ROI gần -100% | min ROI ≤ −80% | Critical |
| R07 | Mẫu quá ít | total_orders < 20 | Low sample |
| R08 | Sharpe thiếu | null | Confidence penalty |
| R09 | Dữ liệu cũ | > 150 phút | Medium |
| R10 | Copier PnL âm trong khi lead dương | copier_pnl < 0, pnl > 0 | High |
| R11 | Copy AUM quá nhỏ | copy_aum / aum < 5% | Medium |
| R12 | WinRate 100% với mẫu nhỏ | win_rate = 100, total_orders < 20 | Suspicious |
| R13 | Fee drag cao | > 20% gross PnL | Medium |
| R14 | DCA/Martingale suspected | heuristic | High |
| R15 | ROI anomaly | robust z-score > 3 | High |
| R16 | AUM giảm mạnh | −30% trong 7 ngày | Medium |
| R17 | Nickname mặc định / mô tả trống | metadata | Data quality |

### Nguyên tắc

- Risk rule **không tự loại** trader khỏi danh sách; chỉ tạo event và ảnh hưởng score/confidence.
- Hard filter mới là thứ loại khỏi ranking.
- Mỗi event phải có `evidence` JSON: field, giá trị, ngưỡng, thời điểm.
- Không dùng AI để tạo risk event.

---

## 7. Ranking boards

| Bảng | Điều kiện | Công thức |
|---|---|---|
| **Overall** | Hard filters cơ bản | Score tổng |
| **Low Risk** | Runtime ≥ 90, MDD ≤ 20, max leverage ≤ 5, confidence ≥ 0.8 | Score + risk weight cao |
| **Consistency** | Runtime ≥ 90, ≥ 3 tháng dữ liệu | Positive months, recovery, stability |

Không làm bảng **High Return** riêng, vì nó khuyến khích chase ROI. ROI cao vẫn có thể lọc/sort trong Screener.

Mỗi lần chụp bảng xếp hạng phải lưu `ranking_snapshots` để vẽ “thay đổi thứ hạng theo thời gian”.

---

## 8. Ví dụ áp dụng: trader `5296057151807357697`

### 8.1. Dữ liệu

| Chỉ số | Giá trị | Đánh giá |
|---|---:|---|
| Runtime | 4 ngày | ❌ Không đủ |
| ROI 90D | 59,23% | Cao |
| PnL | 583.369 | Cao |
| MDD | 31,34% | ❌ Critical |
| Sharpe | null | ⚠️ Thiếu |
| WinRate (order) | 50% (5/10) | Mẫu nhỏ |
| Copier PnL | 1.005 | Rất thấp |
| AUM | 1.185.600 | Lớn nhưng 98% là tiền lead |
| Copy AUM | 22.234 | Nhỏ |
| Max leverage | 15x | ❌ High |
| Worst position ROI | −97,8% | ❌ Critical |
| Profit factor | 1,64 | Trung bình |
| Position win rate | 62,5% (5/8) | Mẫu nhỏ |

### 8.2. Kết luận

- **Bị loại ngay ở Stage 0** vì runtime 4 ngày < 30 ngày.
- **Không deep fetch** trader này trong vận hành bình thường.
- Dữ liệu trong mục 8.1 chỉ dùng làm **audit fixture** để test, không phải shortlist.
- Nếu vẫn hiển thị: badge “Excluded — insufficient history”.
- Nếu được đưa vào đánh giá thủ công, risk flags sẽ là: R03 (MDD > 30), R04 (leverage > 10), R06 (position ROI ≤ −80), R07 (mẫu ít), R08 (Sharpe null), R10 (copier PnL thấp), R11 (copy AUM < 5%).
- Đây là ví dụ điển hình của việc **ROI cao nhưng không thể kết luận tốt**.

---

## 9. Checklist trước khi implement scoring

- [ ] Chốt cohort (PUBLIC/SIGNAL/PRIVATE) cho từng bảng.
- [ ] Chốt tier criteria (Watch/Qualified/High).
- [ ] Chốt preset AUM (1k/5k/10k/20k).
- [ ] Chốt cách tính `traded_last_7d`.
- [ ] Chốt công thức `pre_score` và thứ tự deep fetch.
- [ ] Chốt cách xử lý null cho từng thành phần.
- [ ] Chốt minimum sample (20/50/100 order / 5 position / 30–180 ngày).
- [ ] Chốt cách hiển thị Sharpe null.
- [ ] Chốt cách hiển thị WinRate theo order vs position.
- [ ] Chốt hard filters.
- [ ] Chốt risk rule thresholds.
- [ ] Viết unit test cho normalize/score/missing.
- [ ] Viết test cho trader mẫu: phải ra “Excluded” ở Stage 0, không deep fetch, không ra top.
- [ ] Lưu score theo `config_version`.
