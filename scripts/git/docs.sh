#!/usr/bin/env bash
# @git-docs — cursor-skills/skills/git/docs
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git docs "$@"
