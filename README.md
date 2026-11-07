# CopytradeBinance — Screener & Risk Analytics

Công cụ sàng lọc và phân tích rủi ro **Lead Trader** trên Binance Futures Copy Trading.

> Phase 1 — Foundation + vertical slice. Không auto-trade, không realtime, không Paper Copy.

## Yêu cầu

- Docker Desktop + Docker Compose
- Python 3.12+ (nếu chạy backend ngoài Docker)
- Node 20+ (nếu chạy frontend ngoài Docker)

## Chạy nhanh

```bash
cp .env.example .env
docker compose up -d --build
```

- Giao diện: http://localhost:8080
- API: http://localhost:8080/api/v1
- Health: http://localhost:8080/api/v1/health/db
- Backend trực tiếp: http://localhost:8000/health

## Cấu trúc

```text
backend/        FastAPI, SQLAlchemy async, Alembic, collector, worker scheduler
frontend/       React + Vite + TypeScript + Tailwind
infra/nginx/    Reverse proxy
docs/kehoach/   Kế hoạch và checklist
phase0/         Bằng chứng spike dữ liệu (không commit data/)
data/raw/       JSONL archive (không commit)
```

## Collector Phase 2

- `worker` chạy scheduler: scan 60 phút; performance 6h; detail 12h; trades 24h.
- API vận hành: `/api/v1/collector/status`, `run-scan`, `run-deep`, `kill-switch`.
- UI: http://localhost:8080/data-health

```bash
# Chạy tay từng tầng
docker compose exec backend python -m app.collector_cli scan
docker compose exec backend python -m app.collector_cli recompute
docker compose exec backend python -m app.collector_cli perf
docker compose exec backend python -m app.collector_cli detail
docker compose exec backend python -m app.collector_cli trades

# Xem log worker
docker compose logs -f worker

# Gỡ khóa collector khi process chết giữa chừng (TTL 30 phút)
docker compose exec redis redis-cli DEL lock:collector:scan lock:collector:deep
```

## Lệnh thường dùng

```bash
# Xem log
docker compose logs -f backend

# Migration
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1

# Test backend
pytest backend/tests -q

# Full test (integration dùng PostgreSQL trong compose)
docker compose exec -e RUN_INTEGRATION=1 backend pytest -q

# Build frontend
cd frontend && npm run build

# E2E frontend (cần Chrome/Edge; chạy sau khi compose up)
cd frontend && npm run test:e2e
```

## Biến môi trường

Sao chép `.env.example` thành `.env` và đổi secret khi triển khai thật.
Không commit `.env`, không dùng mật khẩu mặc định ở production.
