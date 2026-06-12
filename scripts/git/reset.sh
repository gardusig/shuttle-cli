#!/usr/bin/env bash
# @git-reset — return to synced main; commit dirty branch work; pass --yes
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git reset "$@"
