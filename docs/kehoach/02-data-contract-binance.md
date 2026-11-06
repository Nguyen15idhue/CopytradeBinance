# 02 — DATA CONTRACT: BINANCE COPY TRADING BAPI

> Đây là tài liệu quan trọng nhất của dự án. Mọi chỉ số phải truy được về một field trong tài liệu này.  
> Kết quả kiểm chứng: **06/11/2026**, trên trader `5296057151807357697` và toàn bộ danh sách PUBLIC/SIGNAL/PRIVATE.

---

## 1. Bản chất nguồn dữ liệu

Đây là **BAPI nội bộ mà web app Binance gọi**, không phải API chính thức trong tài liệu developer của Binance.

- Không cần login, không cần API key, không cần cookie.
- Có thể đổi path, đổi field, chặn IP hoặc rate limit bất kỳ lúc nào.
- ToS của Binance vẫn áp dụng.
- Không được bán lại raw data.
- Nên cache, rate-limit lịch sự, ghi nguồn.

**Hệ quả thiết kế:** Collector phải dùng **Adapter pattern**. Không được để 80% code phụ thuộc trực tiếp vào BAPI.

---

## 2. Base URL & header

```python
BASE_F = "https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade"
BASE_P = "https://www.binance.com/bapi/futures/v1/public/future/copy-trade"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "clienttype": "web",
    "lang": "en",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/",
}
```

> **Quan trọng:** `performance` nằm ở `BASE_P` (public), không phải `BASE_F`.  
> Gọi `BASE_F + /lead-portfolio/performance` sẽ trả **404**.

---

## 3. Danh sách endpoint

| # | Tầng | Method | Path | Base | Page size max |
|---|---|---|---|---|---|
| 1 | List | POST | `/home-page/query-list` | `BASE_F` | **30** |
| 2 | Detail | GET | `/lead-portfolio/detail?portfolioId=...` | `BASE_F` | — |
| 3 | Performance | GET | `/lead-portfolio/performance?portfolioId=...&timeRange=90D` | **`BASE_P`** | — |
| 4 | Position history | POST | `/lead-portfolio/position-history` | `BASE_F` | 50 (khuyến nghị) |
| 5 | Trade history | POST | `/lead-portfolio/trade-history` | `BASE_F` | **200** |
| 6 | Transfer history | POST | `/lead-portfolio/transfer-history` | `BASE_F` | 50 (khuyến nghị) |

Không có endpoint public cho:

- Vị thế đang mở (`position`, `positions`, `current-position`, `open-positions` → 404).
- Danh sách copier / PnL từng copier.
- Funding fee.
- Liquidation price / margin ratio hiện tại.
- Copy fill rate / slippage.

---

## 3.1. Phễu lọc tiềm năng (bắt buộc)

**Không deep-fetch toàn bộ 13.004 trader.**  
Chỉ deep-fetch trader vượt qua phễu. Đây là thay đổi quan trọng nhất so với v1/v2.0.

### 3.1.1. Universe — chỉ quét PUBLIC + SIGNAL

| Loại | Số lượng | Quét mặc định? | Lý do |
|---|---:|---|---|
| PUBLIC | 8.976 | ✅ Có | Copy portfolio công khai |
| SIGNAL | 2.154 | ✅ Có | Signal provider, có thể copy |
| PRIVATE | 1.874 | ❌ Không | Không mở copy công khai |
| **Tổng universe** | **11.130** | | |

> `PRIVATE` chỉ bật khi có nhu cầu nghiên cứu nội bộ; mặc định không quét.

### 3.1.2. Stage 0 — Pre-filter trên list (rẻ, không gọi detail)

Chỉ cần **một lần quét list 90D**. Không cần quét 7D/30D/180D cho toàn bộ universe; các window đó lấy từ `/performance` cho shortlist.

Chỉ dùng các field có sẵn trong `query-list`:

| Điều kiện | Ngưỡng mặc định | Field |
|---|---|---|
| Có giao dịch 7 ngày gần nhất | `max(last 8 chartItems) − min > 0` | `chartItems` |
| Runtime | ≥ 30 ngày | `startTime` |
| ROI 90D | > 0 | `roi` |
| PnL 90D | > 0 | `pnl` |
| WinRate | ≥ 40% | `winRate` |
| MDD | ≤ 40% | `mdd` |
| AUM | ≥ 5.000 USDT | `aum` |
| Còn slot copy | `currentCopyCount < maxCopyCount` | detail/list |
| Max copy | > 0 | `maxCopyCount` |

**Kết quả thực đo (06/11/2026):**

| Tầng | PUBLIC | SIGNAL | Tổng |
|---|---:|---:|---:|
| Universe | 8.976 | 2.154 | 11.130 |
| **C — Watch** (pre-filter) | **460** | **57** | **517** |
| B — Qualified (ước tính) | 103 | 10 | 113 |
| A — High (ước tính) | 13 | 0 | 13 |

> Đây là **upper bound**. Sau khi lọc `totalOrder` và `status`, số thực tế sẽ giảm.  
> **B và A là subset của C**, không cộng dồn. Union deep-fetch = **517**.

### 3.1.3. Preset AUM

| Preset | AUM min | PUBLIC Watch | Ghi chú |
|---|---:|---:|---|
| Broad | 1.000 | ~1.021 | Nhiều trader nhỏ, nhiễu hơn |
| **Balanced (mặc định)** | **5.000** | **460** | Cân bằng |
| Strict | 10.000 | ~314 | Ít nhiễu, bỏ lỡ trader nhỏ |

### 3.1.4. Stage 1 — Performance filter

Chỉ gọi `/performance` cho **517 trader Watch**.

| Điều kiện | Ngưỡng |
|---|---|
| `totalOrder` 90D | ≥ 20 (Watch) / ≥ 50 (Qualified) / ≥ 100 (High) |
| `winOrders` | > 0 |
| `mdd` | không null |
| `roi` | > 0 |

Sau bước này, shortlist thực tế thường còn **300–450 trader**.

### 3.1.5. Stage 2 — Detail + position + transfer

Chỉ gọi detail/position/transfer cho:

- Toàn bộ **B — Qualified** (~113).
- Các **C — Watch** có performance nổi bật nhưng runtime 30–90 ngày (tối đa 200).

Điều kiện detail:

| Điều kiện | Giá trị |
|---|---|
| `status` | `ACTIVE` |
| `isPaused` | `false` |
| `maxCopyCount` | > `currentCopyCount` |
| `positionShow` | không bắt buộc (history vẫn lấy được) |

### 3.1.6. Stage 3 — Full trade history + AI

Chỉ gọi `trade-history` đầy đủ (tất cả page) cho:

- Toàn bộ **A — High** (~13).
- Top 30–50 **B — Qualified** theo `pre_score`.

Không gọi full trade history cho toàn bộ shortlist.

### 3.1.7. Pre-score (chỉ để xếp thứ tự deep fetch)

```python
pre_score = (
    0.30 * norm(roi_90d) +
    0.30 * norm(-mdd_90d) +
    0.20 * norm(sharpe_90d, missing=50) +
    0.10 * norm(win_rate_90d) +
    0.10 * norm(min(runtime_days / 180, 1))
)
```

- `norm()` là percentile rank trong cohort PUBLIC/SIGNAL.
- Sharpe null → 50 (neutral), không phải 0.
- Dùng để quyết định **thứ tự deep fetch**: High → Medium → Low, trong cùng tier sort `pre_score` desc.
- **Không dùng pre_score làm score cuối.**

### 3.1.8. Ưu tiên fetch

```
1. A — High Potential      (~13)   → full trades + AI
2. B — Qualified           (~113)  → detail + positions + transfers
3. C — Watch còn lại       (~400)  → performance + detail giới hạn
4. Excluded                (~10.600) → chỉ lưu list record, không deep fetch
```

### 3.1.9. Khi nào một trader bị loại

| Lý do | Field | Ghi chú |
|---|---|---|
| Không giao dịch 7 ngày | `chartItems` | Proxy; có thể bỏ sót trader đang giữ lệnh |
| Quá mới | `startTime` | < 30 ngày |
| Không có lợi nhuận | `roi`, `pnl` | ≤ 0 |
| Lợi nhuận quá thấp | `roi` | Preset có thể đặt min 5–10% |
| Mẫu quá ít | `totalOrder` | < 20/50/100 theo tier |
| Rủi ro quá cao | `mdd` | > 40% |
| WinRate thấp | `winRate` | < 40% |
| Không còn slot | `currentCopyCount/maxCopyCount` | Full |
| AUM quá nhỏ | `aum` | < 5.000 |
| Không active | `status` | Sau detail |
| Dữ liệu cũ | `data_freshness` | > 150 phút |

> Trader bị loại vẫn được lưu **list record** để audit và có thể xuất hiện lại ở chu kỳ sau. Không xóa.

---

## 4. Endpoint 1 — Danh sách trader

### Request

```http
POST {BASE_F}/home-page/query-list
```

```json
{
  "pageNumber": 1,
  "pageSize": 30,
  "timeRange": "90D",
  "dataType": "ROI",
  "favoriteOnly": false,
  "hideFull": false,
  "nickname": "",
  "order": "DESC",
  "userAsset": 0,
  "portfolioType": "PUBLIC"
}
```

> Ví dụ trên dùng `PUBLIC`. Collector chạy thêm `SIGNAL`.  
> Không dùng `ALL` mặc định vì sẽ kéo theo 1.874 PRIVATE không mở copy công khai.

### `portfolioType`

| Giá trị | Ý nghĩa | Số lượng (06/11/2026) |
|---|---|---:|
| `PUBLIC` | Copy portfolio công khai | **8.976** |
| `SIGNAL` | Trading signal provider | **2.154** |
| `PRIVATE` | Portfolio riêng tư | **1.874** |
| `ALL` | Tất cả | **13.004** |

> Trader `5296057151807357697` là **SIGNAL**, không nằm trong list PUBLIC.  
> Universe mặc định của dự án là **PUBLIC + SIGNAL = 11.130**.  
> `PRIVATE` (1.874) không quét mặc định vì không mở copy công khai.

### `hideFull`

`hideFull: true` có thể dùng để server lọc trader đã đầy slot.  
Chưa kiểm chứng đầy đủ trong Phase 0; **luôn kiểm tra lại** bằng:

```python
current_copy_count < max_copy_count
```

Không phụ thuộc hoàn toàn vào `hideFull`.

### `timeRange`

`7D` | `30D` | `90D` | `180D`

`timeRange` quyết định cửa sổ của `roi`, `pnl`, `mdd`, `winRate`, `copierPnl`, `sharpRatio` và độ dài `chartItems`.

### Response fields (22)

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `leadPortfolioId` | string | ID trader |
| `nickname` | string | Tên hiển thị |
| `avatarUrl` | string | Avatar |
| `currentCopyCount` | int | Số copier hiện tại |
| `maxCopyCount` | int | Slot tối đa |
| `roi` | decimal | ROI theo `timeRange` (%) |
| `pnl` | decimal | PnL theo `timeRange` (USDT) |
| `aum` | decimal | Tổng AUM |
| `copyAum` | decimal | Vốn của copier |
| `mdd` | decimal | Max drawdown (%) |
| `winRate` | decimal | Win rate (%) |
| `copierPnl` | decimal | PnL của copier |
| `apiKeyTag` | string/null | Trader dùng API? |
| `tradFiTag` | string/null | Có giao dịch TradFi? |
| `sharpRatio` | decimal/null | Sharpe ratio |
| `chartItems` | array | Chuỗi ROI theo ngày |
| `badgeName` | string/null | Badge |
| `badgeModifyTime` | int/null | Thời điểm badge |
| `badgeCopierCount` | int/null | Copier tại thời điểm badge |
| `portfolioType` | string | PUBLIC/SIGNAL/PRIVATE |
| `startTime` | int | Thời điểm mở portfolio (ms) |
| `aiSummary` | string/null | AI summary của Binance |

### `chartItems`

```json
[
  { "value": 54.65874945, "dataType": "ROI", "dateTime": 1793750400000 },
  { "value": 6.19121926,  "dataType": "ROI", "dateTime": 1793836800000 }
]
```

- Có **90 điểm** cho `90D`, 180 điểm cho `180D`, v.v.
- Giá trị là **ROI lũy kế từ lúc mở**, không phải daily return.
- Bị **pha loãng bởi nạp/rút**.
- **Không dùng để tính MDD tuyệt đối.**
- Có thể dùng để xem shape, positive days, volatility (sau khi lọc dòng tiền).

### Giới hạn & lỗi

- `pageSize` tối đa **30**. Truyền 100 → server trả 30.
- `total` có thể thay đổi giữa các trang do sort động.
- Phải dedupe theo `leadPortfolioId`.
- Rate limit: mã `11012005`.

---

## 5. Endpoint 2 — Detail

### Request

```http
GET {BASE_F}/lead-portfolio/detail?portfolioId=5296057151807357697
```

### Response: 67 field, 48 non-null / 19 null (trader mẫu)

Các field quan trọng:

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `status` | `ACTIVE` | ACTIVE / CLOSED / PAUSED |
| `nickname` | `请填写昵称` | Tên |
| `nicknameTranslate` | `Please enter your nickname.` | Bản dịch |
| `description` | `包亏` | Mô tả |
| `descTranslate` | `Guaranteed loss` | Bản dịch |
| `aumAmount` | `1185600.66504263` | Tổng AUM |
| `copyAum` | `22234.44092838` | Vốn copier |
| `marginBalance` | `1163366.22411425` | Vốn của lead |
| `copierPnl` | `1005.17878648` | PnL copier |
| `currentCopyCount` | `59` | Copier hiện tại |
| `maxCopyCount` | `200` | Slot tối đa |
| `totalCopyCount` | `97` | Tổng từng copy |
| `closeLeadCount` | `0` | Số lần đóng |
| `favoriteCount` | `104` | Lượt favorite |
| `profitSharingRate` | `10.00` | % chia lợi nhuận |
| `fixedRadioMinCopyUsd` | `100.00` | Min copy fixed ratio |
| `fixedAmountMinCopyUsd` | `10.00` | Min copy fixed amount |
| `startTime` | `1793628005247` | Thời điểm mở |
| `lastTradeTime` | `1793901928516` | Lần trade cuối |
| `positionShow` | `false` | Có hiển thị vị thế? |
| `tag` | `["MEDIUM_LEVERAGE"]` | Nhãn |
| `tagItemVos` | `[...]` | Chi tiết nhãn |
| `futuresType` | `UM` | USD-M Futures |
| `initInvestAsset` | `USDT` | Asset |
| `portfolioType` | `SIGNAL` | Loại portfolio |
| `enableTradingSignal` | `true` | Có bật signal |
| `rebateFee` | `0.00000000` | Rebate |
| `isPaused` | `false` | Tạm dừng |
| `unrealizedProfitShareAmount` | `0` | Profit share chưa thực hiện |

### 19 field null của trader mẫu

```
userId, copyPortfolioId, riskControlMaxCopyCount, finalEffectiveMaxCopyCount,
endTime, closedTime, sharpRatio, lockPeriod, copierLockPeriodTime,
copierUnlockExpiredTime, badgeName, badgeModifyTime, badgeCopierCount,
publicLeadPortfolioId, privateLeadPortfolioId, aiSummary,
cooldownDurationHours, monthlyReopenLimit, monthlyRemaining
```

Phân loại:

| Nhóm | Field | Ghi chú |
|---|---|---|
| Null do ngữ cảnh | `userId`, `copyPortfolioId`, `public/privateLeadPortfolioId` | Chưa login / không copy / loại SIGNAL |
| Null do không áp dụng | `endTime`, `closedTime`, `lockPeriod`, `cooldownDurationHours`, `monthlyReopenLimit`, `monthlyRemaining` | Đang ACTIVE, không lock |
| Null thật sự / đang ẩn | `sharpRatio`, `aiSummary`, `badgeName`, `riskControlMaxCopyCount`, `finalEffectiveMaxCopyCount` | Chưa đủ dữ liệu hoặc không có |

> `positionShow = false` **không chặn** `position-history`. API vẫn trả 8 vị thế đã đóng cho trader này.

---

## 6. Endpoint 3 — Performance

### Request

```http
GET {BASE_P}/lead-portfolio/performance?portfolioId=5296057151807357697&timeRange=90D
```

### Response fields (9)

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `timeRange` | `90D` | Cửa sổ |
| `roi` | `59.23318759` | ROI (%) |
| `pnl` | `583369.67249509` | PnL (USDT) |
| `mdd` | `31.338369` | Max drawdown (%) |
| `copierPnl` | `1005.17878648` | PnL copier |
| `winRate` | `50.0` | Win rate (%) |
| `winOrders` | `5` | Số order thắng |
| `totalOrder` | `10` | Tổng order đóng |
| `sharpRatio` | `null` | Sharpe |

### Giá trị trader mẫu

| Window | ROI | PnL | MDD | WinRate | Win/Total | Sharpe |
|---|---:|---:|---:|---:|---:|---|
| 7D | 59,23% | 583.369,67 | 31,34% | 50,00% | 5/10 | null |
| 30D | 59,23% | 583.369,67 | 31,34% | 50,00% | 5/10 | null |
| 90D | 59,23% | 583.369,67 | 31,34% | 50,00% | 5/10 | null |
| 180D | 59,23% | 583.369,67 | 31,34% | 50,00% | 5/10 | null |

> Cả 4 window giống hệt vì portfolio mới mở **2026-11-02 14:00 UTC**.  
> Đây là lý do bắt buộc phải có `min_runtime_days`.

### Sharpe null

- 34,7% trader PUBLIC 90D có `sharpRatio = null`.
- Nguyên nhân thường gặp: portfolio < 30 ngày, chưa đủ mẫu.
- **Không được chấm điểm 0.** Phải renormalize hoặc giảm confidence.

---

## 7. Endpoint 4 — Position history

### Request

```http
POST {BASE_F}/lead-portfolio/position-history
```

```json
{
  "portfolioId": "5296057151807357697",
  "pageNumber": 1,
  "pageSize": 50
}
```

### Response fields (18)

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `positionId` | `1165716580629422080` | ID vị thế |
| `symbol` | `SAMSUNGUSDT` | Cặp |
| `side` | `Long` | Long/Short |
| `leverage` | `10` | Đòn bẩy |
| `isolated` | `Isolated` | Cross/Isolated |
| `opened` | `1793838300000` | Mở (ms) |
| `closed` | `1793901840000` | Đóng (ms) |
| `avgCost` | `...` | Giá vào TB |
| `avgClosePrice` | `...` | Giá đóng TB |
| `closingPnl` | `-204355.63` | PnL đã trừ phí |
| `maxOpenInterest` | `13653` | Size lớn nhất |
| `closedVolume` | `...` | Khối lượng đóng |
| `roi` | `-0.97822256` | ROI trên margin |
| `status` | `All Closed` | Trạng thái |
| `type` | `...` | Loại |
| `index` | `...` | Index |
| `id` | `...` | ID nội bộ |
| `updateTime` | `...` | Cập nhật |

### Giá trị trader mẫu

| Chỉ số | Giá trị |
|---|---:|
| Số vị thế đóng | 8 |
| Thắng/thua | 5/3 → 62,5% |
| Profit factor | 1,64 |
| Avg win / avg loss | +93.938 / -95.487 |
| Payoff ratio | 0,98 |
| Leverage | max 15x, avg 13,12x |
| Margin mode | 100% Isolated |
| Holding time | avg 26,76h; median 17,02h; max 112,46h |
| Long/Short | 6/2 |
| Best | SNDK +270.852 (+82,9%, 1,8h) |
| Worst | SAMSUNG -204.356 (-97,8%, 10x, 17,7h) |

> **Không có open positions.** `position-history` chỉ trả vị thế đã đóng.

---

## 8. Endpoint 5 — Trade history

### Request

```http
POST {BASE_F}/lead-portfolio/trade-history
```

```json
{
  "portfolioId": "5296057151807357697",
  "pageNumber": 1,
  "pageSize": 200
}
```

### Response fields (14)

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `time` | `1793901928000` | Thời điểm fill |
| `symbol` | `SPCXUSDT` | Cặp |
| `side` | `BUY` | BUY/SELL |
| `price` | `123.18` | Giá |
| `fee` | `0.0` | Phí; có thể **âm** (rebate) |
| `feeAsset` | `USDT` | Asset phí |
| `quantity` | `225761.8404` | Notional |
| `quantityAsset` | `USDT` | Asset notional |
| `realizedProfit` | `0.0` | PnL thực hiện |
| `realizedProfitAsset` | `USDT` | Asset |
| `baseAsset` | `SPCX` | Asset cơ sở |
| `qty` | `1832.78` | Khối lượng |
| `positionSide` | `LONG` | LONG/SHORT |
| `activeBuy` | `false` | Taker/maker flag |

### Giá trị trader mẫu

| Chỉ số | Giá trị |
|---|---:|
| Tổng fill | **5.292** |
| Thời gian | 2026-11-02 14:27 → 2026-11-05 18:05 |
| Fill/ngày | ~1.323 |
| Buy / Sell | 2.506 / 2.786 |
| Notional avg / median / max | 8.724 / 1.166 / 1.435.900 |
| Fees | **-1.797,80** (net rebate) |
| Realized PnL | +190.185,12 |
| Symbol nhiều fill | SPCX 1.593; SNDK 1.426; SAMSUNG 512 |

### Lưu ý phân trang

- `pageSize` tối đa **200**. Truyền 500 → server trả 200.
- Nếu code kiểu `if len(lst) < 500: break` → chỉ lấy 200/5.292.
- Phải so `len(out) >= total`.
- Không có `trade_id`; phải hash để chống trùng.

---

## 9. Endpoint 6 — Transfer history

### Request

```http
POST {BASE_F}/lead-portfolio/transfer-history
```

```json
{
  "portfolioId": "5296057151807357697",
  "pageNumber": 1,
  "pageSize": 50
}
```

### Response fields (6)

| Field | Ví dụ | Ý nghĩa |
|---|---|---|
| `time` | `1793903160000` | Thời điểm |
| `coin` | `USDT` | Asset |
| `amount` | `100027.17` | Số lượng |
| `from` | `Fiat and Spot` | Từ |
| `to` | `Lead Trading Account` | Đến |
| `transType` | `LEAD_DEPOSIT` | Loại |

`transType`: `LEAD_INVEST`, `LEAD_DEPOSIT`, `LEAD_WITHDRAW`.

### Giá trị trader mẫu

| Chỉ số | Giá trị |
|---|---:|
| Số lệnh | 17 |
| Tổng nạp/đầu tư | 1.585.897,80 |
| Tổng rút | 1.010.000,00 |
| Net flow | +575.897,80 |

> Dòng tiền là nguyên nhân chính làm `chartItems` sai MDD. Xem mục 11.

---

## 10. Data Availability Matrix

| Chỉ số | Nguồn | Trạng thái | Ghi chú |
|---|---|---|---|
| ROI 7/30/90/180 | performance | ✅ Published | Dùng trực tiếp |
| PnL | performance | ✅ Published | Tổng, không tách realized/unrealized |
| MDD | performance | ✅ Published | **Không tự tính từ chartItems** |
| Sharpe | performance | ⚠️ Published, 34,7% null | Không chấm 0 |
| WinRate | performance | ✅ Published | Theo order, không theo position |
| WinOrders / TotalOrders | performance | ✅ Published | Dùng để kiểm tra mẫu |
| Copier PnL | performance | ⚠️ 62,7% zero | Zero có thể là không có copier |
| AUM | detail/list | ✅ Published | Không phản ánh chất lượng |
| Copy AUM | detail/list | ⚠️ 60,5% zero | Mới là tiền copier |
| Current Copiers | detail/list | ⚠️ 69,8% zero | 30,2% có copier > 0 |
| Max Copiers | detail/list | ✅ Published | |
| Runtime | startTime | ✅ Derived | Bắt buộc lọc |
| Profit Sharing | detail | ✅ Published | |
| Min Copy | detail | ✅ Published | |
| Margin Balance | detail | ✅ Published | |
| Unrealized Profit Share | detail | ✅ Published | Thường 0 |
| Last Trade Time | detail | ✅ Published | Data freshness |
| Status | detail | ✅ Published | |
| Leverage | position-history | ✅ Derived | Max/avg |
| Margin Mode | position-history | ✅ Derived | Isolated/Cross |
| Holding Time | position-history | ✅ Derived | Avg/median/max |
| Position Win Rate | position-history | ✅ Derived | Khác WinRate Binance |
| Profit Factor | position-history | ✅ Derived | Gross win / gross loss |
| Payoff Ratio | position-history | ✅ Derived | Avg win / avg loss |
| Symbol Concentration | position-history | ✅ Derived | Top symbol share / HHI |
| Fees | trade-history | ✅ Derived | Có thể âm |
| Realized PnL | trade-history | ✅ Derived | Có thể lệch closingPnl |
| DCA / Martingale | trade-history + position | ⚠️ Heuristic | Chỉ ghi “suspected” |
| Fills/day | trade-history | ✅ Derived | |
| Net Flow | transfer-history | ✅ Derived | |
| TWR | transfer + equity | ⚠️ Estimated | Cần equity chính xác |
| Open Positions | — | ❌ Unavailable | Không có endpoint |
| Per-copier | — | ❌ Unavailable | Chỉ aggregate |
| Funding Fee | — | ❌ Unavailable | Cần API funding ngoài |
| Liquidation Price | — | ❌ Unavailable | Cần open positions |
| Copy Fill/Slippage | — | ❌ Unavailable | Cần tài khoản copier |
| Benchmark | Binance klines | ✅ Official | BTC/ETH |
| Correlation | chartItems | ⚠️ Estimated | Sau khi lọc flow |

---

## 11. Bài học dữ liệu bắt buộc

### 11.1. `chartItems` làm MDD sai

Trader mẫu:

```
2026-11-03: 17,68%
2026-11-04: 54,66%
2026-11-05:  6,19%   ← tụt do nạp/rút
2026-11-06: 59,23%
```

| Cách tính | MDD |
|---|---:|
| Từ `chartItems` | **88,67%** |
| Binance công bố | **31,34%** |

Nguyên nhân: 17 lệnh nạp/rút, net +575.897,80 USDT. ROI bị pha loãng.

**Quy tắc:** `mdd` hiển thị = `performance.mdd`. Nếu tự tính, phải dùng equity đã điều chỉnh dòng tiền (TWR), và ghi rõ “estimated”.

### 11.2. WinRate theo order ≠ theo position

Trader mẫu:

| Cách tính | Giá trị |
|---|---:|
| Binance `winRate` | 50,00% (5/10) |
| Position-level | 62,50% (5/8) |

Cả hai đều đúng, nhưng định nghĩa khác nhau. UI phải ghi rõ:

- `WinRate (order)` — nguồn Binance.
- `Position Win Rate` — tính từ position-history.

### 11.3. Null ≠ 0

| Field | Null | Zero | Cách xử lý |
|---|---:|---:|---|
| `sharpRatio` | 34,7% | 0% | Null = thiếu; không chấm 0 |
| `copierPnl` | 0% | 62,7% | Zero = không có copier PnL; không phải lỗi |
| `copyAum` | 0% | 60,5% | Zero = không có vốn copier |
| `currentCopyCount` | 0% | 69,8% | Zero = không có copier |
| `mdd` | 0% | 17,1% | Zero có thể là không drawdown hoặc thiếu dữ liệu |
| `winRate` | 0% | 26,7% | Zero có thể là 0% hoặc chưa có order |
| `aiSummary` | 97,8% | 0% | Gần như không dùng |
| `badgeName` | 99,7% | 0% | Gần như không dùng |

Với `winRate = 0` và `mdd = 0`, phải kiểm tra `totalOrder` từ performance để phân biệt “0% thật” và “không có dữ liệu”.

### 11.4. AUM ≠ chất lượng

Trader mẫu:

- AUM: 1.185.600,67
- Copy AUM: 22.234,44 (1,9%)
- Margin balance: 1.163.366,22 (98,1% là tiền lead)

Nếu chỉ nhìn AUM, trader này trông rất lớn. Nhưng copier chỉ góp 22k. Phải hiển thị **Copy AUM** và **Copiers** bên cạnh AUM.

### 11.5. Lead PnL ≠ Copier PnL

- Lead PnL: 583.369,67
- Copier PnL: 1.005,18

Copier vào muộn, vốn nhỏ, và chỉ có 5/10 order thắng. Đây là ví dụ thực tế cho việc không được đánh đồng hai chỉ số.

---

## 12. Collector: code mẫu đã sửa

### 12.1. Scan toàn bộ list

```python
import httpx, asyncio, json

BASE_F = "https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade"
BASE_P = "https://www.binance.com/bapi/futures/v1/public/future/copy-trade"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "clienttype": "web",
    "lang": "en",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/",
}

async def list_page(client, page: int, time_range: str = "90D", ptype: str = "PUBLIC"):
    # Chạy lần lượt cho ptype = "PUBLIC" và "SIGNAL".
    # Không dùng "ALL" mặc định (kéo theo PRIVATE).
    body = {
        "pageNumber": page,
        "pageSize": 30,
        "timeRange": time_range,
        "dataType": "ROI",
        "favoriteOnly": False,
        "hideFull": False,
        "nickname": "",
        "order": "DESC",
        "userAsset": 0,
        "portfolioType": ptype,
    }
    for attempt in range(6):
        r = await client.post(f"{BASE_F}/home-page/query-list", json=body)
        j = r.json()
        if j.get("code") == "000000":
            return j["data"]["total"], j["data"].get("list") or []
        if j.get("code") == "11012005":
            await asyncio.sleep(2 ** attempt)
            continue
        raise RuntimeError(j)
    raise RuntimeError("rate limited")
```

### 12.2. Pagination đúng cho trade-history

```python
async def all_trades(client, portfolio_id: str):
    out, page, total = [], 1, None
    while True:
        r = await client.post(
            f"{BASE_F}/lead-portfolio/trade-history",
            json={"portfolioId": portfolio_id, "pageNumber": page, "pageSize": 200},
        )
        d = r.json()["data"]
        total = total or d["total"]
        lst = d.get("list") or []
        out.extend(lst)
        if len(out) >= total or not lst:
            break
        page += 1
        await asyncio.sleep(0.5)
    return out
```

### 12.3. Performance đúng base

```python
async def performance(client, portfolio_id: str, time_range: str):
    r = await client.get(
        f"{BASE_P}/lead-portfolio/performance",
        params={"portfolioId": portfolio_id, "timeRange": time_range},
    )
    return r.json()["data"]
```

---

### 12.4. Pre-filter và tier

```python
from datetime import datetime, timezone

def runtime_days(start_time_ms: int) -> float:
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    return (now_ms - start_time_ms) / 86_400_000

def traded_last_7d(item: dict) -> bool:
    values = [p.get("value", 0) for p in (item.get("chartItems") or [])]
    if len(values) < 8:
        return len(set(values)) > 1
    window = values[-8:]
    return max(window) - min(window) > 1e-9

def pass_prefilter(item: dict, min_aum: float = 5_000) -> bool:
    runtime = runtime_days(item.get("startTime") or 0)
    roi = item.get("roi") or 0
    pnl = item.get("pnl") or 0
    win_rate = item.get("winRate") or 0
    mdd = item.get("mdd") or 0
    aum = item.get("aum") or 0
    current = item.get("currentCopyCount") or 0
    maximum = item.get("maxCopyCount") or 0

    return (
        runtime >= 30
        and roi > 0
        and pnl > 0
        and win_rate >= 40
        and mdd <= 40
        and aum >= min_aum
        and maximum > 0
        and current < maximum
        and traded_last_7d(item)
    )
```

### 12.5. Thứ tự deep fetch

```python
# 1. Sort shortlist theo pre_score desc
# 2. Fetch performance cho toàn bộ Watch (~517)
# 3. Lọc totalOrder >= 20
# 4. Fetch detail/positions/transfers cho Qualified (~113) + top Watch
# 5. Fetch full trade-history cho High (~13) + top 30–50 Qualified
```

---

## 13. Checklist trước khi viết Collector

- [ ] Xác nhận lại `performance` dùng `BASE_P`.
- [ ] Xác nhận `pageSize` list = 30, trade = 200.
- [ ] Xác nhận `portfolioType` = ALL / PUBLIC / SIGNAL / PRIVATE.
- [ ] Xác nhận trader mẫu là SIGNAL.
- [ ] Chốt universe = PUBLIC + SIGNAL (11.130), không quét PRIVATE mặc định.
- [ ] Chốt pre-filter criteria và counts 460 / 57.
- [ ] Cài `traded_last_7d` từ `chartItems`.
- [ ] Cài `pre_score` để xếp thứ tự deep fetch.
- [ ] Chỉ gọi performance cho shortlist (~517).
- [ ] Chỉ gọi detail/position/transfer cho B + C nổi bật (~113–313).
- [ ] Chỉ gọi full trade-history cho A + top B (~13–50).
- [ ] Kiểm tra `status=ACTIVE` sau detail.
- [ ] Kiểm tra `currentCopyCount < maxCopyCount` sau detail.
- [ ] Lưu raw JSON trước khi parse.
- [ ] Hash trade/transfer để chống trùng.
- [ ] Lưu `collected_hour` để chống trùng snapshot.
- [ ] Ghi `collection_logs` cho mỗi run.
- [ ] Có backoff cho `11012005`.
- [ ] Có adapter CSV/Demo dự phòng.
- [ ] Không tính MDD từ `chartItems`.
- [ ] Không coi null là 0.
