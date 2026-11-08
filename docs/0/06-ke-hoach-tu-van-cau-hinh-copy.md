# 06 — Kế hoạch: Tư vấn cấu hình copy theo vốn và trader

> Trạng thái: **đã triển khai** (08/11/2026), xem §17 kết quả.
> Phạm vi: agent chat trả lời câu hỏi dạng “Tôi có x USDT, muốn copy trader y thì cấu hình thế nào?”
> bằng một **copy_plan có cấu trúc**, đối chiếu đúng dữ liệu Binance đang có và giới hạn form của Binance.
> Người dùng: admin (theo RBAC của agent hiện tại).
> Liên quan: `backend/app/services/agent/portfolio.py`, `backend/app/services/agent/schema.py`,
> `backend/app/services/agent/orchestrator.py`, `backend/app/services/agent/verifier.py`,
> `backend/app/services/agent/db_tools.py`, `backend/app/models/position.py`,
> `backend/app/models/trade.py`, `backend/migrations/versions/0016_agent_views.py`,
> `frontend/src/components/agent/`, `docs/0/03-ke-hoach-ai-agent.md`.

---

## 1. Vấn đề đã xác nhận (có bằng chứng)

### 1.1 Hiện tại agent chỉ “kiểm tra vốn đủ hay không”, không tạo cấu hình

| Bằng chứng | Chi tiết |
|---|---|
| `backend/app/services/agent/portfolio.py:12-69` | `evaluate_fit()` chỉ trả `can_copy`, `capital_ok`, `min_copy_usd`, `max_loss_at_mdd_usd`, `worst_position_loss_usd`, `missing_fields`, `warnings` |
| `backend/app/services/agent/portfolio.py:97-146` | Tool `analyze_portfolio_fit` chỉ đọc 9 cột từ `agent_trader_copy_constraints`; output không có mode, max, symbol, TP/SL, slippage, margin mode, auto invest |
| `backend/migrations/versions/0016_agent_views.py:54-71` | View chỉ có min copy ratio/amount, profit sharing, slot, AUM; **không có** max copy, symbol, TP/SL, slippage, margin mode |
| `backend/app/services/agent/schema.py:68-87` | `AgentAnswer` chỉ có `answer/facts/citations/assumptions/missing_data/confidence/next_actions`; **không có** `copy_plan` |
| `backend/app/services/agent/orchestrator.py:24-31` | System prompt không có hướng dẫn trả lời cấu hình copy |
| `backend/app/services/agent/orchestrator.py:394-404` | `build_answer_contract` không nhận plan; `next_actions` không được populate |
| `backend/app/services/agent/orchestrator.py:424-437` | SSE `done` chỉ trả `answer`, không trả cấu hình |
| `backend/app/services/agent/verifier.py:7-20` | Verifier chỉ chặn lời khuyên, chưa kiểm tra ràng buộc của một cấu hình |
| `backend/app/services/ai/service.py:44-65` | Context của AI report cũng không có copy constraints |

### 1.2 Đối chiếu 18 trường form Binance với output hiện tại

Nội dung form người dùng cung cấp (đã parse):

| # | Trường form | Agent hiện tại | Kết luận |
|---|---|---|---|
| 1 | Loại sao chép: tỉ lệ cố định / số tiền cố định | Trả `modes` chứa min của cả 2, không chọn, không nêu max | Một phần |
| 2 | Số tiền sao chép (tỉ lệ cố định): 10–300.000 USDT | Chỉ có min | Thiếu max |
| 3 | Nút “Tối đa” | Không có | Thiếu |
| 4 | “Khả dụng” (số dư ví copier) | Không có; agent chỉ nhận `capital_usd` | Thiếu |
| 5 | Tùy chọn ký hiệu (99+) | Không có; `symbol` chỉ nằm trong positions/trades, chưa có tool tổng hợp | Thiếu |
| 6 | Theo dõi cặp TradFi | Không có | Thiếu |
| 7 | Xóa ký hiệu thanh khoản thấp | Không có dữ liệu volume thị trường | Thiếu |
| 8 | Tổng cắt lỗ (USDT, “Được đề xuất”) | Có `max_loss_at_mdd_usd` nhưng không phải giá trị đề xuất | Gần đúng |
| 9 | Sao chép vị thế hiện có | Không có | Thiếu |
| 10 | Sao chép giá vào lệnh tốt hơn | Không có | Thiếu |
| 11 | Chế độ ký quỹ (copy lead) | Không có; `positions.isolated` có dữ liệu nhưng chưa dùng | Thiếu |
| 12 | Đòn bẩy (copy lead) | Chỉ có `max_leverage` lịch sử của lead | Một phần |
| 13 | Mức trượt giá tối đa | Không có; tài liệu ghi rõ không có dữ liệu slippage | Thiếu |
| 14 | Chốt lời 0–2.000% | Không có | Thiếu |
| 15 | Cắt lỗ 0–95% | Không có | Thiếu |
| 16 | Chi phí tối đa mỗi lệnh 5–95% | Không có | Thiếu |
| 17 | Đóng tất cả vị thế ở giá chốt | Không có | Thiếu |
| 18 | Đầu tư tự động | Không có | Thiếu |

Ngoài form, agent đã có thêm: `profit_sharing_rate`, `fee_drag_pct`, `slot_available`,
`risk {level, score, veto}`, `worst_position_loss_usd`, `as_of`, `can_copy`.

### 1.3 Hệ quả

- Câu “Tôi có 100 USDT copy trader X, cấu hình thế nào?” hiện chỉ nhận được câu trả lời
  “đủ/không đủ vốn”, không có cấu hình để người dùng nhập vào Binance.
- Agent có thể trả lời bằng văn xuôi nhưng **không có nguồn sự thật có cấu trúc**;
  hai lần hỏi cùng dữ liệu có thể ra hai câu khác nhau.
- Các trường có thể suy ra từ dữ liệu (margin mode từ `positions.isolated`, đòn bẩy từ
  `positions.leverage`, symbol từ `positions.symbol`) đang bị bỏ phí.
- Các trường không có dữ liệu (slippage, funding, auto invest) nếu để LLM tự trả lời sẽ bịa.

---

## 2. Mục tiêu và tiêu chí nghiệm thu

### 2.1 Mục tiêu

Khi người dùng hỏi bất kỳ câu nào thuộc dạng:

- “Tôi có 100 USDT, muốn copy trader 5143921081414022657 thì cấu hình thế nào?”
- “Khả dụng của tôi 24.84 USDT, nên đặt tỉ lệ hay số tiền cố định?”
- “Copy trader này với 50 USDT, chốt lời/cắt lỗ bao nhiêu, có nên bật auto invest không?”
- “Với 100 USDT, tổng cắt lỗ bao nhiêu là hợp lý?”

Agent phải:

1. Gọi tool lấy dữ liệu thật (profile + copy constraints + positions/trades).
2. Trả về **một object `copy_plan`** phủ đủ 18 trường form ở mục 1.2.
3. Trường nào tính được → có giá trị + `evidence_id` + `as_of`.
4. Trường nào không có dữ liệu → `null` + `status: "missing"` + lý do, **không đổi thành 0**.
5. Trường nào là lựa chọn của người dùng (optional) → `null` + `status: "user_choice"`,
   chỉ điền khi người dùng nói rõ.
6. Không đưa lời khuyên đầu tư; dùng ngôn ngữ “cấu hình tham chiếu theo chính sách”.
7. Không bịa số, không vượt giới hạn form Binance.

### 2.2 Tiêu chí nghiệm thu (AC)

| # | Tiêu chí | Cách kiểm |
|---|---|---|
| AC1 | Với `capital_usd` + `trader_id`, `copy_plan` có đủ 18 khóa (giá trị hoặc null + lý do) | Unit test schema |
| AC2 | `copy_amount_usd`, `cost_per_order_usd` khớp min của lead và max của Binance | Unit + integration |
| AC3 | Không có giá trị nào vượt max form (300.000 / 50.000 / 2.000% / 95%) | Property test |
| AC4 | `capital < min` cả 2 mode → `can_copy=false`, không sinh cấu hình giả | Unit |
| AC5 | `available_balance < capital` → cảnh báo rõ, `copy_amount` không vượt khả dụng | Unit |
| AC6 | Mọi số không phải hằng số nền tảng/người dùng đều có `evidence_id` | Verifier |
| AC7 | Câu trả lời không khớp `ADVICE_PATTERNS`, có disclaimer | Verifier + eval |
| AC8 | Thiếu dữ liệu → có trong `missing_data`, UI hiện “mặc định Binance” | E2E |
| AC9 | Cùng input → cùng plan (không phụ thuộc LLM) | Gọi tool 2 lần |
| AC10 | Các câu hỏi cũ (top 10, Sharpe, MDD, so sánh) không hồi quy | Regression suite |

---

## 3. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| D1 | Trả `copy_plan` có cấu trúc trong `AgentAnswer`, không chỉ văn xuôi | UI điền được form; test được; hết hallucination số |
| D2 | `copy_plan` do **hàm thuần** tính, LLM chỉ diễn giải | Tất định, audit được, không phụ thuộc model |
| D3 | `null` + `status` cho mọi trường thiếu; không dùng 0 thay thế | Đúng nguyên tắc dữ liệu của dự án |
| D4 | Giới hạn form Binance là **hằng số phiên bản** (`COPY_LIMITS_VERSION`) | Binance đổi form thì đổi 1 chỗ, có test |
| D5 | “Khả dụng” là input người dùng, không scrape tài khoản | Hệ thống không giữ API key/số dư |
| D6 | Chỉ tự chọn mode khi **đúng một** mode hợp lệ; cả hai hợp lệ → trả cả hai + hỏi lại | Tránh tự ý chọn thay người dùng |
| D7 | Tổng cắt lỗ suy từ MDD/worst position + chính sách, cap ở vốn | Có nguồn, không bịa |
| D8 | Margin mode/đòn bẩy của lead suy từ `positions` (derived), đánh dấu `confidence` | Không có field setting trực tiếp trong snapshot |
| D9 | Slippage/auto invest/TP mặc định = `null` + “dùng mặc định Binance” | Không có dữ liệu, không bịa |
| D10 | “Thanh khoản thấp” chỉ trả khi có nguồn volume 24h; nếu không → `null` + missing | Không đánh tráo “ít giao dịch của lead” thành “thanh khoản thị trường” |
| D11 | Plan lưu JSONB vào `agent_messages.copy_plan` + version | Xem lại lịch sử, test hồi quy |
| D12 | Ngôn ngữ: “cấu hình tham chiếu”, “hợp lệ về mặt kỹ thuật”; cấm “nên copy”, “nên đầu tư” | Tuân thủ không tư vấn đầu tư |

### 3.1 Cần chốt trước khi code

| # | Câu hỏi | Đề xuất mặc định |
|---|---|---|
| Q1 | Chính sách rủi ro mặc định khi người dùng không nêu | `balanced` |
| Q2 | Có tự chọn mode khi cả hai hợp lệ không | Không; trả cả hai + hỏi |
| Q3 | Có thu thập volume 24h để lọc thanh khoản thấp trong MVP không | Không; để `null` + missing, làm ở bước 6.1.8 (optional) |
| Q4 | Có lưu “khả dụng” vào DB không | Không; chỉ lưu trong plan message |
| Q5 | Ngưỡng `max_cost_order_pct` theo policy | safe 5, balanced 10, aggressive 20 (%); user custom được |

---

## 4. Kiến trúc

```text
Người dùng hỏi
  ↓
Agent orchestrator
  ├── get_trader_profile          → metrics, risk, max/avg leverage, margin mode
  ├── get_copy_constraints        → min ratio/amount, slot, profit sharing, AUM
  ├── get_symbol_stats            → symbol distribution từ positions/trades
  └── build_copy_plan             → hàm thuần + policy + platform limits
        ↓
  copy_plan (JSON)  +  answer (văn xuôi)  +  evidence/citation
        ↓
  verifier kiểm tra plan
        ↓
  SSE done { answer, copy_plan, usage }
        ↓
  UI card cấu hình + disclaimer
```

Nguyên tắc: **tool tính, model kể**. Model không được sửa số trong `copy_plan`;
nếu model viết số khác plan, verifier cảnh báo và UI hiển thị plan làm nguồn chính.

---

## 5. Hợp đồng dữ liệu `copy_plan`

### 5.1 Kiểu chung cho mỗi trường

```json
{
  "value": 100.0,
  "unit": "USDT",
  "source": "published|derived|computed|platform|user|default|missing",
  "status": "ok|defaulted|missing|needs_choice|blocked|infeasible|user_choice",
  "min": 10,
  "max": 300000,
  "evidence_id": "5143921081414022657:min_copy_usd",
  "as_of": "2026-11-08T10:00:00+07:00",
  "note": "lý do ngắn"
}
```

- `source=platform` → không cần evidence, dùng `COPY_LIMITS_VERSION`.
- `source=user` → không cần evidence, nhưng phải echo đúng input.
- `source=computed/derived/published` → **bắt buộc** `evidence_id`.
- `status=missing` → `value=null`, phải có `note`.

### 5.2 Schema đầy đủ

```json
{
  "version": 1,
  "trader_id": "5143921081414022657",
  "as_of": "2026-11-08T10:00:00+07:00",
  "inputs": {
    "capital_usd": 100.0,
    "available_usd": 24.84,
    "risk_policy": "balanced",
    "preferred_mode": null
  },
  "copy_mode": {
    "value": "fixed_amount",
    "source": "computed",
    "status": "ok",
    "eligible_modes": ["fixed_amount"],
    "blocked_modes": [
      {"mode": "fixed_ratio", "reason": "min_copy_ratio_usd=100 > copy_amount_usd=24.84"}
    ],
    "note": "chỉ một mode hợp lệ"
  },
  "copy_amount_usd": {
    "value": 24.84,
    "unit": "USDT",
    "source": "computed",
    "status": "ok",
    "min": 10,
    "max": 300000,
    "max_available": 24.84,
    "evidence_id": "5143921081414022657:fixed_amount_min_copy_usd"
  },
  "cost_per_order_usd": {
    "value": 10.0,
    "unit": "USDT",
    "source": "computed",
    "status": "defaulted",
    "min": 10,
    "max": 50000,
    "evidence_id": "5143921081414022657:fixed_amount_min_copy_usd",
    "note": "min lệnh 10 USDT > 10% của 24.84; đã nâng % chi phí tối đa"
  },
  "max_cost_per_order_pct": {
    "value": 41,
    "unit": "%",
    "source": "computed",
    "status": "defaulted",
    "min": 5,
    "max": 95
  },
  "total_stop_loss_usd": {
    "value": 8.69,
    "unit": "USDT",
    "source": "computed",
    "status": "ok",
    "evidence_id": "5143921081414022657:worst_position_roi"
  },
  "symbols": {
    "value": null,
    "source": "missing",
    "status": "missing",
    "mode": "all",
    "tradfi": ["XAUUSDT"],
    "low_liquidity": null,
    "top": [
      {"symbol": "BTCUSDT", "share_pct": 40.0},
      {"symbol": "ETHUSDT", "share_pct": 30.0},
      {"symbol": "XAUUSDT", "share_pct": 10.0}
    ],
    "note": "chưa có volume 24h để xác định thanh khoản thấp"
  },
  "copy_existing_positions": {
    "value": null,
    "source": "default",
    "status": "user_choice"
  },
  "better_entry_price": {
    "value": null,
    "source": "default",
    "status": "user_choice"
  },
  "margin_mode": {
    "value": "copy_lead",
    "lead_mode": "isolated",
    "confidence": 0.8,
    "source": "derived",
    "status": "ok",
    "evidence_id": "5143921081414022657:margin_mode"
  },
  "leverage": {
    "value": "copy_lead",
    "lead_max": 20.0,
    "lead_avg": 8.0,
    "effective": null,
    "source": "derived",
    "status": "ok",
    "evidence_id": "5143921081414022657:max_leverage"
  },
  "max_slippage_pct": {
    "value": null,
    "source": "missing",
    "status": "missing",
    "note": "hệ thống không có dữ liệu slippage; dùng mặc định Binance"
  },
  "take_profit_pct": {
    "value": null,
    "source": "default",
    "status": "user_choice",
    "min": 0,
    "max": 2000
  },
  "stop_loss_pct": {
    "value": 35,
    "unit": "%",
    "source": "computed",
    "status": "ok",
    "min": 0,
    "max": 95,
    "evidence_id": "5143921081414022657:worst_position_roi",
    "note": "bằng mức lỗ lớn nhất đã quan sát"
  },
  "close_all_at_take_profit": {
    "value": null,
    "source": "default",
    "status": "user_choice"
  },
  "auto_invest": {
    "value": null,
    "source": "default",
    "status": "user_choice"
  },
  "can_copy": false,
  "used_capital_usd": 24.84,
  "warnings": [
    "Vốn khai báo 100 USDT lớn hơn khả dụng 24.84 USDT; dùng 24.84 USDT.",
    "Min fixed ratio 100 USDT > số tiền copy 24.84 USDT."
  ],
  "missing_fields": ["symbols.low_liquidity", "max_slippage_pct"],
  "assumptions": [
    "Chính sách balanced: max cost/order 10%, tổng cắt lỗ theo mức lỗ lớn hơn giữa MDD và worst position."
  ]
}
```

---

## 6. Quy tắc tính (hàm thuần)

### 6.1 Chuẩn hoá input

- `capital_usd` bắt buộc, `> 0`; thiếu → hỏi lại, không mặc định.
- `available_usd` optional, `>= 0`; nếu có và `< capital_usd` → cảnh báo + dùng `available_usd`.
- `risk_policy` ∈ `safe | balanced | aggressive | custom`; mặc định `balanced`.
- `preferred_mode` ∈ `fixed_ratio | fixed_amount | null`.
- `symbol_scope` ∈ `all | exclude_low_liquidity | custom`; mặc định `all`.
- TP/SL/max cost/auto invest/copy existing/better entry: chỉ nhận khi người dùng nói rõ.

### 6.2 Hằng số nền tảng

Đặt trong `app/core/config.py` (hoặc bảng `app_settings`), có `COPY_LIMITS_VERSION`:

| Hằng số | Giá trị | Nguồn |
|---|---|---|
| `RATIO_COPY_MIN_USD` | 10 | Form Binance |
| `RATIO_COPY_MAX_USD` | 300.000 | Form Binance |
| `AMOUNT_ORDER_MIN_USD` | 10 | Form Binance |
| `AMOUNT_ORDER_MAX_USD` | 50.000 | Form Binance |
| `AMOUNT_COPY_MIN_USD` | 10 | Form Binance |
| `AMOUNT_COPY_MAX_USD` | 300.000 | Form Binance |
| `TP_MIN_PCT` / `TP_MAX_PCT` | 0 / 2.000 | Form Binance |
| `SL_MIN_PCT` / `SL_MAX_PCT` | 0 / 95 | Form Binance |
| `MAX_COST_ORDER_PCT_MIN` / `MAX` | 5 / 95 | Form Binance |

> Ghi chú: Binance dùng tên raw `fixedRadioMinCopyUsd` (thiếu chữ “t”);
> code giữ đúng tên nguồn, không tự sửa thành `fixedRatio`.

### 6.3 Chọn mode

```text
copy_upper = min(capital_usd, available_usd nếu có,
                 mode_max tương ứng hằng số)
ratio_ok   = r_min != null and copy_upper >= r_min
amount_ok  = a_min != null and copy_upper >= a_min
```

- `preferred_mode` có và hợp lệ → chọn.
- `preferred_mode` có nhưng không hợp lệ → `copy_mode=null`, `status=blocked`,
  liệt kê lý do; **không tự đổi mode**.
- Không có `preferred_mode`:
  - cả hai hợp lệ → `value=null`, `status=needs_choice`, trả `eligible_modes`;
  - đúng một hợp lệ → chọn mode đó;
  - không mode nào → `can_copy=false`, `status=blocked`.

### 6.4 Số tiền copy / “Tối đa” / “Khả dụng”

```text
mode_max   = RATIO_COPY_MAX_USD nếu fixed_ratio, ngược lại AMOUNT_COPY_MAX_USD
copy_upper = min(capital_usd, available_usd nếu có, mode_max)
copy_amount = copy_upper           # đây cũng là giá trị nút “Tối đa”
```

- Nếu `copy_amount < mode_min` → `can_copy=false`.
- `used_capital_usd = copy_amount` (phần vốn thực sự dùng cho trader này).
- Không tự cộng dồn nhiều trader; cảnh báo nếu người dùng có ý định copy nhiều trader
  nhưng chỉ cung cấp một `available_usd`.

### 6.5 Chi phí mỗi lệnh (fixed amount)

```text
pct = user_max_cost_order_pct ?? policy.max_cost_order_pct
pct = clamp(pct, 5, 95)
raw = copy_amount * pct / 100
lower = max(a_min, AMOUNT_ORDER_MIN_USD)
upper = min(AMOUNT_ORDER_MAX_USD, copy_amount)
cost = clamp(raw, lower, upper)
```

- Nếu `lower > upper` → `cost=null`, `status=infeasible`, `can_copy=false`.
- Nếu `cost` bị đẩy lên `lower` vì `raw < lower`:
  - tính lại `effective_pct = ceil(cost / copy_amount * 100)`;
  - ghi đè `max_cost_per_order_pct = max(pct, effective_pct)` nếu ≤ 95;
  - nếu `effective_pct > 95` → `infeasible`, cảnh báo “không thể đạt lệnh tối thiểu”.

Ví dụ: copy 24,84 USDT, policy 10% → raw 2,484 < min 10 → cost 10;
`effective_pct = ceil(10/24,84*100) = 41%` → trả `max_cost_per_order_pct=41`.

### 6.6 Tổng cắt lỗ và SL/TP

Định nghĩa:

```text
mdd_loss    = capital_usd * mdd_90d / 100        (nếu mdd_90d != null)
worst_loss  = capital_usd * abs(worst_position_roi) / 100
              (nếu worst_position_roi < 0)
```

Chính sách (hằng số sản phẩm, ghi rõ trong `assumptions`):

| Policy | `max_cost_order_pct` | `total_stop_loss_usd` |
|---|---|---|
| `safe` | 5 | `min(capital_usd, mdd_loss)` |
| `balanced` | 10 | `min(capital_usd, max(mdd_loss, worst_loss))` |
| `aggressive` | 20 | `min(capital_usd, max(mdd_loss, worst_loss) * 1.25)` |
| `custom` | user | user, validate `0 < value <= capital_usd` |

- `mdd_loss` và `worst_loss` đều null → `total_stop_loss=null`, `status=missing`.
- `stop_loss_pct = clamp(ceil(abs(worst_position_roi)), 0, 95)` nếu có; null nếu không.
- `take_profit_pct = null` mặc định (không có dữ liệu để suy); chỉ nhận input người dùng.
- `close_all_at_take_profit` mặc định `null` (user choice).

> Đây là **cấu hình tham chiếu**, không phải khuyến nghị đầu tư. Câu trả lời phải kèm
> `DISCLAIMER` và không dùng động từ “nên copy/đầu tư”.

### 6.7 Symbol / TradFi / thanh khoản

Nguồn: `positions.symbol`, `positions.max_open_interest`, `trades.symbol`, `trades.quantity`, `trades.price`.

```text
symbol_stats = group by symbol:
  - trade_count
  - notional = sum(price * quantity)
  - share_pct = notional / total_notional * 100
top = 10 symbol theo share_pct
```

- `symbol_scope=all` → `symbols.value=null`, `status=user_choice`, kèm `top` để tham khảo.
- `symbol_scope=custom` → validate từng symbol có trong lịch sử của lead;
  symbol lạ → warning, vẫn echo nhưng đánh dấu `source=user`.
- `tradfi` → nhận diện theo bảng hằng số `TRADFI_SYMBOLS` (XAU, XAG, EUR, GBP, JPY, …);
  đánh dấu `source=computed`, `confidence=estimated` vì Binance không trả cờ TradFi.
- `low_liquidity`:
  - Chưa có volume 24h → `null`, `status=missing`, note “dùng mặc định Binance”.
  - Nếu bước 6.1.8 thêm nguồn volume → mới trả danh sách.
- Tuyệt đối không gọi “symbol ít giao dịch bởi lead” là “thanh khoản thấp”.

### 6.8 Margin mode / đòn bẩy / slippage / auto invest

- **Margin mode**: đọc `positions.isolated` của lead trong 90D:
  - chuẩn hoá `true|ISOLATED` → `isolated`; `false|CROSSED` → `cross`;
  - lấy mode chiếm đa số; `confidence = majority_count / total`;
  - trả `value="copy_lead"` + `lead_mode` + `confidence`;
  - nếu không có position → `null`, `status=missing`.
- **Đòn bẩy**: `value="copy_lead"`, `lead_max`, `lead_avg` từ metrics; `effective=null`
  vì Binance mới là nơi tính đòn bẩy hiệu lực.
- **Slippage**: chỉ nhận input; mặc định `null` + “dùng mặc định Binance”.
- **Auto invest / copy existing / better entry / close all at TP**: `null` + `user_choice`;
  chỉ echo khi người dùng nói rõ.

### 6.9 Bảng xung đột & cách xử lý

| Tình huống | Xử lý |
|---|---|
| `capital > available` | Dùng `available`, warning, `can_copy=false` nếu `< min` |
| `copy_amount > platform max` | Cap ở max, warning |
| `copy_amount < mode min` | `can_copy=false`, không sinh cost/total SL giả |
| `preferred_mode` không hợp lệ | `blocked`, không tự đổi |
| `raw cost < order min` | Nâng cost lên min, tính lại `effective_pct` |
| `effective_pct > 95` | `infeasible`, `can_copy=false` |
| Không có `mdd_90d` và `worst_position_roi` | `total_stop_loss=null`, missing |
| Không có slot | `can_copy=false` + lý do “hết slot” |
| Symbol custom không có trong lịch sử | Warning, vẫn echo `source=user` |

---

## 7. Tool, API và lưu trữ

### 7.1 Tool mới `build_copy_plan`

```json
{
  "name": "build_copy_plan",
  "description": "Tạo cấu hình copy tham chiếu cho trader theo vốn; trả đủ trường form Binance, thiếu dữ liệu thì null + lý do.",
  "parameters": {
    "type": "object",
    "properties": {
      "trader_id": {"type": "string"},
      "capital_usd": {"type": "number"},
      "available_usd": {"type": "number"},
      "risk_policy": {"type": "string", "enum": ["safe", "balanced", "aggressive", "custom"]},
      "preferred_mode": {"type": "string", "enum": ["fixed_ratio", "fixed_amount"]},
      "symbol_scope": {"type": "string", "enum": ["all", "exclude_low_liquidity", "custom"]},
      "symbols": {"type": "array", "items": {"type": "string"}},
      "allow_tradfi": {"type": "boolean"},
      "max_cost_order_pct": {"type": "number"},
      "take_profit_pct": {"type": "number"},
      "stop_loss_pct": {"type": "number"},
      "close_all_at_take_profit": {"type": "boolean"},
      "copy_existing_positions": {"type": "boolean"},
      "better_entry_price": {"type": "boolean"},
      "auto_invest": {"type": "boolean"},
      "max_slippage_pct": {"type": "number"}
    },
    "required": ["trader_id", "capital_usd"]
  }
}
```

Output: `ToolResult(data=copy_plan, meta={source, as_of, row_ids, config_version, limits_version}, evidence=[...])`.

Evidence bắt buộc:

| `evidence_id` | Giá trị |
|---|---|
| `<id>:fixed_ratio_min_copy_usd` | `fixedRadioMinCopyUsd` |
| `<id>:fixed_amount_min_copy_usd` | `fixedAmountMinCopyUsd` |
| `<id>:mdd_90d` | MDD 90D |
| `<id>:worst_position_roi` | worst position ROI |
| `<id>:max_leverage` | max leverage |
| `<id>:avg_leverage` | avg leverage |
| `<id>:margin_mode` | majority `positions.isolated` |
| `<id>:profit_sharing_rate` | profit sharing |
| `<id>:symbol_share_<symbol>` | tỷ trọng symbol |

### 7.2 Hàm thuần

Tách khỏi DB, test không cần Postgres:

```text
backend/app/services/copy_plan/
  __init__.py
  limits.py       # hằng số form Binance + COPY_LIMITS_VERSION
  policy.py       # safe/balanced/aggressive/custom
  planner.py      # build_plan(inputs, constraints, metrics, symbol_stats) -> dict
  validate.py     # validate_plan(plan) -> list[warning]
```

`analyze_portfolio_fit` giữ nguyên; `build_copy_plan` gọi lại `evaluate_fit` nếu cần,
không copy logic.

### 7.3 Schema / SSE / DB

- `AgentAnswer` thêm `copy_plan: dict | None = None`; `to_dict()` trả kèm.
- SSE `done` thêm `copy_plan`.
- Migration `0021_agent_copy_plan`:
  - `ALTER TABLE agent_messages ADD COLUMN copy_plan JSONB`;
  - `ALTER TABLE agent_messages ADD COLUMN copy_plan_version INTEGER`;
  - có `downgrade()`.
- `GET /api/v1/agent/sessions/{id}` trả `copy_plan` trong message.
- Không thêm bảng mới; không lưu số dư ví.

### 7.4 Template fallback

Khi model lỗi, `template_from_evidence` hiện chỉ liệt kê evidence. Bổ sung:
nếu có `copy_plan`, render template cấu hình từ plan (cùng một hàm với UI) để câu trả lời
tất định vẫn đủ ý.

---

## 8. Prompt và routing

### 8.1 System prompt bổ sung

```text
Khi người dùng hỏi "có x USDT copy trader y thì cấu hình thế nào":
1. Gọi get_trader_profile.
2. Gọi build_copy_plan với trader_id, capital_usd và các lựa chọn người dùng đã nêu.
3. Trả lời theo đúng copy_plan; không tự tính lại số, không đổi null thành 0.
4. Nêu rõ: mode, số tiền copy, min/max, tổng cắt lỗ, các mục để mặc định Binance.
5. Không dùng "nên copy", "nên đầu tư"; dùng "cấu hình tham chiếu".
6. Nếu thiếu capital/available/risk_policy, hỏi lại thay vì giả định.
```

### 8.2 Few-shot bắt buộc trong eval

| Câu hỏi | Tool phải gọi | Kết quả phải có |
|---|---|---|
| “100$ copy trader X, cấu hình sao?” | `get_trader_profile` + `build_copy_plan` | `copy_plan`, mode, min/max, total SL |
| “Khả dụng 24.84, đặt tỉ lệ hay số tiền cố định?” | `build_copy_plan` | `eligible_modes`, lý do block |
| “Copy 5$ trader X được không?” | `build_copy_plan` | `can_copy=false`, lý do min |
| “Chốt lời 50%, cắt lỗ 20%” | `build_copy_plan` | echo đúng input, validate biên |
| “Trader X có hợp để copy 100$ không?” | `analyze_portfolio_fit` | giữ nguyên hành vi cũ |

---

## 9. Verifier

Thêm `verify_copy_plan(plan, facts) -> list[str]`:

1. **Đủ khóa**: 18 trường + `can_copy`, `warnings`, `missing_fields`.
2. **Biên**: mọi `value` số phải nằm trong `[min, max]` của chính nó và hằng số nền tảng.
3. **Evidence**: mọi `source` ∈ `computed/derived/published` phải có `evidence_id`
   tồn tại trong `facts`; sai → warning `copy_plan_evidence_missing:<field>`.
4. **Nhất quán**:
   - `can_copy=true` ⇒ `copy_amount >= mode_min` và `slot_available != false`;
   - `copy_amount <= min(capital, available nếu có, max)`;
   - `total_stop_loss <= capital`;
   - `stop_loss_pct`/`take_profit_pct` trong biên.
5. **Không lời khuyên**: chạy `contains_advice(answer)` như hiện tại.
6. **Không bịa mặc định**: trường `source=default` phải có `status=user_choice|defaulted`
   và note nói rõ “mặc định Binance” hoặc lý do.
7. Nếu có warning → giảm `confidence` xuống `low` và thêm vào `missing_data` tương ứng.

Verifier **không tự sửa số**; chỉ cảnh báo. Builder đã chịu trách nhiệm clamp.

---

## 10. Frontend

### 10.1 Card cấu hình trong chat

Component `CopyPlanCard`:

- Header: trader nickname/id, `as_of`, badge `can_copy` (Đủ điều kiện / Không đủ / Chưa đủ dữ liệu).
- Nhóm “Bắt buộc”: mode, số tiền copy, min/max, khả dụng.
- Nhóm “Ký hiệu”: scope, top symbol, TradFi, low liquidity (null → “mặc định Binance”).
- Nhóm “Rủi ro”: tổng cắt lỗ, TP, SL, max cost/order.
- Nhóm “Nâng cao”: 6 toggle copy_lead/user_choice + trạng thái dữ liệu.
- Mỗi trường có chip nguồn: `Dữ liệu Binance`, `Suy ra`, `Bạn nhập`, `Mặc định`, `Thiếu`.
- Footer disclaimer + link “Vì sao?” mở `facts/citations`.
- Nút “Sao chép JSON” (chỉ admin) để đối chiếu, không phải để auto-trade.

### 10.2 Trạng thái

- `needs_choice`: hiện 2 nút chọn mode, gửi lại tin nhắn.
- `blocked`: hiện lý do, không hiện nút.
- `missing`: hiện “Chưa có dữ liệu — dùng mặc định Binance”, không hiện số 0.
- `infeasible`: hiện cảnh báo đỏ, không cho copy.

### 10.3 i18n

Thêm khóa vào `frontend/src/i18n/vi.ts`:
`copyPlan.title`, `copyPlan.mode.fixedRatio`, `copyPlan.mode.fixedAmount`,
`copyPlan.source.published/derived/computed/platform/user/default/missing`,
`copyPlan.status.*`, `copyPlan.disclaimer`.

---

## 11. Test và bằng chứng

### 11.1 Unit (không cần DB)

| File | Case |
|---|---|
| `test_copy_plan_limits.py` | Hằng số đúng; clamp không vượt biên; version |
| `test_copy_plan_mode.py` | Chỉ ratio hợp lệ; chỉ amount hợp lệ; cả hai → needs_choice; không mode nào → blocked; preferred mode bị block |
| `test_copy_plan_amount.py` | capital < available; capital > available; cap max; min; `Tối đa` |
| `test_copy_plan_cost.py` | raw < min → nâng + effective_pct; effective > 95 → infeasible; cost > copy_amount |
| `test_copy_plan_loss.py` | safe/balanced/aggressive; thiếu MDD/worst → null; cap capital; SL clamp 0–95 |
| `test_copy_plan_symbols.py` | share_pct; custom symbol lạ; TradFi; low liquidity null |
| `test_copy_plan_advanced.py` | margin mode majority; thiếu position → null; leverage copy_lead; slippage null |
| `test_copy_plan_validate.py` | thiếu evidence; vượt biên; can_copy sai; null không thành 0 |

### 11.2 Integration (container)

- Trader thật có `fixedRadioMinCopyUsd`/`fixedAmountMinCopyUsd`:
  - gọi `build_copy_plan` với capital 100 → `meta.row_ids`, evidence, `as_of`;
  - đối chiếu `copy_amount` với view `agent_trader_copy_constraints`.
- Trader không có constraints → `error` rõ, không bịa.
- Kiểm tra `positions.isolated` thật → margin mode + confidence.
- Kiểm tra symbol stats khớp `GROUP BY symbol` trong DB.

### 11.3 Agent eval

Thêm 10 case vào `test_agent_eval_analysis.py` (hoặc file mới `test_agent_eval_copy_plan.py`):

1. 100$ + trader → plan đủ 18 khóa.
2. 5$ → `can_copy=false`.
3. 24.84 khả dụng → block ratio, chọn amount.
4. “tỉ lệ cố định” nhưng min 100 > 24.84 → blocked, không tự đổi.
5. “chốt lời 50%, cắt lỗ 20%” → echo đúng.
6. “auto invest bật” → echo true, không bịa dữ liệu.
7. Thiếu capital → hỏi lại, không gọi plan.
8. Trader hết slot → `can_copy=false`.
9. Không có MDD → `total_stop_loss=null`, missing.
10. Câu trả lời không chứa “nên copy/đầu tư”, có disclaimer.

### 11.4 E2E Playwright

- Hỏi trong chat → card hiện đủ nhóm, chip nguồn.
- `missing` hiện “mặc định Binance”, không hiện `0`/`NaN`.
- `needs_choice` → bấm chọn mode → gửi lại → card cập nhật.
- `blocked` → hiện lý do.
- Không console error; mobile 375px không tràn.

### 11.5 Regression

- `test_agent_portfolio.py` giữ nguyên pass.
- Full backend suite + ruff + `npm run build`.
- `python scripts/check_refs.py` 0 lỗi sau khi thêm tài liệu.

---

## 12. Các bước triển khai

| Bước | Nội dung | Ước lượng | Bằng chứng |
|---|---|---|---|
| B6.1.1 | Chốt spec + hằng số `COPY_LIMITS_*` + migration `0021` (`copy_plan`, `copy_plan_version`) | 0,5 ngày | Migration up/down; `test_copy_plan_limits` pass |
| B6.1.2 | Hàm thuần `planner.py` + `policy.py` + `validate.py` + unit test mode/amount/cost | 1 ngày | 20+ unit pass; không cần DB |
| B6.1.3 | Adapter dữ liệu: copy constraints, metrics, margin mode từ `positions.isolated`, symbol stats từ positions/trades | 1 ngày | Integration test với trader thật; số khớp SQL |
| B6.1.4 | Tool `build_copy_plan` + evidence + `meta.as_of` | 1 ngày | `run_tool` trả plan; `test_agent_copy_plan` pass |
| B6.1.5 | Agent routing/prompt + `AgentAnswer.copy_plan` + SSE `done` + lưu DB | 0,5 ngày | Eval 10 case; SSE payload có plan |
| B6.1.6 | Verifier `verify_copy_plan` + confidence + warning | 0,5 ngày | `test_copy_plan_validate` pass; case evidence thiếu bị chặn |
| B6.1.7 | Frontend `CopyPlanCard` + i18n + trạng thái | 1 ngày | `npm run build`; E2E card PASS |
| B6.1.8 | (Optional) Thu thập volume 24h để lọc thanh khoản thấp + bảng TradFi | 1 ngày | Nếu làm: danh sách low liquidity có nguồn; nếu không: giữ null |
| B6.1.9 | QA + docs (`docs/api.md`, `docs/ky-thuat/12-ai.md`) + eval đầy đủ | 0,5–1 ngày | Full suite pass; check_refs 0; báo cáo hash |

Tổng: **6–7,5 ngày** (chưa gồm 6.1.8 optional).

---

## 13. Checklist nghiệm thu

- [ ] `copy_plan` có đủ 18 trường + `can_copy/warnings/missing_fields`.
- [ ] Mode đúng khi chỉ một mode hợp lệ; cả hai → `needs_choice`.
- [ ] `copy_amount` = min(capital, available, max) và ≥ min của mode.
- [ ] `cost_per_order` xử lý đúng xung đột min 10 USDT.
- [ ] `total_stop_loss` theo policy, ≤ capital, null khi thiếu dữ liệu.
- [ ] `stop_loss_pct` clamp 0–95; `take_profit_pct` null nếu người dùng không nhập.
- [ ] `margin_mode` suy từ `positions.isolated` + confidence; thiếu → null.
- [ ] `leverage=copy_lead` kèm `lead_max/lead_avg`; `effective=null`.
- [ ] Symbol top + TradFi; low liquidity null nếu chưa có nguồn.
- [ ] Slippage/auto invest/copy existing/better entry/close all = null + user_choice.
- [ ] Mọi số có evidence hoặc là hằng số/input người dùng.
- [ ] Không có `0`/`NaN` thay cho `null`.
- [ ] Verifier chặn lời khuyên + plan lệch evidence.
- [ ] UI hiện chip nguồn + disclaimer.
- [ ] Regression agent cũ pass; full suite pass; ruff/build/E2E pass.
- [ ] `docs/api.md` + `docs/ky-thuat/12-ai.md` + TASKS cập nhật.

---

## 14. Rủi ro và kiểm soát

| Rủi ro | Mức | Kiểm soát |
|---|---|---|
| Binance đổi giới hạn form | Trung bình | Hằng số có version + `as_of`; test biên; ghi rõ nguồn “form Binance 2026-11” |
| `positions.isolated` không phản ánh setting hiện tại | Trung bình | Ghi `derived`, `confidence`, note; không khẳng định tuyệt đối |
| LLM tự viết số khác plan | Cao | Plan là nguồn chính; verifier so khớp; UI render plan, không render số từ text |
| Người dùng hiểu là lời khuyên đầu tư | Cao | Ngôn ngữ “cấu hình tham chiếu”; disclaimer; verifier chặn “nên copy” |
| Không có volume 24h → không lọc được thanh khoản | Thấp | `null` + missing; không đánh tráo bằng dữ liệu lead |
| Số dư khả dụng không có thật | Trung bình | Bắt buộc user nhập; cảnh báo nếu > available; không lưu |
| Nhiều trader dùng chung số dư | Thấp | Cảnh báo plan chỉ tính 1 trader; không cộng dồn |
| Plan lỗi thời do dữ liệu cũ | Trung bình | `as_of` + freshness warning hiện có; verifier cảnh báo nếu > 150 phút |

---

## 15. Việc không làm

- Không đặt lệnh, không lưu API key, không auto-trade.
- Không lưu số dư ví/“khả dụng” vào DB.
- Không bịa slippage, funding, TP mặc định, lý do vào lệnh của lead.
- Không tính PnL từng copier.
- Không tự chọn mode khi cả hai hợp lệ.
- Không đưa ra câu “nên copy trader này”.
- Không thêm bảng `user_wallets`/`copy_accounts` trong phạm vi này.

---

## 16. Definition of Done

- Code chạy; `build_copy_plan` trả plan đủ trường với trader thật.
- Unit + integration + eval + E2E liên quan pass.
- Không có số bịa; null đúng chỗ; evidence đầy đủ.
- UI card hiển thị đúng trạng thái, có disclaimer.
- `docs/api.md`, `docs/ky-thuat/12-ai.md`, `docs/kehoach/TASKS.md`, `SESSION.md` cập nhật.
- `ruff`, `npm run build`, `check_refs.py` pass.
- Commit theo bước `feat(phase6): 6.1.x ...`; báo cáo 1–3 dòng kèm hash.


---

## 17. Kết quả triển khai (08/11/2026)

| Bước | Kết quả | Commit |
|---|---|---|
| B6.1.1 | `copy_plan/limits.py`, Settings override, migration `0021_agent_copy_plan` | `1af6cdf` |
| B6.1.2 | `policy.py`, `planner.py`, `validate.py`; 18 unit case | `4540626` |
| B6.1.3 | `data.py`: constraints, margin mode đa số, symbol stats, TradFi estimated | `56464c1` |
| B6.1.4 | Tool `build_copy_plan` + evidence + meta | `dbc249d` |
| B6.1.5 | `AgentAnswer.copy_plan`, SSE `done`, lưu DB, session API, fallback template | `131820b` |
| B6.1.6 | `verify_copy_plan` + warning/confidence | `f402127` |
| B6.1.7 | `CopyPlanCard`, types, E2E desktop + mobile 375 | `aaca92a` |
| B6.1.8 | TradFi có; volume 24h không làm theo Q3 (`low_liquidity=null`) | `edbfe08` |
| B6.1.9 | QA + docs + eval | (commit QA) |

Bằng chứng QA cuối:
- Backend: **320 passed** (`RUN_INTEGRATION=1`), ruff pass.
- Frontend: `npm run build` pass; E2E **PASS** 25 checkpoint (gồm “Agent copy plan card”).
- Migration head: `0021_agent_copy_plan`; up/down/up OK.
- Tài liệu: `check_refs` 174/0; `check_tech_docs` 20/20.
- Không có secret/file rác trong commit.

Khác biệt so với kế hoạch:
- `max_cost_per_order_pct` lấy từ policy (safe 5 / balanced 10 / aggressive 20) và có thể
  bị nâng để đạt lệnh tối thiểu 10 USDT; trả `status=defaulted` + note.
- `copy_amount_usd` cap theo `min(capital, available, max)` và cap thêm `copy_amount` khi
  tính tổng cắt lỗ (không vượt phần vốn thực dùng).
- `i18n/vi.ts` không sửa vì đang có thay đổi của người dùng; card dùng chuỗi tiếng Việt
  inline giống phần còn lại của AgentPanel.
