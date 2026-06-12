#!/usr/bin/env bash
# Integration gate inside the container workdir (pytest + smoke + live docker).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export SHUTTLE_CONFIG_DIR="$ROOT/config/ci"
SHUTTLE_BOOTSTRAP_DEV=1 ./scripts/bootstrap.sh
source .venv/bin/activate

run_step() {
  echo "==> $1"
  shift
  "$@"
}

run_step "pytest" pytest -q
run_step "integration smoke" ./scripts/integration/smoke.sh
run_step "live docker checks" python scripts/integration/check_docker_commands.py --live
