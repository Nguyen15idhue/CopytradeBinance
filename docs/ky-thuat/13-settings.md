---
id: settings
title: "Settings và versioning"
group: "Vận hành"
order: 13
keywords: "settings, scoring, weights, hard filter, ai, collector, preview, rollback, audit"
---

# Settings và versioning

## 1. Các tab

- Chấm điểm
- Quy tắc rủi ro
- AI
- Thu thập dữ liệu
- Sức khỏe dữ liệu
- Xếp hạng
- Hệ thống

## 2. Scoring

- Đổi trọng số tạo version mới.
- Preview impact hiển thị trader, số đổi band, top thay đổi.
- Score cũ giữ nguyên; version active rebuild.
- Rollback tạo version mới và rebuild.

## 3. Hard filters

- HF01–HF06 thuộc scoring version.
- Không sửa trực tiếp score.
- Có thể xem JSON cấu hình trong tab Quy tắc rủi ro.

## 4. AI

- Model chính/dự phòng.
- Budget ngày/tháng.
- Bật/tắt AI report.
- API key chỉ hiển thị masked.
- Override key lưu mã hoá Fernet.

## 5. Collector

- Scan/performance/detail/trades interval.
- Worker đọc cấu hình mỗi vòng.
- Lưu chu kỳ có audit.

## 6. Audit và RBAC

- Admin mới được sửa.
- Viewer chỉ xem.
- Thay đổi quan trọng ghi audit log.

## 7. Nguồn

`backend/app/services/settings_service.py`, `backend/app/api/v1/settings.py`,
`frontend/src/pages/SettingsPage.tsx`, `docs/api.md`.
