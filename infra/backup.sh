#!/usr/bin/env bash
# Backup DB + .env, giữ 7 ngày. Chạy tại root repo.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . <(tr -d '\r' < .env)
  set +a
fi

USER_NAME="${POSTGRES_USER:-copytrade}"
DB_NAME="${POSTGRES_DB:-copytrade}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p backups

docker compose exec -T db pg_dump -Fc -U "$USER_NAME" -d "$DB_NAME" > "backups/db-${STAMP}.dump"
if [ -f .env ]; then
  cp .env "backups/env-${STAMP}.bak"
  chmod 600 "backups/env-${STAMP}.bak"
fi

find backups -name 'db-*.dump' -mtime +7 -delete
find backups -name 'env-*.bak' -mtime +7 -delete

echo "Backup xong: backups/db-${STAMP}.dump"
