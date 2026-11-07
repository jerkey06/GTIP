#!/bin/sh
# Arranque para Render (plan gratuito, sin pre-deploy): migra la base y levanta la API.
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
