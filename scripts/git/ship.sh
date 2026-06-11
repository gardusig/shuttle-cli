#!/usr/bin/env bash
# @git-ship — stage all, commit, and push with confirmation
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git ship "$@"
