#!/usr/bin/env bash
# @git-review — cursor-skills/skills/git/review
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git review "$@"
