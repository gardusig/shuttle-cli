#!/usr/bin/env bash
# @git-post-merge-cleanup — cursor-skills/skills/git/post/merge/cleanup
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git post-merge-cleanup "$@"
