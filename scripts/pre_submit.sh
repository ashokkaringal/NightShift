#!/usr/bin/env bash
set -euo pipefail

echo "== NightShift pre-submit checks =="
python main.py --dry-run
pytest -q
echo "OK"
