#!/usr/bin/env bash
# Copia de seguridad lógica de PostgreSQL con pg_dump (ADD §14.4).
# Uso (desde la raíz del repo, con `docker compose up -d db` en marcha):
#   ./scripts/backup-db.sh                 -> backups/gtip-AAAAMMDD-HHMMSS.dump
#   ./scripts/backup-db.sh mi-copia.dump
set -euo pipefail

DB_USER="${POSTGRES_USER:-gtip}"
DB_NAME="${POSTGRES_DB:-gtip}"
OUT="${1:-backups/gtip-$(date +%Y%m%d-%H%M%S).dump}"

mkdir -p "$(dirname "$OUT")"
# Formato custom (-Fc): comprimido y restaurable con pg_restore.
docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "$OUT"
echo "Copia creada: $OUT ($(du -h "$OUT" | cut -f1))"
