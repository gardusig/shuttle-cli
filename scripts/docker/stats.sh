#!/usr/bin/env bash
# @docker-stats — top consumers by cpu, memory, or storage
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle docker stats "$@"
