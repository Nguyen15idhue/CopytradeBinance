---
id: kien-truc
title: "Kiến trúc hệ thống"
group: "Nền tảng"
order: 3
keywords: "kiến trúc, react, fastapi, postgres, redis, worker, nginx, docker, luồng request"
---

# Kiến trúc hệ thống

## 1. Sơ đồ tổng thể

```text
Browser
  ↓
Nginx :8090
  ├── /        → frontend React/Vite
  └── /api/v1  → backend FastAPI :8010
                     ├── PostgreSQL :5432
                     ├── Redis :6379
                     └── OpenRouter (AI)
Worker → Binance BAPI → PostgreSQL + raw archive
```

## 2. Frontend

- React 18, TypeScript strict, Vite, Tailwind.
- TanStack Query cho dữ liệu.
- Theme token trong `docs/ui-theme.md`.
- Các trang: Screener, Detail, Compare, Risk, Ranking, Data Health, Settings, Help, Technical docs.

## 3. Backend

- FastAPI async, Pydantic Settings.
- SQLAlchemy 2 typed model.
- Response wrapper `{data, meta, error}`.
- Auth JWT, RBAC server-side.
- Logic thuần trong `services/`, truy vấn DB tách khỏi công thức.

## 4. PostgreSQL

Các nhóm bảng chính:

- Auth/config: users, scoring_config, app_settings, audit_logs.
- Trader: traders, trader_universe, portfolio_snapshots.
- Lịch sử: performance_metrics, positions, trades, transfers.
- Phân tích: trader_metrics, trader_scores, risk_events, ranking_snapshots.
- AI: ai_reports, ai_usage.

## 5. Redis và worker

- Redis lock cho collector, fallback advisory lock.
- Worker chạy scheduler, đọc collector config mỗi vòng.
- Job scan/deep có trạng thái running/success/skipped/failed.

## 6. Nginx và Docker

- Nginx reverse proxy, CSP/security headers.
- Docker Compose: db, redis, backend, worker, frontend, nginx.
- Port host: web 8090, backend 8010.
- Recreate backend có thể cần restart nginx do cache DNS.

## 7. Luồng request

```text
React → TanStack Query → /api/v1 → FastAPI → service → DB → response
```

## 8. Luồng collector

```text
Scheduler → lock → L0 scan → tier → L2 performance → L3 detail/position/transfer → L4 trades
```

## 9. Nguồn

`docs/kehoach/01-pham-vi-va-kien-truc.md`, `docs/deployment.md`, `docker-compose.yml`.
