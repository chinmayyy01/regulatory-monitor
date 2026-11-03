#!/bin/sh
set -e

python -m app.db
python -m app.demo.seed --map 0

exec uvicorn api.main:app --host 0.0.0.0 --port 8000
