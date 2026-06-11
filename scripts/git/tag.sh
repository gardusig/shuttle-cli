#!/usr/bin/env bash
# @git-tag — cursor-skills/skills/git/tag
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git tag "$@"
