#!/bin/bash
set -e

if [ "${CELERY_BEAT_ENABLED:-true}" = "true" ]; then
    python -m celery -A app worker -B -l info &
else
    python -m celery -A app worker -l info &
fi
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
