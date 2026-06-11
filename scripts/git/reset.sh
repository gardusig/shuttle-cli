#!/usr/bin/env bash
# @git-reset — cursor-skills/skills/git/reset
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git reset "$@"
