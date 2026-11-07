---
id: changelog
title: "Changelog và nguồn tài liệu"
group: "Tham chiếu"
order: 20
keywords: "changelog, version, phase 5, prompt v2, việt hóa, nguồn"
---

# Changelog và nguồn tài liệu

## 1. Version tài liệu

| Ngày | Thay đổi |
|---|---|
| 07/11/2026 | Tạo bộ tài liệu kỹ thuật, 20 mục |
| 07/11/2026 | Đồng bộ thuật ngữ tiếng Việt và prompt AI v2 |
| 07/11/2026 | Cập nhật Risk V2: R01–R19, risk_score, veto, Low Risk eligibility |

## 2. Phạm vi

- Áp dụng cho Phase 5.
- Không bao gồm Phase 6 (deploy beta) nếu chưa triển khai.

## 3. Nguồn chính

- `docs/kehoach/01-pham-vi-va-kien-truc.md`
- `docs/kehoach/02-data-contract-binance.md`
- `docs/kehoach/03-bo-chi-so-va-scoring.md`
- `docs/kehoach/06-kiem-thu-van-hanh-bao-mat.md`
- `docs/api.md`
- `docs/deployment.md`
- `docs/kehoach/PHASE5-REPORT.md`
- `SESSION.md`

## 4. Quy ước cập nhật

- Sửa code làm thay đổi hành vi → cập nhật mục liên quan.
- Sửa mục lục → cập nhật `manifest.ts` và `docs/ky-thuat/README.md`.
- Chạy `scripts/check_tech_docs.py` trước commit.
