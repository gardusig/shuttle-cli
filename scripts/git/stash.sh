#!/usr/bin/env bash
# @git-stash — cursor-skills/skills/git/stash
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git stash "$@"
