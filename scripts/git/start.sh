#!/usr/bin/env bash
# @git-start — align main and start feature branch (--no-prep to branch in place)
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git start "$@"
