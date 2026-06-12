#!/usr/bin/env bash
# Local integration: Docker container smoke + optional live docker CLI on host.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is required for integration tests" >&2
  exit 127
fi

./scripts/test-in-docker.sh

./scripts/bootstrap.sh
source .venv/bin/activate
python scripts/integration/check_docker_commands.py --live

echo "All integration checks passed."
