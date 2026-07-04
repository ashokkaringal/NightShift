#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== NightShift pre-submit checks =="

echo "-- policy: no auto-send --"
python policy/check_no_send.py

echo "-- security: key scan --"
bash scripts/scan_keys.sh

echo "-- ADK graph dry-run --"
python main.py --dry-run

echo "-- test suite --"
pytest -q

echo "OK: all pre-submit checks passed"
