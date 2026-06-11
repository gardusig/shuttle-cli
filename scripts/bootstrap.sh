#!/usr/bin/env bash
# macOS dev setup: venv + editable install
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${PYTHON:-}" ]]; then
  for candidate in python3.13 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      ver="$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
      major="${ver%%.*}"
      minor="${ver#*.}"
      if [[ "$major" -ge 3 && "$minor" -ge 12 ]]; then
        PYTHON="$candidate"
        break
      fi
    fi
  done
fi
PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "ERROR: Python 3.12+ not found (set PYTHON=...)" >&2
  exit 1
fi

"$PYTHON" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip
pip install -e ".[dev]"

echo ""
echo "Done. Activate with: source .venv/bin/activate"
echo "Try: python -m shuttle --help"
