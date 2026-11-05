#!/bin/sh
set -e

PORT="${PORT:-8000}"

echo "Starting PRISM Production Backend..."
echo "Port: ${PORT}"
echo "Environment: ${ENVIRONMENT:-development}"

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Applying database schema migrations (alembic upgrade head)..."
    python -m alembic upgrade head || {
        echo "WARNING: alembic upgrade head encountered an issue. Proceeding to boot application..."
    }
fi

echo "Launching uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT}"
