#!/usr/bin/env bash
# @git-branch-delete — cursor-skills/skills/git/branch/delete
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git branch-delete "$@"
