#!/usr/bin/env bash
# @docker-image-delete — prune unused images
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle docker image-delete "$@"
