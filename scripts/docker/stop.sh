#!/usr/bin/env bash
# @docker-stop — stop running containers
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle docker stop "$@"
