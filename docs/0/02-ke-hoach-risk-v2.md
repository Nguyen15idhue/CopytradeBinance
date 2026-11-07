# 02 — Kế hoạch định nghĩa lại phân loại rủi ro (Risk V2)

> Trạng thái: đã implement backend + migration + test. Frontend labels R12–R19 xong.
> Phạm vi code: `risk_rules.py` R01–R19 + `risk_score` + veto Sharpe; `ranking.py` cấm `low_risk` khi Sharpe âm/null; `trader_detail.py` trả `risk_score/veto`.
> Nguồn: `backend/app/services/risk_rules.py`, `scoring.py`, `quant/metrics.py`, `docs/kehoach/03-bo-chi-so-va-scoring.md §6`.

## 1. Vấn đề đã xác nhận

- Scoring v1 (`scoring.py:20-40`) không có `sharpe` trong 19 components → trader 90 điểm + Sharpe âm vẫn `low_risk` được.
- Risk hiện tại (`risk_rules.py:21-33`) chỉ có R08 `Sharpe null`, không có thang Sharpe âm/thấp.
- Phân bố live 511 trader: `critical 214 / high 164 / medium 55 / low 13 / none 38 / unknown 27` → nhạy MDD/lev nhưng thiếu bù trừ tin cậy.
- Spec cũ có R12–R17 (`03-bo-chi-so-va-scoring.md:429-434`: fee_drag, HHI, DCA/martingale, ROI anomaly, AUM drop, metadata) chưa implement.

## 2. Quyết định đã chốt

- Giữ enum UI `critical/high/medium/low/none/unknown` (`frontend/src/i18n/vi.ts:38-48`).
- Sharpe published 90D là chân lý; `sharpe null → N/A`, không gán 0.
- MDD chỉ dùng published; thiếu dữ liệu → `unknown`, không tạo event sai.
- Mỗi kết luận có `evidence {field,value,threshold,rule,at}`; risk không tự loại trader.
- Thiết kế: **Layer 1 veto + Layer 2 risk_score 0–100**.

## 3. Thiết kế veto (Layer 1)

| Điều kiện | Mức tối thiểu | Cấm |
|---|---|---|
| `sharpe_90d < 0` | `>=high` | cấm `low_risk`, cap score hiển thị `<=54 weak` |
| `sharpe 0–0.5` | `>=medium` | cấm `low_risk` trừ khi `mdd<=15 + lev<=3 + runtime>=180` |
| `sharpe null` | giữ R08 + `unknown` | cấm `low_risk`, cấm `none` |
| `mdd>30 / lev>20 / worst_roi<=-80%` | `critical` | giữ R03/R05/R06 |
| `mdd 20–30 / lev 10–20 / calmar<0 / near_liq>=1` | `>=high` | — |
| `fee_drag>20% / HHI>0.4 / top_share>50% / profit_factor<1 (mẫu>=5) / copy_aum_ratio<5% / copier âm+lead dương` | `>=medium` | — |
| `runtime<30 / orders<20 / freshness>150p / confidence<0.5` | giữ R01/R07/R09 + hard-filter HF01–HF06 | cấm ranking như cũ |

## 4. Điểm rủi ro tổng hợp (Layer 2)

```text
risk_score = 30*MDD + 20*Lev + 15*Sharpe + 15*Concentration + 10*Quality + 10*Copy
```

- Chuẩn hóa ngưỡng cố định, không percentile:
  - MDD: `<=10→0, 15→25, 20→50, 30→80, >40→100`
  - Lev: `<=3→0, 5→30, 10→70, 20→100`
  - Sharpe: `>=1.5→0, 1.0→20, 0.5→50, 0→75, <0→100, null→70 + flag`
  - Concentration (HHI/top_share/worst_roi/fee_drag): 0–100 tương tự
- Missing → loại thành phần + renormalize, cộng `unknown_fields`, hạ confidence.
- Map: `0-20 none, 21-40 low, 41-60 medium, 61-80 high, 81-100 critical`; sau đó áp veto nâng mức.

## 5. Bước triển khai (mỗi task ≤1 ngày)

1. **T1. Chốt spec Sharpe (0.5 ngày).** Ra `docs/kehoach/RISK-V2-SPEC.md §1-2` + 3 ví dụ (âm, 0.3, null).
2. **T2. Chốt ma trận R01–R17 mở rộng (0.5 ngày).** Ra `RISK-V2-SPEC.md §3`: R12 fee_drag, R13 HHI, R14 near_liq/worst_roi, R15 profit_factor, R16 copier divergence, R17 freshness/confidence + evidence mẫu.
3. **T3. Chốt công thức risk_score + map level (1 ngày).** Ra `RISK-V2-SPEC.md §4`: trọng số, hàm norm, tính tay 3 trader (gồm case 90 điểm Sharpe âm → `high`, cap 54).
4. **T4. Chốt tương thích + rollout (0.5 ngày).** Ra `RISK-V2-SPEC.md §5`: giữ enum, thêm `risk_score, veto_reasons[]`, không sửa migration cũ; cập nhật `TASKS.md` + `SESSION.md`.

## 6. Kiểm chứng (gate spec)

- [ ] Trader 90 điểm + Sharpe âm → `>=high`, không vào `low_risk`.
- [ ] Sharpe null → không `none`.
- [ ] MDD null → `unknown`.
- [ ] Fee rebate âm không trigger fee_drag.
- [ ] Mẫu <5 vị thế → `profit_factor=null`, không phạt.
- [ ] `ruff` line-length 100 pass nếu có code; `check_refs.py` 0 lỗi nếu sửa `KE-HOACH-TONG-THE.md`.
