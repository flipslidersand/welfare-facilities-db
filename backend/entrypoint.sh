#!/bin/bash
set -e

echo "Running database migrations..."
cd /app && alembic upgrade head

echo "Initializing API keys..."
cd /app && python scripts/init_api_keys.py

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
