#!/usr/bin/env bash
# @docker-reset — stop all, delete containers, prune images and cache
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle docker reset "$@"
