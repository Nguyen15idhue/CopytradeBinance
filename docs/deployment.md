# Deployment & vận hành

## 1. Cổng & dịch vụ

| Dịch vụ | Host | Ghi chú |
|---|---|---|
| Web + API qua Nginx | `8090` | `/api/v1` → backend |
| Backend trực tiếp | `8010` | debug/health |
| PostgreSQL | không expose | chỉ trong network compose |
| Redis | không expose | lock/cache |
| Metrics | `backend:8000/metrics` | scrape nội bộ (không mở internet) |

## 2. Deploy lần đầu

```bash
cp .env.example .env
# sửa secret: POSTGRES_PASSWORD, JWT_SECRET, ADMIN_INITIAL_PASSWORD, APP_ENV=production
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed all
```

Kiểm tra:

```bash
curl -fsS http://localhost:8010/health
curl -fsS http://localhost:8090/api/v1/health/db
docker compose ps
```

## 3. Cập nhật phiên bản

```bash
git pull
docker compose build backend frontend worker
docker compose up -d
docker compose exec backend alembic upgrade head
```

Rollback image: giữ tag image cũ trước khi build, hoặc `git checkout <tag>` rồi build lại.
Luôn chạy `alembic downgrade -1` có kiểm soát nếu migration mới lỗi.

## 4. Backup

```bash
bash infra/backup.sh
# Windows
powershell -ExecutionPolicy Bypass -File scripts/backup.ps1
powershell -ExecutionPolicy Bypass -File scripts/backup.ps1 -DryRun
```

- `pg_dump -Fc` + copy `.env` vào `backups/`; giữ 7 ngày.
- Nên đẩy `backups/` lên storage ngoài máy chủ.

## 5. Restore

```bash
docker compose exec -T db pg_restore -U copytrade -d copytrade --clean --if-exists < backups/db-<stamp>.dump
docker compose restart backend worker
```

Sau restore: kiểm tra `alembic current`, `/health`, số trader, và chạy smoke test.

## 6. Bảo mật

- Nginx thêm CSP, `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`.
- API rate limit 100/phút/user; login 5/phút/IP.
- AI key lưu mã hoá Fernet (derive từ `JWT_SECRET`); API chỉ trả `configured/masked`.
- Không mở PostgreSQL/Redis ra internet; firewall chỉ 22/80/443 (hoặc cổng proxy thực tế).
- Đổi toàn bộ secret mặc định trước khi public.

## 7. Monitoring

- `GET /metrics` (Prometheus text): request count/latency + `collector_last_scan_success_timestamp`.
- Alert gợi ý: scan quá 150 phút, 5xx > 1%, disk > 80%, AI budget vượt.
