#!/usr/bin/env bash
# @git-branch-clear — reset locally, keep main, delete all other branches
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
exec_shuttle git branch-clear "$@"
