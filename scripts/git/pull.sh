#!/usr/bin/env bash
# @git-pull — cursor-skills/skills/git/pull
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git pull "$@"
