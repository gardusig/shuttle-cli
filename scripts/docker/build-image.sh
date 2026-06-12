#!/usr/bin/env bash
# Build the shuttle-cli dev/test base image (Python 3.12 + git + editable install).
set -euo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
docker_require
echo "Building $IMAGE from $ROOT"
docker build -t "$IMAGE" "$ROOT"
echo "Built: $IMAGE"
