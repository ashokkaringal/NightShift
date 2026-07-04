#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../ui/nightshift-gmail"
npm run test:e2e
