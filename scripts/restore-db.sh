#!/usr/bin/env bash
# Restaura una copia creada con backup-db.sh. SOBRESCRIBE los datos actuales.
# Uso: ./scripts/restore-db.sh backups/gtip-AAAAMMDD-HHMMSS.dump
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "Uso: $0 <archivo.dump>" >&2
  exit 1
fi

DB_USER="${POSTGRES_USER:-gtip}"
DB_NAME="${POSTGRES_DB:-gtip}"

read -r -p "Se reemplazarán los datos de '$DB_NAME'. ¿Continuar? [s/N] " answer
[[ "$answer" =~ ^[sS]$ ]] || { echo "Cancelado."; exit 1; }

# Detener api y worker para que nadie escriba durante la restauración.
docker compose stop api worker 2>/dev/null || true
docker compose exec -T db pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner < "$1"
docker compose start api worker 2>/dev/null || true
echo "Restauración completada desde $1"
