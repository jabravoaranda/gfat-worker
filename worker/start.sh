#!/bin/bash

python -m celery -A app worker -B -l info &
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000