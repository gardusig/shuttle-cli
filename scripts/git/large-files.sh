#!/usr/bin/env bash
# @git-large-files — cursor-skills/skills/git/large/files
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git large-files "$@"
