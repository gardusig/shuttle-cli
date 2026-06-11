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
  bash -c "
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
    git config --global user.email 'shuttle@example.test'
    git config --global user.name 'Shuttle Test'
    env -u GIT_DIR -u GIT_WORK_TREE git -C '$CONTAINER_WORK' init -b main
    env -u GIT_DIR -u GIT_WORK_TREE git -C '$CONTAINER_WORK' add -A
    env -u GIT_DIR -u GIT_WORK_TREE git -C '$CONTAINER_WORK' commit -m 'docker integration snapshot'
    pytest -q
    ./scripts/integration/smoke.sh
  "
