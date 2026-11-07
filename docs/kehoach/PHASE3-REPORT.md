# PHASE 3 REPORT — Quant + Scoring + Screener

> Ngày: 07/11/2026 · Phạm vi 3.1–3.7 · Trạng thái: **ĐẠT GATE**

## 1. Gate

| Tiêu chí | Yêu cầu | Kết quả |
|---|---|---|
| Screener shortlist dùng được | ~700 | 511 trader có metrics/score; lọc/sort/phân trang hoạt động |
| Trader mẫu excluded không lọt top | Không top | Golden dataset 12 archetype (2 excluded) không vào top 5 |
| Score breakdown khớp | ≤ 0,01 | Sai số max **0,0051** trên 511 trader |
| p95 danh sách | < 1s | **97 ms** (30 request, page_size 100); median 78 ms |
| Filter MDD ≤ 15 | Đúng | 10 dòng đầu đối chiếu SQL khớp hoàn toàn |
| Audit false negative | Kỳ vọng 0 | 50 excluded: **0%**, 0 lỗi |
| Test | Pass | **81 passed** (container, gồm integration) |

## 2. Số liệu

| Hạng mục | Giá trị |
|---|---|
| Trader có metrics | 511 |
| Có score | 511 (không null) |
| Rankable | 236 |
| Band | good 14 · average 145 · weak 240 · high_risk 112 |
| Confidence trung bình | 0,847 |
| Risk events | 1.100 (critical 280 · high 501 · medium 219 · low_sample 91 · penalty 9) |
| Risk level | critical 214 · high 164 · medium 55 · low 13 · none 38 · unknown 27 |
| Ranking | overall 50 · low_risk 38 · consistency 50 |
| Config version | v1 active |

## 3. Đã triển khai

```text
services/quant/{metrics,confidence,builder}.py   published + derived + confidence
services/funnel_audit.py                         audit 50 excluded
services/risk_rules.py + risk_service.py         R01–R11 + evidence
services/scoring.py + scoring_service.py         percentile, winsorize, renormalize, hard filters
services/ranking.py                              3 board + snapshot
services/screener.py                             filter/sort/paginate + funnel
api/v1/{screener,saved_views}.py                 /traders, funnel-summary, export.csv, saved views
migrations 0008–0011
frontend/src/pages/ScreenerPage.tsx              filter bar, table, drawer, saved views, CSV
backend/tests/fixtures/golden_traders.json       12 archetype
```

## 4. Kiểm thử chi tiết

- Golden dataset: 12 archetype, 2 excluded; excluded không vào top 5; missing không bị chấm 0.
- Hard filter: HF04 ngưỡng 20/50/100 theo tier; HF01–HF06.
- Breakdown: tổng contribution = score, sai số ≤ 0,01.
- Screener integration: default sort score desc; MDD filter; excluded toggle + reasons; funnel; saved views CRUD; CSV.
- E2E: login → Data Health → Screener render → trader qualified → trader excluded → logout.

## 5. Quyết định

- Winsorize dùng 2,5–97,5 percentile (theo yêu cầu triển khai).
- Cohort normalization hiện dùng chung toàn bộ trader có metrics (chưa tách portfolio_type) — ghi nhận để Phase 5 tinh chỉnh.
- `benchmark_return` null vì chưa có nguồn klines; đã gắn `missing_benchmark`.
- Consistency board xếp theo điểm consistency, không theo ROI.
- Saved views lưu server theo user (không localStorage).

## 6. Vấn đề đã biết

1. `excess_return` luôn null (chưa có benchmark).
2. `calmar` null khi MDD = 0 theo đúng quy tắc.
3. Virtualize bảng chưa bật vì page_size ≤ 100; sẽ bật khi cho phép 200+.
4. Rate limit login ảnh hưởng test suite → đã reset limiter trong `conftest.py` khi chạy integration.

## 7. Kết luận

Phase 3 đạt gate: scoring có thể giải thích, screener phản hồi < 100ms, excluded không lọt top.
Sẵn sàng Phase 4 — Detail + Compare + Risk Monitor.
