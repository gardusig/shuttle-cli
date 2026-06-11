# Docker integration

Issue [#9](https://github.com/gardusig/shuttle-cli/issues/9) tracks a Docker-based integration lane for exercising CLI and shell scripts without damaging local files.

## Run locally

```bash
./scripts/test-in-docker.sh
```

The runner:

1. Builds the local `Dockerfile`.
2. Mounts the repository read-only at `/workspace/src`.
3. Copies the repo into `/tmp/shuttle-cli` inside the container, excluding `.git`, `.venv`, and cache directories.
4. Runs `./scripts/bootstrap.sh`, `pytest -q`, and `./scripts/integration/smoke.sh`.

Because tests run from the copied tree in `/tmp`, commands like `shuttle git start` and bookmark export fixtures cannot mutate your host checkout.

## Optional pytest trigger

The normal pytest suite only verifies the Docker harness files. To run Docker from pytest:

```bash
SHUTTLE_RUN_DOCKER_TESTS=1 pytest tests/test_docker_integration.py -q
```

## Smoke coverage

The container smoke test checks:

- `python -m shuttle --help` and `--version`
- placeholder endpoints: `backup`, `restore`, `drives`, `notion`, `bookmarks`
- shell syntax for `scripts/chrome`, `scripts/git`, and `scripts/integration`
- Chrome bookmark export/import using local fixture files and `SHUTTLE_SKIP_CHROME_AUTOMATION=1`
- `shuttle git start` inside a temporary git repository
