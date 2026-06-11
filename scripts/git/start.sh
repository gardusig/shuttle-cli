#!/usr/bin/env bash
# @git-start — cursor-skills/skills/git/start
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git start "$@"
