#!/usr/bin/env bash
# Integration tests in shuttle-cli:dev (mounts host Docker socket for live checks).
set -euo pipefail
# shellcheck source=docker/common.sh
source "$(dirname "$0")/docker/common.sh"

INNER="$(docker_copy_workspace_script)
cd '$CONTAINER_WORK'
$(docker_init_git_workspace "$CONTAINER_WORK" "docker integration snapshot")
./scripts/docker/run-integration.sh"

docker_run_in_workspace "$INNER" 1
