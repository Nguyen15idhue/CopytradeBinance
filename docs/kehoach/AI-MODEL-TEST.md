# AI MODEL TEST — OpenRouter

> Sinh tự động bởi `scripts/test_ai_models.py`.

## Cấu hình

- Primary: `google/gemma-4-31b-it:free`
- Fallback: `nvidia/nemotron-3.5-super-vl:free`
- Key check: HTTP `200`

## Model primary

### Case `rich_data`
- Kết quả: **FAIL**
- HTTP: `429`
- Lỗi: `{"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own provider key to use your own limits: https://openrouter.ai/workspaces/default/byok","provider_name":"Google AI Studio","i`
- Latency: 6986 ms

### Case `young_portfolio`
- Kết quả: **FAIL**
- HTTP: `429`
- Lỗi: `{"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own provider key to use your own limits: https://openrouter.ai/workspaces/default/byok","provider_name":"Google AI Studio","i`
- Latency: 7013 ms

## Model fallback

### Case `rich_data`
- Kết quả: **PASS**
- Latency: 11901 ms
- Tokens: prompt `349`, completion `2081`
- Điểm chất lượng: **30/30**
- Chi tiết: {'json': 5, 'schema': 5, 'evidence': 5, 'risk': 5, 'uncertainty': 5, 'no_advice': 5}

```json
{
  "summary": "Trader ID 5143921081414022657 đạt ROI 90 ngày 30.3% với mdd_90d 6.52%. Tỷ lệ thắng lệnh là 99.64% trên tổng số 1234 lệnh, Sharpe 3.83 và confidence 0.89. Vị thế tệ nhất có ROI -88.5%, mức rủi ro được đánh giá là high trong thời gian chạy 691 ngày.",
  "strengths": [
    "ROI 90 ngày cao 30.3% (roi_90d)",
    "Tỷ lệ thắng lệnh rất cao 99.64% (win_rate_order)",
    "Sharpe ratio cao 3.83 (sharpe)",
    "Tổng số lệnh lớn 1234 (total_orders)",
    "Confidence cao 0.89 (confidence)"
  ],
  "weaknesses": [
    "Vị thế tệ nhất lỗ sâu -88.5% (worst_position_roi)",
    "Mức rủi ro được đánh giá là high (risk_level)",
    "Đòn bẩy tối đa 10.0 (max_leverage)"
  ],
  "risk_flags": [
    "Vị thế tệ nhất ROI -88.5% cho thấy khả năng thua lớn trên một vị thế (worst_position_roi)",
    "Mức rủi ro high (risk_level)",
    "Đòn bẩy tối đa 10.0 (max_leverage)"
  ],
  "missing_data": [
    "profit_factor",
    "benchmark_return"
  ],
  "evidence_ids": [
    "id",
    "roi_90d",
    "mdd_90d",
    "sharpe",
    "win_rate_order",
    "total_orders",
    "max_leverage",
    "worst_position_roi",
    "profit_factor",
    "runtime_days",
    "confidence",
    "risk_level",
    "benchmark_return"
  ]
}
```

### Case `young_portfolio`
- Kết quả: **PASS**
- Latency: 15074 ms
- Tokens: prompt `345`, completion `2005`
- Điểm chất lượng: **30/30**
- Chi tiết: {'json': 5, 'schema': 5, 'evidence': 5, 'risk': 5, 'uncertainty': 5, 'no_advice': 5}

```json
{
  "summary": "Trader ID 5296057151807357697 có ROI 90 ngày là 61.75% và drawdown 90 ngày là 31.34%. Tài khoản thực hiện tổng cộng 10 lệnh với tỷ lệ thắng 50.0%, hệ số lợi nhuận 1.64 và vị trí kém nhất -97.8%. Thời gian chạy 4.11 ngày, mức rủi ro critical, độ tin cậy 0.31 và tier excluded.",
  "strengths": [
    "ROI 90 ngày dương 61.75% (roi_90d)",
    "Hệ số lợi nhuận 1.64 lớn hơn 1 (profit_factor)",
    "Tỷ lệ thắng lệnh 50.0% (win_rate_order)"
  ],
  "weaknesses": [
    "Vị trí kém nhất -97.8% (worst_position_roi)",
    "Đòn bẩy tối đa 15.0 (max_leverage)",
    "Thời gian chạy ngắn 4.11 ngày (runtime_days)",
    "Độ tin cậy thấp 0.31 (confidence)",
    "Tier bị loại trừ (tier)"
  ],
  "risk_flags": [
    "Mức rủi ro critical (risk_level)",
    "Drawdown 90 ngày 31.34% (mdd_90d)",
    "Vị trí lỗ tối đa -97.8% (worst_position_roi)",
    "Đòn bẩy cao 15.0 (max_leverage)",
    "Độ tin cậy 0.31 (confidence)"
  ],
  "missing_data": [
    "sharpe (null)",
    "benchmark_return (null)"
  ],
  "evidence_ids": [
    "id",
    "roi_90d",
    "mdd_90d",
    "win_rate_order",
    "total_orders",
    "profit_factor",
    "worst_position_roi",
    "runtime_days",
    "risk_level",
    "confidence",
    "tier",
    "max_leverage"
  ]
}
```

## Đề xuất

| Phương án | Ưu | Nhược |
|---|---|---|
| **A. Đổi primary/fallback** | Dùng ngay, cả 2 đều free và đã test JSON | Latency 12–24s/model |
| B. Giữ gemma + nạp credit/BYOK | Giữ model đã chọn | Tốn tiền, chưa kiểm chứng chất lượng |
| C. Chờ free tier gemma hết rate-limit | Không đổi cấu hình | Không ổn định, 429 lặp lại |

Cấu hình đề xuất (phương án A):

```dotenv
AI_MODEL_PRIMARY=nvidia/nemotron-3.5-super-vl:free
AI_MODEL_FALLBACK=nvidia/nemotron-3-ultra-550b-a55b:free
```

Kết quả test model thay thế `nvidia/nemotron-3-ultra-550b-a55b:free`:

| Case | JSON | Điểm | Latency | Tokens |
|---|---|---|---:|---:|
| rich_data | hợp lệ | 29/30 | 24,1s | 1.190 |
| young_portfolio | hợp lệ | 30/30 | 13,5s | 1.154 |

Ghi chú: đây là model reasoning nên `completion_tokens` gồm cả reasoning; cần `max_tokens >= 2000`
khi dùng thật. Chi phí hiện tại = 0 (free tier).

## Kết luận

- Kết nối OpenRouter + API key: **OK** (HTTP 200).
- Model primary hiện tại (`google/gemma-4-31b-it:free`): **không dùng được ổn định** do upstream 429.
- Model fallback hiện tại (`nvidia/nemotron-3.5-super-vl:free`): **chất lượng tốt 30/30**, chậm 12–15s.
- Cần đổi cấu hình hoặc nạp credit trước khi làm Phase 5.
