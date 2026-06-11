#!/usr/bin/env bash
# Build and run shuttle-cli checks inside Docker without mutating the host repo.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${SHUTTLE_DOCKER_IMAGE:-shuttle-cli-integration:local}"
CONTAINER_SRC="/workspace/src"
CONTAINER_WORK="/tmp/shuttle-cli"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not on PATH" >&2
  exit 127
fi

if [[ "${SHUTTLE_DOCKER_SKIP_BUILD:-0}" != "1" ]]; then
  echo "Building image: $IMAGE"
  docker build -t "$IMAGE" "$ROOT"
else
  echo "Using pre-built image: $IMAGE"
  if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "ERROR: SHUTTLE_DOCKER_SKIP_BUILD=1 but image not found: $IMAGE" >&2
    exit 1
  fi
fi

docker run --rm \
  -v "$ROOT:$CONTAINER_SRC:ro" \
  -e SHUTTLE_DOCKER_INTEGRATION=1 \
  "$IMAGE" \
  bash -lc "
    set -euo pipefail
    mkdir -p '$CONTAINER_WORK'
    tar \
      --exclude='.git' \
      --exclude='.venv' \
      --exclude='__pycache__' \
      --exclude='.pytest_cache' \
      -C '$CONTAINER_SRC' \
      -cf - . | tar -C '$CONTAINER_WORK' -xf -
    cd '$CONTAINER_WORK'
    ./scripts/bootstrap.sh
    source .venv/bin/activate
    git init -b main '$CONTAINER_WORK/.test-git-root' >/dev/null
    git -C '$CONTAINER_WORK/.test-git-root' config user.email 'shuttle@example.test'
    git -C '$CONTAINER_WORK/.test-git-root' config user.name 'Shuttle Test'
    touch '$CONTAINER_WORK/.test-git-root/README.md'
    git -C '$CONTAINER_WORK/.test-git-root' add README.md
    git -C '$CONTAINER_WORK/.test-git-root' commit -m 'initial' >/dev/null
    SHUTTLE_GIT_ROOT='$CONTAINER_WORK/.test-git-root' pytest -q
    ./scripts/integration/smoke.sh
  "
