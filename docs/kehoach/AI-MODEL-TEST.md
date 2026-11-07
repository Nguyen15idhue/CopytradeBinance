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
- Latency: 7073 ms

### Case `young_portfolio`
- Kết quả: **FAIL**
- HTTP: `429`
- Lỗi: `{"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own provider key to use your own limits: https://openrouter.ai/workspaces/default/byok","provider_name":"Google AI Studio","i`
- Latency: 6977 ms

## Model fallback

### Case `rich_data`
- Kết quả: **PASS**
- Latency: 15670 ms
- Tokens: prompt `349`, completion `2124`
- Điểm chất lượng: **30/30**
- Chi tiết: {'json': 5, 'schema': 5, 'evidence': 5, 'risk': 5, 'uncertainty': 5, 'no_advice': 5}

```json
{
  "summary": "Trader ID 5143921081414022657 đạt ROI 90 ngày 30.3% và MDD 90 ngày 6.52%. Tỷ lệ thắng lệnh 99.64% trên tổng 1234 lệnh, Sharpe 3.83 và niềm tin 0.89. Vị trí tệ nhất ROI -88.5%, đòn bẩy tối đa 10.0, mức rủi ro cao.",
  "strengths": [
    "ROI 90 ngày 30.3% (roi_90d)",
    "Tỷ lệ thắng lệnh 99.64% với 1234 lệnh (win_rate_order, total_orders)",
    "Sharpe ratio 3.83 (sharpe)",
    "Thời gian chạy 691 ngày (runtime_days)",
    "Niềm tin 0.89 (confidence)"
  ],
  "weaknesses": [
    "Vị trí tệ nhất ROI -88.5% (worst_position_roi)",
    "Mức rủi ro được đánh giá là cao (risk_level)",
    "Đòn bẩy tối đa 10.0 (max_leverage)"
  ],
  "risk_flags": [
    "Mức rủi ro cao (risk_level)",
    "Vị trí lỗ lớn nhất -88.5% (worst_position_roi)",
    "Đòn bẩy tối đa 10.0 (max_leverage)",
    "MDD 90 ngày 6.52% (mdd_90d)"
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
- Latency: 11423 ms
- Tokens: prompt `345`, completion `2116`
- Điểm chất lượng: **30/30**
- Chi tiết: {'json': 5, 'schema': 5, 'evidence': 5, 'risk': 5, 'uncertainty': 5, 'no_advice': 5}

```json
{
  "summary": "Trader ID 5296057151807357697 có ROI 90 ngày 61.75% và MDD 90 ngày 31.34%. Tổng số lệnh là 10, tỷ lệ thắng 50.0%, hệ số lợi nhuận 1.64, thời gian chạy 4.11 ngày. Mức rủi ro được đánh giá critical, đòn bẩy tối đa 15.0, vị trí kém nhất -97.8%, độ tin cậy 0.31.",
  "strengths": [
    "ROI 90 ngày đạt 61.75% (roi_90d)",
    "Hệ số lợi nhuận 1.64 lớn hơn 1 (profit_factor)"
  ],
  "weaknesses": [
    "Thời gian chạy ngắn chỉ 4.11 ngày (runtime_days)",
    "Tổng số lệnh chỉ 10 lệnh, mẫu dữ liệu nhỏ (total_orders)",
    "Độ tin cậy thấp 0.31 (confidence)",
    "Vị trí kém nhất -97.8% (worst_position_roi)"
  ],
  "risk_flags": [
    "Mức rủi ro critical (risk_level)",
    "MDD 90 ngày 31.34% (mdd_90d)",
    "Đòn bẩy tối đa 15.0 (max_leverage)",
    "Vị trí kém nhất -97.8% (worst_position_roi)"
  ],
  "missing_data": [
    "sharpe",
    "benchmark_return"
  ],
  "evidence_ids": [
    "id",
    "roi_90d",
    "mdd_90d",
    "total_orders",
    "win_rate_order",
    "profit_factor",
    "runtime_days",
    "risk_level",
    "max_leverage",
    "worst_position_roi",
    "confidence"
  ]
}
```
