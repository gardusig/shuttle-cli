#!/usr/bin/env bash
# @git-main — cursor-skills/skills/git/main
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git main "$@"
