---
id: testing
title: "Testing và quality gate"
group: "Tham chiếu"
order: 16
keywords: "test, unit, integration, e2e, playwright, golden dataset, gate"
---

# Testing và quality gate

## 1. Unit test

- Công thức ROI, MDD, Sharpe, WinRate, profit factor.
- Normalize/score.
- Confidence.
- Pre-filter/tier.
- AI schema/template.

## 2. Integration test

- Collector → DB.
- Quant → metric.
- Scoring → score/band.
- API contract.
- AI analyze/cached/RBAC/budget.
- Settings preview/rollback/audit.
- Rate limit.

## 3. E2E

Playwright kiểm tra:

- Đăng nhập, theme.
- Settings preview/save/rollback.
- Ranking.
- Help/search/anchor.
- Data Health.
- Screener.
- Compare/risk.
- Trader Detail + AI.
- Technical docs (mới).

## 4. Golden dataset

- 12 trader archetype.
- Trader thật làm regression fixture.
- Không phụ thuộc ID hardcode trong test.

## 5. Gate

- Backend test pass.
- ruff pass.
- Frontend build pass.
- E2E pass.
- check_refs 0 lỗi.
- Không secret, không file rác.

## 6. Nguồn

`docs/kehoach/06-kiem-thu-van-hanh-bao-mat.md`, `frontend/scripts/e2e.mjs`.
