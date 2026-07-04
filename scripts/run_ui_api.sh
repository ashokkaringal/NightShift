#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export DB_URL="sqlite:///$(pwd)/nightshift.db"

if lsof -ti :8001 >/dev/null 2>&1; then
  echo "Stopping existing process on port 8001..."
  lsof -ti :8001 | xargs kill -9 2>/dev/null || true
  sleep 1
fi

exec uvicorn api.ui_server:app --reload --host 127.0.0.1 --port 8001
