# PHASE 0 REPORT — Data Spike & Pre-filter

> **Ngày chạy:** 2026-11-06  
> **Phạm vi:** PUBLIC + SIGNAL, `timeRange=90D`  
> **Mục tiêu:** xác minh BAPI, chốt phễu tiềm năng, đo false negative, quyết định go/no-go  
> **Nguyên tắc:** chỉ phân tích/screener; không auto-trade, không đặt lệnh, không WebSocket realtime

---

## 1. Kết luận nhanh

**Quyết định: GO CÓ ĐIỀU KIỆN.**

Dữ liệu BAPI đủ ổn định để xây Screener & Risk Analytics. Phễu tiềm năng hoạt động đúng. Không có false negative thực sự trong 50 trader bị loại được audit.

Các điều kiện bắt buộc trước Phase 1:

1. **MDD chỉ hiển thị `performance.mdd`.** Không dùng MDD tự tính từ `chartItems` làm số production.
2. **Luôn gắn nhãn window** cho MDD/ROI/PnL/Sharpe vì các window khác nhau trả giá trị khác nhau.
3. **Xác minh `lastTradeTime` ở tầng detail** trước khi ranking; list payload không có field này.
4. **Hiển thị WinRate theo order và theo position tách biệt**, không gộp.
5. **Sharpe null 34,9%** phải hiển thị `N/A` + confidence, không chấm 0.
6. **Không hứa** open positions, per-copier PnL, funding, liquidation, copy slippage — các endpoint này không tồn tại.

---

## 2. Endpoint & hợp đồng dữ liệu

### 2.1. Sáu endpoint cốt lõi

| Endpoint | Base | Kết quả Phase 0 |
|---|---|---|
| `POST /home-page/query-list` | `BASE_F` | Ổn định, page size tối đa **30** |
| `GET /lead-portfolio/detail` | `BASE_F` | Ổn định |
| `GET /lead-portfolio/performance` | **`BASE_P`** | Đủ 4 window 7D/30D/90D/180D |
| `GET /lead-portfolio/position-history` | `BASE_F` | Ổn định, page size 50 dùng nội bộ |
| `GET /lead-portfolio/trade-history` | `BASE_F` | Ổn định, page size tối đa **200** |
| `GET /lead-portfolio/transfer-history` | `BASE_F` | Ổn định |

- `BASE_F = https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade`
- `BASE_P = https://www.binance.com/bapi/futures/v1/public/future/copy-trade`
- `performance` gọi bằng `BASE_F` trả **404**; bắt buộc dùng `BASE_P`.

### 2.2. Endpoint không tồn tại

Đã probe 6 đường dẫn, **6/6 trả HTTP 404**:

- open positions: `/lead-portfolio/position`, `/lead-portfolio/positions`, `/lead-portfolio/current-position`
- copier list: `/lead-portfolio/copier-list`
- funding: `/lead-portfolio/funding-history`, `/lead-portfolio/funding-fee`

Hệ quả: MVP không thể hiển thị vị thế đang mở, PnL từng copier, funding fee, liquidation price, hay copy slippage.

---

## 3. Universe & phễu tiềm năng

### 3.1. Universe live

| Nguồn | Số trader | Coverage | Thời gian |
|---|---:|---:|---:|
| PUBLIC | 8.970 | 100% | 60,5s |
| SIGNAL | 2.154 | 100% | 14,5s |
| **Tổng** | **11.124** | **100%** | **78,0s** |

- 371 trang, **0 trang lỗi**, không retry thất bại.
- Không quét PRIVATE.
- Dedupe theo `leadPortfolioId`: 11.124 dòng, 11.124 ID duy nhất.
- `chartItems` có đúng **90 điểm** ở **11.124/11.124** trader.

### 3.2. Phễu

| Tầng | PUBLIC | SIGNAL | Tổng |
|---|---:|---:|---:|
| Watch-only (C) | 358 | 48 | 406 |
| **Watch (gồm B/A)** | **457** | **58** | **515** |
| Qualified-only (B) | 86 | 10 | 96 |
| **Qualified gồm High (B+A)** | **99** | **10** | **109** |
| High-only (A) | 13 | 0 | 13 |
| Excluded | 8.513 | 2.096 | 10.609 |

Ghi chú: B và A là **tập con** của Watch, không cộng dồn. `union_deep_fetch = Watch = 515`.

Lý do loại chính (có overlap, trên toàn universe):

| Lý do | Số trader |
|---|---:|
| AUM < 5.000 | 10.493 |
| ROI ≤ 0 | 8.096 |
| PnL ≤ 0 | 7.924 |
| WinRate < 40 | 4.876 |
| MDD > 40 | 4.876 |
| Runtime < 30 ngày | 3.316 |
| Không trade 7D (proxy) | 1.790 |
| Hết slot | 8 |

Số live lệch nhẹ so với snapshot kế hoạch (11.130 → 11.124; Watch 517 → 515; Qualified 113 → 109; High 13 → 13). Đây là dao động tự nhiên của danh sách, không phải lỗi code; không ép số.

---

## 4. Mẫu & deep fetch

### 4.1. Cấu trúc mẫu

| Nhóm | Kế hoạch | Thực tế | Lý do |
|---|---:|---:|---|
| A — High | 20 | **13** | Toàn bộ universe chỉ có 13 High |
| B — Qualified | 20 | **20** | Đủ |
| C — Watch-only | 20 | **20** | Đủ |
| Excluded | 10 | **10** | Đủ 8 lý do loại + fixture |
| **Tổng** | **70** | **63** | Thiếu 7 do trần cấu trúc của A |

- Chọn theo stratified sampling có seed cố định `20261106`.
- Excluded phủ đủ 8 lý do: `no_trade_7d`, `runtime_lt_30`, `roi_le_0`, `pnl_le_0`, `winrate_lt_40`, `mdd_gt_40`, `aum_lt_5000`, `no_slots`.
- Fixture `5296057151807357697` bắt buộc có mặt; bị loại bởi `runtime_lt_30` (~4,11 ngày tuổi).

### 4.2. Deep fetch

| Chỉ số | Kết quả |
|---|---|
| Trader | 63/63 thành công |
| Thời gian | 153,34s, 6 worker |
| Endpoint lỗi | 0 |
| Dữ liệu mỗi trader | detail + 4 performance + positions + transfers + trade page 1 |
| Full trade history | **Không lấy** cho bất kỳ trader nào |

Fixture: `ACTIVE`, `SIGNAL`, 8 positions, 5.292 trades, 17 transfers.

**Giới hạn đã biết của lần fetch này:**

| Dữ liệu | Đã lấy | Ghi chú |
|---|---:|---|
| Positions | **13.589 / 22.641 dòng (60,0%)** | 7/63 trader bị cắt ở 1.000 vị thế gần nhất (cap 20 trang × 50) |
| Trades | **10.967 dòng** | Chỉ page 1 (tối đa 200/trader); tổng thực tế 112.759 |
| Transfers | **2.063 / 2.063 dòng** | Đầy đủ |

Các chỉ số suy ra từ position-history (leverage, holding time, position win rate) của 7 trader bị cắt chỉ phản ánh 1.000 vị thế gần nhất. Phase 1 nếu cần full history phải nâng cap và fetch theo nhu cầu.

---

## 5. Kiểm chứng chỉ số

### 5.1. MDD — câu hỏi trọng tâm

**Kết luận: đúng là production phải lấy MDD trực tiếp từ Binance. Nhưng lý do không phải “tự tính luôn sai”, mà là published là định nghĩa chính thức và `chartItems` chỉ là chuỗi ROI theo ngày.**

Con số **88,67%** trong tài liệu cũ là **lỗi công thức**, không phải bằng chứng dữ liệu `chartItems` hỏng:

| Cách tính | MDD fixture | Đánh giá |
|---|---:|---|
| Coi `chartItems.value` là mức equity | 88,67% | ❌ Sai |
| `equity = 1 + value / 100` | 31,3384% | ✅ Đúng |
| Binance published | 31,338369% | ✅ Chuẩn |

Trên 63 trader:

- So sánh được: **63/63**.
- Sai số tuyệt đối lớn nhất: **4,9 × 10⁻⁷ pp** (chỉ là làm tròn).
- Số ca lệch > 0,0001 pp: **0**.
- Nếu dùng công thức sai (ROI là equity): median lệch **70,18 pp**, **59/63** ca lệch > 5 pp.

**Vì sao vẫn dùng published:**

1. Là định nghĩa chính thức, đã xử lý nạp/rút theo Binance.
2. `chartItems` chỉ có điểm chốt theo ngày, bỏ qua drawdown trong ngày.
3. Không có NAV/equity thật; mọi tự tính đều là xấp xỉ từ ROI.
4. MDD **phụ thuộc window**: chỉ **6/63** trader có MDD giống nhau ở cả 4 window; chênh tối đa giữa các window là **70,26 pp**.

**Quy tắc production:** hiển thị và xếp hạng bằng `performance.mdd`. Tự tính từ `chartItems` chỉ dùng để audit/sanity-check.

### 5.2. WinRate

| Chỉ số | Kết quả |
|---|---|
| So sánh được | 59/63 |
| Median lệch order vs position | **2,52 pp** |
| Max lệch | **33,33 pp** |
| Số ca lệch > 5 pp | **18** |
| `winRate` vs `winOrders / totalOrder` | Khớp tuyệt đối |

Kết luận: `winRate` của Binance là **theo order**, không phải theo position. Phải ghi nhãn rõ; không trộn hai định nghĩa.

### 5.3. Sharpe null

| Phạm vi | Null rate |
|---|---:|
| Universe 11.124 | **34,9%** |
| Sample 63 | **4,8%** |

Kết luận: null là phổ biến, không được chấm 0. Phải hiển thị `N/A` và giảm confidence.

### 5.4. AUM vs CopyAum

| Chỉ số | Kết quả |
|---|---:|
| Median `copyAum / aum` | **0,2486** |
| CopyAum < 5% AUM | **28/63** |
| CopyAum < 1% AUM | **23/63** |

Kết luận: AUM chủ yếu là tiền của lead, không phải tiền copier. Phải hiển thị riêng CopyAum.

### 5.5. Lead PnL vs Copier PnL

| Chỉ số | Kết quả |
|---|---:|
| Median `copierPnl / leadPnl` | **0,0002** |
| Copier PnL < 1% lead PnL | **35/63** |
| Copier PnL âm | **17/63** |

Kết luận: lead PnL không đại diện cho trải nghiệm copier. Không dùng lead PnL để quảng cáo “copier kiếm được bao nhiêu”.

### 5.6. Fee âm (rebate)

| Chỉ số | Kết quả |
|---|---:|
| Trader có ít nhất 1 fill fee âm | **56/58** |
| Tổng fee page 1 | **−5.835,4656** |
| Trader có fee = 0 toàn bộ page 1 | 2 |

Kết luận: fee âm là bình thường (rebate), không phải lỗi dữ liệu. Không cộng fee như chi phí dương.

### 5.7. `chartItems`, young portfolio, `positionShow`

- `chartItems` = 90 điểm: **63/63** sample, **11.124/11.124** universe.
- Young portfolio:
  - 1/2 có cả 4 window giống hệt (portfolio ~4,11 ngày).
  - Portfolio ~29,98 ngày đã khác giữa các window → không thể giả định “dưới 30 ngày là giống nhau”.
- `positionShow = false` ở **30 trader**, nhưng **cả 30 vẫn trả position-history đầy đủ** → không dùng cờ này để chặn fetch.

---

## 6. Activity proxy `traded_last_7d`

List payload **không có** `lastTradeTime` (0/11.124 dòng). Phase 0 dùng proxy `max−min` của 8 điểm `chartItems` cuối, rồi so với `detail.lastTradeTime`.

| Chỉ số | Kết quả |
|---|---:|
| So sánh | 63 |
| Khớp | **60/63 = 95,2%** |
| False positive | **3** |
| False negative | **0** |

3 false positive thuộc C (1) và excluded (2): proxy báo “có trade” nhưng lần trade cuối đã 68,88 / 274,07 / 854,57 ngày.

Kết luận: proxy **không bỏ sót trader đang hoạt động**, nhưng có thể giữ lại trader đã ngừng trade. Vì vậy phải xác minh `lastTradeTime` ở tầng detail trước khi ranking.

---

## 7. Audit false negative

Chọn 50 trader excluded, phủ 7 primary reason, gọi detail + performance 90D.

| Định nghĩa | Kết quả | Tỷ lệ |
|---|---:|---:|
| `fn_prompt` — literal: ACTIVE + ROI>0 + PnL>0 + totalOrder≥20 + còn slot | 12/50 | **24,0%** |
| `fn_watch_eligible` — thêm runtime≥30, WR≥40, MDD≤40, AUM≥5k, lastTradeTime≤7d | **0/50** | **0,0%** |
| `fn_qualified_eligible` — thêm ngưỡng B | **0/50** | **0,0%** |

12 ca `fn_prompt` bị loại có chủ đích vì AUM < 5k hoặc MDD > 40. Đây **không phải** false negative của phễu.

**Gate dùng `fn_watch_eligible_rate ≤ 5%` → đạt 0%.**

---

## 8. Rate limit & thời gian

### 8.1. Rate limit

| Concurrency | Request | OK | Rate-limited | Failed | Median |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 0 | 0 | ~650–685 ms |
| 5 | 5 | 5 | 0 | 0 | ~1,1–1,35 s |
| 10 | 10 | 10 | 0 | 0 | ~1,5–1,6 s |

Tổng: **32 request, 0 rate-limit, 0 lỗi**. 10 concurrent vẫn an toàn, nhưng production nên giữ 5–6 worker.

### 8.2. Thời gian thực đo / ngoại suy

| Tác vụ | Kết quả | Loại |
|---|---:|---|
| Scan 11k (371 trang) | **78,0s** | Thực đo |
| Performance 517 trader (2.068 request) | **~6,9 phút** | Ngoại suy từ 12 trader × 4 window = 9,51s |
| Detail 113 trader | **~23s** | Ngoại suy từ 20 trader = 4,06s |
| Detail 313 trader | **~64s** | Ngoại suy |
| Full trades 13 High (~158 trang) | **~32s** | Ước tính từ `total` page 1 của nhóm A |

Throughput thực tế ~5 request/s với 6 worker. Không fetch full trade-history trader nào trong Phase 0.

---

## 9. Gate Phase 0

| Tiêu chí | Mục tiêu | Thực tế | Đạt |
|---|---|---|---|
| 6 endpoint ổn định | Không lỗi | 0 lỗi trên 11.124 list + 63 deep + 50 audit | ✅ |
| Raw file | 70 trader | **63 trader** (A chỉ có 13) | ⚠️ thiếu do cấu trúc |
| Tiêu chí phễu | Rõ ràng, tái lập được | Có code + CSV + giải thích lệch | ✅ |
| False negative | < 5% | **0%** (`fn_watch_eligible`) | ✅ |
| Rate limit | Không bị chặn | 0/32 | ✅ |
| Performance `BASE_P` | Đủ 4 window | Đủ | ✅ |

**Lý do GO CÓ ĐIỀU KIỆN thay vì GO:**

- Mẫu 63 thay vì 70 là **giới hạn cấu trúc** (universe chỉ có 13 High), không phải lỗi dữ liệu. Hạ ngưỡng A để ép đủ 20 sẽ làm hỏng định nghĩa tier.
- Các điều kiện về MDD, WinRate, Sharpe null, `lastTradeTime`, và endpoint thiếu phải được đưa vào thiết kế Phase 1 ngay từ đầu.

---

## 10. Artifact

| File | Nội dung |
|---|---|
| `phase0/data/universe_90d.jsonl` | 11.124 trader + tier + lý do |
| `phase0/data/tier_summary.csv` | Tổng hợp phễu theo nguồn |
| `phase0/data/scan_summary.json` | Metadata + thời gian scan |
| `phase0/data/sample_manifest.csv` | 63 trader mẫu |
| `phase0/data/sample_summary.json` | Cấu trúc mẫu + strata |
| `phase0/data/deep_fetch_status.csv` | Trạng thái 63 trader |
| `phase0/data/deep_fetch_summary.json` | Tổng hợp deep fetch |
| `phase0/data/activity_check.csv` | Proxy vs `lastTradeTime` |
| `phase0/data/audit_excluded.csv` | 50 trader audit |
| `phase0/data/audit_summary.json` | False negative rates |
| `phase0/data/indicator_quality.csv` | Kiểm chứng 7 nhóm chỉ số |
| `phase0/data/indicator_quality_summary.json` | Tổng hợp kiểm chứng |
| `phase0/data/rate_limit_test.csv` | 32 request thô |
| `phase0/data/rate_limit_summary.json` | Tổng hợp rate limit |
| `phase0/data/raw/` | Raw bundle theo tier/trader |

---

## 11. Việc phải làm ở Phase 1

1. Dùng `performance.mdd` làm nguồn duy nhất cho hiển thị/xếp hạng.
2. Luôn lưu `timeRange` cùng metric; không trộn 7D/30D/90D/180D.
3. Gọi detail trước khi ranking để lấy `lastTradeTime`, `startTime`, `aumAmount`, `copyAum`.
4. Hiển thị `winRate` (order) và `positionWinRate` (derived) tách biệt.
5. Sharpe null → `N/A`, confidence thấp; không chấm 0.
6. Không cam kết open positions/per-copier/funding.
7. Giữ 5–6 worker; backoff khi gặp 429/418.
8. Lưu raw response để tái kiểm chứng khi Binance đổi schema.
