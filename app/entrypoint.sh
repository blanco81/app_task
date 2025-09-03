#!/bin/sh

# Fail on first error
set -e

echo "⏳ Esperando a que la base de datos esté lista..."

until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "✅ Base de datos disponible, aplicando migraciones..."
alembic upgrade head

echo "🚀 Iniciando aplicación FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload --app-dir /app
