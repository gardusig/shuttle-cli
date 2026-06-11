#!/usr/bin/env bash
# @git-branch — cursor-skills/skills/git/branch
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git branch "$@"
