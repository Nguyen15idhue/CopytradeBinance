# RISK V2 SPEC — Định nghĩa lại phân loại rủi ro (đã implement 07/11/2026)

> Nguồn: `backend/app/services/risk_rules.py`, `scoring.py:20-48`, `quant/metrics.py`, `quant/confidence.py`, `docs/kehoach/03-bo-chi-so-va-scoring.md §6`.
> Trạng thái: đã code + migration `0014_risk_v2` + test 20 pass. Nguyên tắc giữ nguyên bên dưới.
> Nguyên tắc: Published > Derived > Estimated; MDD chỉ dùng published; Sharpe null → N/A; thiếu → `unknown`, không bịa số.

## 1. Sharpe trong Risk V2 (T1)

- Dùng `published["90D"]["sharpe"]` (`performance.sharpRatio`), cửa sổ 90D, `rf=0`, ghi rõ trong tooltip.
- `null` → giữ R08, `risk_level` không được `none`, cấm board `low_risk`, trừ `coverage` trong confidence.
- Thang thực tế (Schwab/CME/Morningstar):
  - `<0`: lỗ so với cash, biến động không được bù → rủi ro cao.
  - `0–0.5`: yếu, `0.5–1.0`: trung bình, `1.0–2.0`: tốt, `>2.0`: kiểm tra leverage/overfit, `>3.0`: nghi ngờ.
- Veto Sharpe:
  - `sharpe < 0` → `risk_level >= high`, cấm `low_risk`, cap score hiển thị `<=54`.
  - `0 <= sharpe < 0.5` → `>= medium`, cấm `low_risk` trừ khi `mdd<=15 + lev<=3 + runtime>=180`.
  - `null` → `unknown/low`, cấm `low_risk` và `none`.

## 2. Ma trận R01–R17 (T2)

| Mã | Field | Ngưỡng | Severity | Evidence |
|---|---|---|---|---|
| R01 | `runtime_days` | `<30` | insufficient→low | value, 30 |
| R02 | `mdd_90d` | `>20` | high | value, 20 |
| R03 | `mdd_90d` | `>30` | critical | value, 30 |
| R04 | `max_leverage` | `>10` | high | value, 10 |
| R05 | `max_leverage` | `>20` | critical | value, 20 |
| R06 | `worst_position_roi` | `<=-80%` | critical | value, -80 |
| R07 | `total_orders_90d` | `<20` | low_sample→low | value, 20 |
| R08 | `sharpe_90d` | `null` | confidence_penalty→low | value null |
| R09 | `freshness_minutes` | `>150` | medium | value, 150 |
| R10 | `copier_pnl/pnl` | copier<0<lead | high | {copier_pnl,pnl}, 0 |
| R11 | `copy_aum_ratio` | `<5%` | medium | value, 5 |
| R12 | `fee_drag_pct` | `>20%` | medium | value, 20; fee âm không trigger |
| R13 | `hhi/top_share` | `HHI>0.4` hoặc `top>50%` | medium | value, threshold |
| R14 | `near_liquidation_count` | `>=1` | high | value, 1 |
| R15 | `profit_factor` | `<1` khi `positions>=5` | medium | value, 1; mẫu <5 → unknown |
| R16 | `calmar` | `<0` khi `mdd>0` | high | value, 0 |
| R17 | `confidence` | `<0.5` hoặc `freshness null` | medium | value, 0.5 |

Mỗi event: `{"code","severity","label","evidence":{"field","value","threshold","rule","at"}}`.

## 3. Công thức risk_score + map level (T3)

```text
risk_score = 30*norm_mdd + 20*norm_lev + 15*norm_sharpe
           + 15*norm_conc + 10*norm_qual + 10*norm_copy
```

- `norm_mdd`: `<=10→0, 15→25, 20→50, 30→80, >40→100`, tuyến tính giữa mốc.
- `norm_lev`: `<=3→0, 5→30, 10→70, 20→100`.
- `norm_sharpe`: `>=1.5→0, 1.0→20, 0.5→50, 0→75, <0→100, null→70`.
- `norm_conc`: max của `HHI/top_share/worst_roi/fee_drag` chuẩn hóa 0–100.
- `norm_qual`: từ `runtime/orders/freshness/confidence` (thiếu → 70 + unknown).
- `norm_copy`: từ `copy_aum_ratio/copier divergence` (R10/R11).
- Missing → loại thành phần, renormalize trọng số còn lại, `unknown_fields += 1`.
- Map: `0–20 none, 21–40 low, 41–60 medium, 61–80 high, 81–100 critical`; áp veto Layer 1 để nâng mức sau map.
- `risk_level = max(map(risk_score), veto_level)`; không event + có unknown → `unknown`; đủ dữ liệu + score ≤20 → `none`.

### Ví dụ tính tay

1. Case của bạn: score 90, `sharpe=-0.4, mdd=12, lev=4, runtime=120, confidence=0.85`.
   `norm_sharpe=100, norm_mdd≈15, norm_lev≈15` → `risk_score≈35` → map `low`, nhưng veto Sharpe âm → `high`, cấm `low_risk`, cap score hiển thị `<=54`.
2. Sharpe 0.3, còn lại đẹp: `norm_sharpe≈65` → `risk_score≈45` → `medium`, cấm `low_risk`.
3. Sharpe null, còn lại đẹp: `norm_sharpe=70` + unknown → `medium/unknown`, cấm `low_risk` và `none`.

## 4. Tương thích + rollout (T4)

- Giữ enum `critical/high/medium/low/none/unknown`; frontend `RISK_LEVEL_LABELS` không đổi.
- Thêm trường mới khi implement sau này: `risk_score (0–100)`, `veto_reasons[]`, `unknown_fields`; không sửa migration cũ, chỉ thêm migration mới `0014_risk_v2`.
- Không sửa `KE-HOACH-TONG-THE.md` trong spec này; khi duyệt kiến trúc mới sửa + chạy `scripts/check_refs.py`.
- Test spec (gate):
  - [ ] 90 điểm + Sharpe âm → `>=high`, không `low_risk`.
  - [ ] Sharpe null → không `none`.
  - [ ] MDD null → `unknown`.
  - [ ] Fee rebate âm không trigger R12.
  - [ ] Mẫu <5 → `profit_factor=null`, không trigger R15.
