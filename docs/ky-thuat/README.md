# Tài liệu kỹ thuật CopytradeBinance

> Bộ tài liệu tham chiếu kỹ thuật cho hệ thống phân tích copy trading Binance Futures.
> Áp dụng cho Phase 5, cập nhật 07/11/2026.

## 1. Phạm vi

Tài liệu này giải thích:

- copy trading và giới hạn dữ liệu Binance;
- kiến trúc, luồng dữ liệu, collector;
- phễu sàng lọc và tier;
- bộ chỉ số, scoring, risk, ranking;
- AI report, settings, API, bảo mật, vận hành;
- testing, glossary, FAQ và giới hạn đã biết.

Đây là tài liệu tĩnh. Không gọi API, không dùng dữ liệu live.

## 2. Quy ước

- UI dùng tiếng Việt; mã kỹ thuật giữ tiếng Anh (`high_upper`, `published`, `R02`…).
- Số liệu ví dụ ghi rõ “ví dụ Phase 0”; không dùng làm số live.
- Nguồn tham chiếu ghi ở cuối mỗi mục.
- Không đưa API key, secret, dữ liệu cá nhân vào tài liệu.

## 3. Mục lục

| # | Mục | Nhóm |
|---|---|---|
| 01 | Tổng quan hệ thống | Nền tảng |
| 02 | Copy trading và Binance Futures | Nền tảng |
| 03 | Kiến trúc hệ thống | Nền tảng |
| 04 | Nguồn và hợp đồng dữ liệu | Nền tảng |
| 05 | Phễu sàng lọc và Tier | Phân tích |
| 06 | Bộ chỉ số | Phân tích |
| 07 | Scoring | Phân tích |
| 08 | Risk rules | Phân tích |
| 09 | Ranking | Phân tích |
| 10 | Compare và tương quan | Phân tích |
| 11 | Data Health và Collector | Vận hành |
| 12 | AI Report | Vận hành |
| 13 | Settings và versioning | Vận hành |
| 14 | API và bảo mật | Vận hành |
| 15 | Vận hành, backup, monitoring | Vận hành |
| 16 | Testing và quality gate | Tham chiếu |
| 17 | Glossary | Tham chiếu |
| 18 | FAQ kỹ thuật | Tham chiếu |
| 19 | Known limitations | Tham chiếu |
| 20 | Changelog và nguồn tài liệu | Tham chiếu |

## 4. Nguồn chính

- `docs/kehoach/01-pham-vi-va-kien-truc.md`
- `docs/kehoach/02-data-contract-binance.md`
- `docs/kehoach/03-bo-chi-so-va-scoring.md`
- `docs/kehoach/06-kiem-thu-van-hanh-bao-mat.md`
- `docs/api.md`, `docs/deployment.md`
- `docs/kehoach/PHASE5-REPORT.md`, `SESSION.md`

## 5. Trang web

- Route: `/technical`
- Manifest: `frontend/src/content/technical/manifest.ts`
- Section TSX: `frontend/src/content/technical/sections/`
- Page: `frontend/src/pages/TechnicalDocsPage.tsx`
- Kiểm tra đồng bộ: `python scripts/check_tech_docs.py`

