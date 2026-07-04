#!/usr/bin/env bash
# Scan tracked files for accidental API key commits (Member D — D13).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PATTERN='AIza[0-9A-Za-z_-]{20,}|sk-[a-zA-Z0-9]{20,}|ghp_[0-9A-Za-z]{20,}'

matches=()
while IFS= read -r file; do
  [[ "$file" == ".env.example" ]] && continue
  [[ "$file" == *"test_member_d.py" ]] && continue
  if grep -qE "$PATTERN" "$file" 2>/dev/null; then
    matches+=("$file")
  fi
done < <(git ls-files 2>/dev/null || find . -type f \( -name '*.py' -o -name '*.md' -o -name '*.json' -o -name '*.ts' -o -name '*.tsx' \) ! -path './.venv/*' ! -path './ui/*/node_modules/*')

if ((${#matches[@]} > 0)); then
  echo "FAIL: possible API keys in tracked files:"
  printf '  %s\n' "${matches[@]}"
  exit 1
fi

echo "PASS: no API key patterns in tracked files"
