---
id: van-hanh
title: "Vận hành, backup, monitoring"
group: "Vận hành"
order: 15
keywords: "deploy, docker, port, backup, restore, metrics, monitoring, alert, sự cố"
---

# Vận hành, backup, monitoring

## 1. Dịch vụ Docker

| Service | Vai trò |
|---|---|
| db | PostgreSQL 16 |
| redis | Redis 7 |
| backend | FastAPI :8010 |
| worker | Scheduler/collector |
| frontend | React/Vite |
| nginx | Reverse proxy :8090 |

## 2. Port

- Web: `8090`
- Backend: `8010`
- DB/Redis: nội bộ Docker

## 3. Backup

- `pg_dump -Fc` + `.env`.
- Giữ 7 ngày trong `backups/`.
- Không commit backup.
- Có script Linux và Windows.

## 4. Restore

- Tạo DB tạm.
- Restore dump.
- Kiểm tra alembic version, số trader.
- Không restore đè DB thật khi chưa xác nhận.

## 5. Monitoring

- `/metrics` Prometheus.
- Alert rules trong `infra/prometheus-alerts.yml`.
- Theo dõi collector stale, lỗi API, job fail, DB size.

## 6. Sự cố thường gặp

- Nginx cache DNS sau khi recreate backend → restart nginx.
- Collector bị lock → kiểm tra Redis.
- Dữ liệu cũ → xem Data Health.
- AI 429/JSON lỗi → fallback/template.

## 7. Nguồn

`docs/deployment.md`, `infra/backup.sh`, `scripts/backup.ps1`, `SESSION.md`.
