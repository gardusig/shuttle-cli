#!/usr/bin/env bash
# Local unit tests (same gate as CI macOS job).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
./scripts/bootstrap.sh
source .venv/bin/activate
pytest -q -m "not integration" \
  --cov=shuttle \
  --cov-config=coverage-unit.ini \
  --cov-report=term-missing \
  --cov-fail-under=80
