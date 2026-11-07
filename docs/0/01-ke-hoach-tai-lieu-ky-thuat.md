# 01 — Kế hoạch trang Tài liệu kỹ thuật

> Trạng thái: đã chốt cấu trúc, bắt đầu triển khai.
> Phạm vi: trang `/technical` + bộ tài liệu nguồn `docs/ky-thuat/`.

## 1. Quyết định đã chốt

- Mỗi mục tài liệu là một file riêng.
- Nội dung docs và nội dung web tách riêng (Cách A).
- `manifest.ts` là nguồn duy nhất cho cấu trúc mục lục.
- Script kiểm tra đảm bảo docs và manifest cùng ID/thứ tự.
- Trang tĩnh, không gọi API, không phụ thuộc dữ liệu live.

## 2. Cấu trúc docs

```text
docs/ky-thuat/
  README.md
  01-tong-quan.md
  02-copy-trading-binance.md
  03-kien-truc.md
  04-du-lieu.md
  05-pheu-va-tier.md
  06-bo-chi-so.md
  07-scoring.md
  08-risk.md
  09-ranking.md
  10-compare.md
  11-data-health-collector.md
  12-ai.md
  13-settings.md
  14-api-bao-mat.md
  15-van-hanh.md
  16-testing.md
  17-glossary.md
  18-faq.md
  19-gioi-han.md
  20-changelog.md
```

## 3. Cấu trúc frontend

```text
frontend/src/content/technical/
  types.ts
  manifest.ts
  index.ts
  sections/01-tong-quan.tsx
  ...
  sections/20-changelog.tsx

frontend/src/pages/TechnicalDocsPage.tsx
frontend/src/components/docs/TechIllustrations.tsx
```

`TechnicalDocsPage` chỉ xử lý mục lục, search, anchor, active section, progress, mobile drawer, print.

## 4. Nhóm mục lục

- Nền tảng: 01–04
- Phân tích: 05–10
- Vận hành: 11–15
- Tham chiếu: 16–20

## 5. Bước triển khai

1. Tạo docs/ky-thuat + 20 file markdown.
2. Tạo types/manifest + 20 section TSX + index.
3. Làm page shell.
4. Thêm SVG kiến trúc/pipeline/scoring.
5. Thêm route `/technical`, menu, link từ Help.
6. Thêm script check docs ↔ manifest.
7. E2E, screenshot, print/PDF, QA.

## 6. Kiểm chứng

- `npm run build` pass.
- E2E: route, TOC ≥ 20, anchor, search, mobile drawer, không undefined/NaN, không lỗi console.
- `scripts/check_tech_docs.py`: đủ 20 ID, không trùng, đúng thứ tự.
- Screenshot light/dark/mobile.
- Print/PDF hiển thị đủ nội dung.

## 7. Kết quả

- Đã tạo 20 file `docs/ky-thuat/*.md` + README.
- Đã tạo 20 section TSX + manifest + index.
- Trang `/technical` hoạt động; TOC 2 cấp, search, group filter, mobile drawer, print.
- `check_tech_docs.py`: 20/20 khớp.
- E2E pass; build pass.

