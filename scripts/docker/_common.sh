#!/usr/bin/env bash
# Shared helpers for scripts/docker wrappers.
set -euo pipefail

DOCKER_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SHUTTLE_ROOT:-$(cd "$DOCKER_SCRIPT_DIR/../.." && pwd)}"

resolve_shuttle() {
  if [[ -n "${SHUTTLE_BIN:-}" ]]; then
    printf '%s\n' "$SHUTTLE_BIN"
    return 0
  fi
  if command -v shuttle >/dev/null 2>&1; then
    printf '%s\n' "shuttle"
    return 0
  fi
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    printf '%s\n' "$ROOT/.venv/bin/python -m shuttle"
    return 0
  fi
  echo "ERROR: shuttle not found. Run ./scripts/bootstrap.sh or ./scripts/install.sh" >&2
  return 1
}

exec_shuttle() {
  local shuttle_cmd
  shuttle_cmd=$(resolve_shuttle)
  # shellcheck disable=SC2086
  exec $shuttle_cmd "$@"
}
