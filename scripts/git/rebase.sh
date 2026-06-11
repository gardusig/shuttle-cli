#!/usr/bin/env bash
# @git-rebase — cursor-skills/skills/git/rebase
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git rebase "$@"
