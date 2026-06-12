#!/usr/bin/env bash
# @docker-container-delete — remove containers
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle docker container-delete "$@"
