#!/usr/bin/env bash
# @git-commit — cursor-skills/skills/git/commit
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git commit "$@"
