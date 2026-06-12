#!/usr/bin/env bash
# Onboard: interactive shell in a container with a bootstrapped copy of the repo.
set -euo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

docker_ensure_image
docker run --rm -it \
  -v "$ROOT:$CONTAINER_SRC:ro" \
  -e SHUTTLE_DOCKER_INTEGRATION=1 \
  "$IMAGE" \
  bash -c "
    set -euo pipefail
    $(docker_copy_workspace_script)
    cd '$CONTAINER_WORK'
    SHUTTLE_BOOTSTRAP_DEV=1 ./scripts/bootstrap.sh
    echo ''
    echo 'Bootstrapped workspace: $CONTAINER_WORK'
    echo 'Try: python -m shuttle --help'
    echo ''
    exec bash
  "
