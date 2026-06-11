#!/usr/bin/env bash
# @git-zip — archive a git tag to zip
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
exec_shuttle git zip "$@"
