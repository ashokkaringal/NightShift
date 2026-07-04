#!/usr/bin/env bash
# Fresh dev DB + overnight run. Run from repo root with venv active.
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export DB_URL="sqlite:///$(pwd)/nightshift.db"
rm -f nightshift.db
python db/init_db.py
python main.py run-overnight
echo "Done. Start UI API: bash scripts/run_ui_api.sh"
