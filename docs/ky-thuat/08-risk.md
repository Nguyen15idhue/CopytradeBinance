---
id: risk
title: "Risk rules"
group: "Phân tích"
order: 8
keywords: "risk, R01, R11, severity, evidence, risk level, cảnh báo"
---

# Risk rules

## 1. Nguyên tắc

Risk event **không tự loại trader**. Nó chỉ tạo cảnh báo, kèm evidence, và ảnh hưởng confidence.

## 2. R01–R11

| Mã | Điều kiện | Severity |
|---|---|---|
| R01 | Runtime < 30 ngày | insufficient |
| R02 | MDD > 20% | high |
| R03 | MDD > 30% | critical |
| R04 | Max leverage > 10x | high |
| R05 | Max leverage > 20x | critical |
| R06 | Position ROI ≤ −80% | critical |
| R07 | totalOrder < 20 | low_sample |
| R08 | Sharpe null | confidence_penalty |
| R09 | Dữ liệu cũ > 150 phút | medium |
| R10 | Copier PnL âm, lead dương | high |
| R11 | Copy AUM < 5% AUM | medium |

## 3. Severity và risk level

- critical → Nghiêm trọng
- high → Cao
- medium → Trung bình
- low_sample → Mẫu nhỏ
- confidence_penalty → Trừ điểm tin cậy
- insufficient → Chưa đủ dữ liệu
- none → Không có
- unknown → Chưa rõ

## 4. Evidence

Mỗi event có:

```json
{"field": "mdd_90d", "value": 31.34, "threshold": 30, "rule": "R03"}
```

Evidence giúp kiểm tra vì sao cảnh báo được tạo.

## 5. Cách đọc

- Risk Monitor hiển thị event, severity, trader, evidence.
- Detail hiển thị cảnh báo rủi ro của trader.
- Không dùng risk event như tín hiệu mua/bán.

## 6. Nguồn

`backend/app/services/risk_rules.py`, `docs/kehoach/03-bo-chi-so-va-scoring.md`.
