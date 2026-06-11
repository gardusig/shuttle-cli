#!/usr/bin/env bash
# @git-cherry-pick — cursor-skills/skills/git/cherry/pick
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git cherry-pick "$@"
