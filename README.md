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

- Giao diện: http://localhost:8090
- API: http://localhost:8090/api/v1
- Health: http://localhost:8090/api/v1/health/db
- Backend trực tiếp: http://localhost:8010/health

## Cấu trúc

```text
backend/        FastAPI, SQLAlchemy async, Alembic, collector, worker scheduler
frontend/       React + Vite + TypeScript + Tailwind
infra/nginx/    Reverse proxy
docs/kehoach/   Kế hoạch và checklist
phase0/         Bằng chứng spike dữ liệu (không commit data/)
data/raw/       JSONL archive (không commit)
```

## Giao diện sáng / tối

- Nút chuyển ở topbar (và trang đăng nhập): **Sáng / Tối / Hệ thống**.
- Mặc định theo OS, lưu lựa chọn ở `localStorage`.
- Chi tiết token và quy tắc màu: `docs/ui-theme.md`.

## Backup & restore

```bash
# Linux/VPS
bash infra/backup.sh

# Windows
powershell -ExecutionPolicy Bypass -File scripts/backup.ps1
powershell -ExecutionPolicy Bypass -File scripts/backup.ps1 -DryRun
```

Backup gồm `pg_dump -Fc` + `.env`, giữ 7 ngày trong `backups/` (đã gitignore).
Hướng dẫn restore và monitoring: `docs/deployment.md` (`/metrics`, alert rules).

## Collector Phase 2

- `worker` chạy scheduler: scan 60 phút; performance 6h; detail 12h; trades 24h.
- API vận hành: `/api/v1/collector/status`, `run-scan`, `run-deep`, `kill-switch`.
- UI: http://localhost:8090/data-health

## Quant, Scoring & Screener

```bash
# Tính metrics/score/risk/ranking từ dữ liệu đã thu thập
docker compose exec backend python -m app.collector_cli metrics
docker compose exec backend python -m app.collector_cli risk
docker compose exec backend python -m app.collector_cli score
docker compose exec backend python -m app.collector_cli rank

# Audit false negative 50 trader excluded
docker compose exec backend python -m app.collector_cli audit
```

UI: `/screener`, `/traders/:id`, `/compare?ids=a,b`, `/risk`, `/ranking`, `/settings`,
`/data-health`, `/help` (hướng dẫn người mới), `/technical` (tài liệu kỹ thuật).
Trợ lý AI chat (chỉ admin): icon ✦ góc phải dưới mọi trang sau đăng nhập.

## AI Report (Phase 5)

- Cấu hình trong `.env`: `OPENROUTER_API_KEY`, `AI_MODEL_PRIMARY`, `AI_MODEL_FALLBACK`.
- Fallback 1 lần nếu model chính lỗi/JSON invalid; cuối cùng dùng template tất định.
- Budget ngày/tháng + cooldown 24h; API key lưu mã hoá, chỉ trả trạng thái masked.
- Test model: `python scripts/test_ai_models.py`.
- Báo cáo: `docs/kehoach/AI-MODEL-TEST.md`.

## AI Agent chat (Phase 6b, chỉ admin)

- Icon ✦ góc phải dưới mọi trang; viewer không thấy, không gọi API.
- Panel drawer desktop (~440px), full-screen mobile; Esc đóng; Ctrl/Cmd+Enter gửi.
- Stream SSE: tool trace collapsible, citation chips, cảnh báo; session lưu DB.
- API: `POST /agent/chat` (SSE), `GET/PATCH/DELETE /agent/sessions`, `POST /agent/feedback`.

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

Khi BAPI trả `11012005` hoặc HTTP 429, client tự cooldown 30–180s và retry (tối đa 5 lần).
Trade-history chạy 1 trader/lần, nghỉ 0,4s mỗi trang để tránh bị chặn tần suất.

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

Phase 6 sẽ chuyển sang `@playwright/test`; ma trận use case tại `docs/kehoach/E2E-TEST-PLAN.md`.

## Biến môi trường

Sao chép `.env.example` thành `.env` và đổi secret khi triển khai thật.
Không commit `.env`, không dùng mật khẩu mặc định ở production.
