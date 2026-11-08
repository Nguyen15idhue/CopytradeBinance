---
id: risk
title: "Risk rules"
group: "Phân tích"
order: 8
keywords: "risk, R01, R19, risk_score, veto, severity, evidence, low_risk, risk_level"
---

# Risk rules

## 1. Nguyên tắc

Risk event **không tự loại trader**. Nó tạo cảnh báo, kèm evidence, và tham gia vào
`risk_score`/`risk_level`. Chỉ ranking board `low_risk` mới có điều kiện loại riêng.

## 2. Đầu vào

Từ `_value()` trong `backend/app/services/risk_rules.py`:

- **Published 90D**: MDD, Sharpe, totalOrder, copier PnL / lead PnL.
- **Derived**: max leverage, worst position ROI, Copy AUM ratio, fee drag,
  HHI/top symbol share, near-liquidation count, profit factor + positions count, Calmar.
- **Meta**: runtime_days, freshness_minutes, confidence.value.

## 3. Rules R01–R19

| Mã | Field / điều kiện | Severity |
|---|---|---|
| R01 | runtime_days < 30 | insufficient |
| R02 | MDD > 20% | high |
| R03 | MDD > 30% | critical |
| R04 | max leverage > 10x | high |
| R05 | max leverage > 20x | critical |
| R06 | vị thế đã đóng lỗ ≤ −80% | critical |
| R07 | totalOrder < 20 | low_sample |
| R08 | Sharpe null | confidence_penalty |
| R09 | freshness > 150 phút | medium |
| R10 | Copier PnL âm, lead PnL dương | high |
| R11 | Copy AUM ratio < 5% | medium |
| R12 | fee drag > 20%; fee âm bỏ qua | medium |
| R13 | HHI > 0.4 hoặc top symbol > 50% | medium |
| R14 | số vị thế đã đóng lỗ sâu (−80%, −50%] ≥ 1 | high |
| R15 | profit factor < 1 khi positions ≥ 5 | medium |
| R16 | Calmar < 0 | high |
| R17 | confidence < 0.5 hoặc freshness null | medium |
| R18 | Sharpe < 0 | high |
| R19 | 0 ≤ Sharpe < 0.5 | medium |

## 4. Evidence và unknown

Mỗi event có:

```json
{"field": "mdd_90d", "value": 31.34, "threshold": 30, "rule": "R03"}
```

- Field thiếu dữ liệu → ghi vào `unknown`, không tạo event sai.
- R15 chỉ xét khi `positions >= 5`; mẫu nhỏ → unknown.
- R12 bỏ qua fee âm (rebate).
- R13 dùng HHI hoặc top symbol share; thiếu cả hai → unknown.

## 5. risk_score

```text
risk_score = 30 × norm(MDD)
           + 20 × norm(Leverage)
           + 15 × norm(Sharpe)
           + 15 × norm(Concentration)
           + 10 × norm(Quality)
           + 10 × norm(Copy)
```

### Chuẩn hoá chính

| Thành phần | Mốc |
|---|---|
| MDD | 10→0, 15→25, 20→50, 30→80, 40→100 |
| Leverage | 3→0, 5→30, 10→70, 20→100 |
| Sharpe | ≥1.5→0, ≥1→20, ≥0.5→50, ≥0→75, <0→100, null→70 |
| Concentration | max của HHI/top share/worst ROI/fee drag đã chuẩn hoá |
| Quality | max của runtime/orders/freshness/confidence |
| Copy | max của copy AUM ratio và copier divergence |

Quy tắc:

- Thiếu component → loại khỏi tổng và renormalize trọng số còn lại.
- Nếu thiếu **cả MDD và Leverage** → `risk_score = null`.
- Sharpe null vẫn có điểm nền 70, không bị coi là 0.

## 6. Map level và veto

| risk_score | Level |
|---:|---|
| 0–20 | none |
| 21–40 | low |
| 41–60 | medium |
| 61–80 | high |
| 81–100 | critical |

```text
risk_level = max(event_level, score_level)
```

- `unknown` không kéo tụt event level.
- Nếu `unknown` và score chỉ none/low → giữ `unknown`.
- Nếu score medium/high/critical → có thể nâng level.
- `veto_reasons` giữ các mã: R02, R03, R04, R05, R06, R14, R18, R19.
- R19 là medium nhưng vẫn là veto của Sharpe thấp.

## 7. Low-risk eligibility

`eligible_for_low_risk()` và `ranking.py` chặn board `low_risk`:

- Sharpe null → cấm.
- Sharpe âm → cấm.
- Sharpe 0–0.5 chỉ được qua khi:
  - MDD ≤ 15%
  - max leverage ≤ 3x
  - runtime ≥ 180 ngày
- Board còn yêu cầu:
  - runtime ≥ 90 ngày
  - MDD ≤ 20%
  - max leverage ≤ 5x (hoặc null)
  - confidence ≥ 0.8
  - Sharpe ≥ 0

Ví dụ: score 90 + Sharpe âm → R18 (high), `low_risk_eligible = false`,
không vào board Low Risk.

## 8. Lưu trữ và API

- `trader_metrics.risk_level`
- `trader_metrics.risk_score`
- `trader_metrics.risk_veto` (JSONB, chứa `reasons`)
- Migration `0014_risk_v2`.
- `GET /traders/{id}/risk` trả `risk_level`, `risk_score`, `veto_reasons`, `events`.

## 9. Nguồn

`backend/app/services/risk_rules.py`, `backend/app/services/risk_service.py`,
`backend/app/services/ranking.py`, `backend/migrations/versions/0014_risk_v2.py`,
`docs/kehoach/RISK-V2-SPEC.md`.
