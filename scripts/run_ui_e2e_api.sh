#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export DB_URL="sqlite:///$(pwd)/ui_e2e.db"
python scripts/seed_e2e_ui_db.py
exec uvicorn api.ui_server:app --host 127.0.0.1 --port 8002
