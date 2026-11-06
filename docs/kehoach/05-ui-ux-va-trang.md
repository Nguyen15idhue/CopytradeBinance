# 05 — UI/UX & THIẾT KẾ MÀN HÌNH

> Mục tiêu: người dùng ra quyết định trong **< 30 giây** khi sàng lọc, và hiểu **vì sao** một trader được điểm cao/thấp.  
> Không làm dashboard trang trí. Mỗi pixel phải phục vụ quyết định.

---

## 1. Nguyên tắc thiết kế

1. **Số liệu trước, màu sắc sau.** Không dùng màu để trang trí; chỉ dùng để cảnh báo.
2. **Luôn hiển thị cửa sổ thời gian.** `ROI 90D`, `MDD 90D`, không bao giờ chỉ ghi `ROI`.
3. **Luôn hiển thị nguồn.** `Binance`, `Derived`, `Estimated`.
4. **Không giấu sự thiếu dữ liệu.** `N/A` kèm lý do, không hiển thị `0`.
5. **Một màn hình = một quyết định.** Screener để chọn; Detail để xác nhận; Compare để chốt.
6. **Table là trung tâm.** Không biến mọi thứ thành card.
7. **Empty state phải hữu ích.** Gợi ý bỏ filter, mở rộng thời gian, xem trader mẫu.
8. **Tooltip ngắn, có ví dụ.** Không viết định nghĩa hàn lâm.

---

## 2. Layout tổng thể

```
┌─────────────────────────────────────────────────────────────┐
│ Topbar: Logo · Search · Data freshness · User menu          │
├──────────┬──────────────────────────────────────────────────┤
│ Sidebar  │  Nội dung                                        │
│ Screener │                                                  │
│ Ranking  │                                                  │
│ Compare  │                                                  │
│ Risk     │                                                  │
│ Settings │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

- Sidebar cố định, có thể thu gọn.
- Topbar luôn hiển thị **Data freshness**: “Cập nhật 12 phút trước”.
- Nếu dữ liệu cũ > 150 phút: banner vàng toàn trang.
- Mobile: sidebar thành drawer; table horizontal scroll; ẩn cột phụ.

---

## 3. Màn hình 1 — Screener

### Mục tiêu

Lọc từ universe 11k xuống shortlist 5–20 ứng viên trong < 30 giây.

### Bố cục

```
┌─────────────────────────────────────────────────────────────┐
│ Filter bar (sticky)                                         │
│ [Search] [Type] [Runtime] [ROI] [MDD] [Sharpe] [WinRate]    │
│ [Copiers] [CopyAum] [Leverage] [Risk] [Saved views] [Reset] │
├─────────────────────────────────────────────────────────────┤
│ 517 kết quả · Sắp xếp: Score ▼ · [Export CSV] [Compare 3]  │
├─────────────────────────────────────────────────────────────┤
│ ☐ Trader      Score  Conf  ROI90  MDD90  Sharpe  WR   Lev   │
│ ☐ ...                                                       │
└─────────────────────────────────────────────────────────────┘
```

### Cột mặc định

| Cột | Nội dung | Ghi chú |
|---|---|---|
| ☐ | Chọn để compare | Max 4 |
| Trader | Avatar + nickname + type | Click mở detail |
| Tier | High / Qualified / Watch | Màu theo tier |
| Score | 0–100 + band | Có tooltip breakdown |
| Confidence | 0–100% | Badge màu |
| ROI 90D | % | Kèm benchmark delta |
| MDD 90D | % | Đỏ nếu > 20 |
| Sharpe | Số hoặc `N/A` | `N/A` không tô đỏ |
| WinRate | % + win/total | Low sample badge |
| Runtime | Ngày | < 30 → badge “New” |
| Copiers | Số hiện tại | 0 → xám |
| Copy AUM | USDT | |
| Max Leverage | x | Từ position-history |
| Risk | Low/Medium/High/Critical | |
| Freshness | Thời gian | |

### Cột tùy chọn (ẩn mặc định)

- PnL 90D
- Calmar
- Profit Factor
- Position Win Rate
- Avg Holding
- Fee Drag
- Top Symbol
- Tags
- Last Trade

### Filter

| Filter | Kiểu | Mặc định |
|---|---|---|
| Search | Text | — |
| Portfolio type | Multi-select | PUBLIC + SIGNAL |
| **Potential tier** | Multi-select | **High + Qualified + Watch** |
| Include excluded | Toggle | Off |
| Runtime | Min/max days | ≥ 30 |
| ROI 90D | Min/max | — |
| MDD 90D | Max | — |
| Sharpe | Min | — |
| WinRate | Min | — |
| Total Orders | Min | 20 |
| Copiers | Min | — |
| Copy AUM | Min | — |
| Max Leverage | Max | — |
| Risk level | Multi-select | — |
| Has Sharpe | Toggle | — |
| Only with copiers | Toggle | — |
| Saved view | Dropdown | — |

### Hành vi quan trọng

- **Funnel summary** trên đầu bảng: `Universe 11.130 → Watch 517 → Qualified 113 → High 13`.
- **Tier badge** trên mỗi dòng: High / Qualified / Watch / Excluded.
- **Count preview** ngay trên filter: “1.234 trader khớp”.
- Nếu filter trả về 0: gợi ý “Thử bỏ MDD ≤ 15” hoặc “Mở rộng runtime”.
- Sort mặc định: Score DESC.
- Không cho sort mặc định theo ROI.
- Chọn > 4 trader → disable compare, hiển thị “Tối đa 4”.
- Lưu view: tên + filter JSON, chỉ admin/viewer tự lưu.
- Export CSV: chỉ export cột đang hiển thị, kèm metadata filter.

### Empty state

```
Không có trader khớp bộ lọc.
[ Bỏ filter MDD ] [ Mở rộng runtime lên 30 ngày ] [ Xem trader mẫu ]
```

---

## 4. Màn hình 2 — Trader Detail

### Mục tiêu

Trả lời: “Trader này có đáng theo dõi không? Rủi ro lớn nhất là gì? Dữ liệu có đủ tin không?”

### Bố cục

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Avatar · Nickname · Type · Status · Tags            │
│ Score 72 · Confidence 83% · Risk Medium · [Compare] [AI]    │
├─────────────────────────────────────────────────────────────┤
│ 10 chỉ số cốt lõi (grid 5x2)                                │
├─────────────────────────────────────────────────────────────┤
│ [Equity/ROI] [Drawdown] [Monthly Return]                    │
├─────────────────────────────────────────────────────────────┤
│ Score breakdown · Risk flags · What's missing               │
├─────────────────────────────────────────────────────────────┤
│ Positions · Trades summary · Transfers                      │
└─────────────────────────────────────────────────────────────┘
```

### Header

- Avatar, nickname, `portfolio_type`.
- Status badge: ACTIVE / PAUSED / CLOSED.
- Tags: `MEDIUM_LEVERAGE`, `TradFi`, `API`.
- Tier: `High` / `Qualified` / `Watch` / `Excluded`.
- Nếu Excluded: badge + lý do (runtime, ROI, số lệnh, AUM, full slot…).
- Runtime: “Mở 4 ngày trước” + badge “Insufficient history” nếu < 30.
- Score + band.
- Confidence + tooltip.
- Risk level.
- Nút Compare, AI Analyze (chỉ bật cho Qualified/High).

### 10 chỉ số cốt lõi

| # | Chỉ số | Ghi chú |
|---|---|---|
| 1 | ROI 90D | + benchmark delta |
| 2 | MDD 90D | |
| 3 | Sharpe | `N/A` nếu null |
| 4 | WinRate (order) | kèm win/total |
| 5 | Profit Factor | derived |
| 6 | Max Leverage | derived |
| 7 | Avg Holding | derived |
| 8 | Copier PnL | |
| 9 | Copy AUM | |
| 10 | Copiers | |

Mỗi ô có tooltip: định nghĩa + nguồn + cửa sổ.

### Biểu đồ

1. **ROI vs Benchmark** — ROI 90D và BTC buy&hold.
2. **Drawdown** — chỉ vẽ nếu có dữ liệu; ghi rõ “estimated from published MDD” nếu không có equity.
3. **Monthly Return** — nếu đủ dữ liệu; nếu không, empty state.
4. **Position PnL distribution** — từ position-history.

### Score breakdown

```
Risk Management   61/100  ███████░░░  15.3/25
Consistency       78/100  █████████░  15.6/20
Profitability     85/100  ██████████  12.8/15
Trading Quality   70/100  ███████░░░  10.5/15
Copy Performance  55/100  █████░░░░░   5.5/10
Capital Efficiency 60/100 ██████░░░░   3.0/5
Data Reliability  80/100  ████████░░   8.0/10
```

Bên cạnh: “Vì sao điểm này thấp?” — text deterministic, không dùng AI.

### Risk flags

| Severity | Ví dụ |
|---|---|
| Critical | MDD > 30%, position ROI ≤ −80%, leverage > 20x |
| High | MDD > 20%, leverage > 10x, copier PnL âm |
| Medium | Data stale, fee drag cao, copy AUM < 5% |
| Low | Sample nhỏ, Sharpe null |

Mỗi flag mở ra evidence: field, value, threshold, timestamp.

### What’s missing

Luôn hiển thị panel:

```
Dữ liệu chưa đủ để kết luận:
- Sharpe: chưa đủ 30 ngày
- Open positions: Binance không cung cấp
- Per-copier: Binance không cung cấp
- Funding: không có trong trade-history
```

Đây là điểm tạo niềm tin, không phải điểm yếu.

### Positions

- Bảng: symbol, side, leverage, margin mode, opened, closed, holding, PnL, ROI.
- Filter symbol/side.
- Badge “Near liquidation” nếu ROI ≤ −80%.
- Không hiển thị open positions.

### Trades summary

- Tổng fill, fill/day, buy/sell, notional avg/median/max.
- Fees, realized PnL.
- Top symbols.
- DCA/martingale badge nếu suspected.
- Không hiển thị từng fill ở MVP (quá nhiều); có thể tải thêm.

### Transfers

- Nạp/rút, net flow, timeline.
- Cảnh báo nếu flow lớn làm ROI khó so sánh.

---

## 5. Màn hình 3 — Compare

### Mục tiêu

Chốt 2–4 trader.

### Bố cục

- Bảng so sánh: 2–4 cột.
- Chart overlay: ROI, drawdown.
- Correlation matrix.
- “Winner by category”: Risk, Consistency, Profitability.
- Cảnh báo nếu compare trader khác `portfolio_type`.

### Bảng

| Chỉ số | Trader A | Trader B | Trader C |
|---|---:|---:|---:|
| Score | | | |
| Confidence | | | |
| ROI 90D | | | |
| MDD 90D | | | |
| Sharpe | | | |
| WinRate | | | |
| Profit Factor | | | |
| Max Leverage | | | |
| Copy PnL | | | |
| Copy AUM | | | |
| Runtime | | | |
| Risk | | | |

### Correlation

- Tính từ daily returns (chartItems), sau khi lọc flow.
- Ghi rõ “estimated”.
- Nếu < 30 điểm chung → `N/A`.

---

## 6. Màn hình 4 — Settings & Data Health

### Mục tiêu

Toàn bộ cấu hình chỉnh trên web, không cần SSH.

### Tabs

| Tab | Nội dung |
|---|---|
| **Data Collection** | Chu kỳ, portfolio type, giới hạn, retry, chạy thủ công |
| **Shortlist / Funnel** | Preset AUM, ngưỡng tier, pre-score, xem excluded, chạy lại phễu |
| **Data Health** | Lần chạy cuối, số trader theo tier, lỗi, stale, null rates |
| **Scoring** | Trọng số, hard filters, version, rollback |
| **Risk Rules** | Ngưỡng, bật/tắt, severity |
| **AI** | Provider, model, temperature, budget, prompt version |
| **Ranking** | Bảng, filter, thời gian |
| **System** | Log, backup, version, health |

### Data Health

```
Lần chạy cuối: 2026-11-06 15:00 UTC (12 phút trước)
Trạng thái: SUCCESS
Universe: 11.130 / 11.130
Watch: 517 · Qualified: 113 · High: 13
Deep fetch: 113–313 detail · 13–50 full trades
Lỗi: 3 (0.02%)
Null Sharpe: 34,7%
Null AI summary: 97,8%
Stale > 150 phút: 12 trader
```

Nút: `Run now`, `View logs`, `Download report`.

### Scoring

- Slider/number input cho từng trọng số.
- Tổng phải = 100; nếu không, disable Save.
- “Preview impact”: so sánh top 20 trước/sau.
- Save → tạo version mới + audit log.
- Rollback về version cũ.

---

## 7. Màn hình 5 — AI Report (phase 5)

- Nút “Analyze” trên Trader Detail.
- Report gồm:
  - Tóm tắt 3 câu.
  - Điểm mạnh (có evidence).
  - Điểm yếu (có evidence).
  - Risk flags.
  - “Chưa đủ dữ liệu để kết luận”.
  - Không đưa ra lời khuyên đầu tư.
- Hiển thị model, prompt version, cost, thời gian.
- Không auto chạy mọi trader.
- Cooldown 24h/trader.

---

## 8. Component & style

### Component cần có

- `MetricCard` — value, label, tooltip, badge, delta.
- `ScoreBadge` — score + band + confidence.
- `RiskBadge` — severity.
- `DataSourceBadge` — Binance / Derived / Estimated.
- `ConfidenceBadge`.
- `EmptyState`.
- `ErrorState`.
- `FilterBar`.
- `DataTable` — sort, virtualize, column visibility.
- `ChartCard` — title, source, timeframe.
- `TooltipInfo`.
- `InsightList` — deterministic insights.

### Màu

| Ý nghĩa | Màu |
|---|---|
| Tốt | Green |
| Trung bình | Amber |
| Xấu / Critical | Red |
| Thiếu dữ liệu | Gray |
| Derived | Blue outline |

Không dùng đỏ cho `N/A`.

### Typography

- Số liệu: tabular nums, font mono cho bảng.
- Tiêu đề: semibold.
- Tooltip: 12–13px, tối đa 2 dòng.

---

## 9. Accessibility

- Contrast ≥ 4.5:1.
- Không chỉ dùng màu để biểu đạt; luôn có text/icon.
- Keyboard navigation cho filter/table.
- Focus visible.
- Tooltip truy cập được bằng keyboard.
- Chart có bảng dữ liệu thay thế.

---

## 10. Những thứ không hiển thị

- Không hiển thị “open positions” như thể có dữ liệu.
- Không hiển thị “copy fill rate” hoặc “slippage” giả.
- Không hiển thị MDD tự tính từ `chartItems`.
- Không hiển thị Sharpe 0 khi null.
- Không hiển thị ROI mà không ghi cửa sổ.
- Không hiển thị “AI dự đoán giá”.
- Không hiển thị “nên copy trader này” như một khuyến nghị đầu tư.
- Không hiển thị badge Binance như chứng nhận chất lượng.
- Không hiển thị trader `excluded` trong view mặc định; chỉ hiện khi bật “Include excluded”.
- Không hiển thị `pre_score` như thể là score chất lượng cuối cùng.

---

## 11. Checklist UI trước khi release

- [ ] Mọi chỉ số có tooltip định nghĩa + nguồn.
- [ ] Mọi chỉ số có cửa sổ thời gian.
- [ ] `N/A` không bị hiển thị là 0.
- [ ] Có empty state cho mọi màn hình.
- [ ] Có loading skeleton.
- [ ] Có error state + retry.
- [ ] Có data freshness toàn trang.
- [ ] Có “What’s missing”.
- [ ] Responsive 1280 / 1024 / 768.
- [ ] Không có chart nào không có dữ liệu thật.
- [ ] Không có màu đỏ cho `N/A`.
- [ ] Compare max 4.
- [ ] Filter count preview đúng.
