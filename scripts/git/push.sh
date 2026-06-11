#!/usr/bin/env bash
# @git-push — cursor-skills/skills/git/push
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git push "$@"
