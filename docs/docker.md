# Docker

## CLI shortcuts

Monitor and cleanup only (no `docker run` from shuttle):

| Command | Purpose |
| --- | --- |
| `shuttle docker top` | Dashboard: CPU, memory, and storage leaders |
| `shuttle docker stats --by cpu` | Top consumers by domain (`memory`, `storage`, `all`) |
| `shuttle docker ps` / `containers` / `images` / `df` | Lists and disk summary |
| `shuttle docker stop --yes` | Stop running containers |
| `shuttle docker container-delete --yes` | Remove containers |
| `shuttle docker image-delete --yes` | Prune unused images |
| `shuttle docker reset --yes` | Full wipe: stop, delete containers, prune images + cache |
| `shuttle docker clean TARGET --yes` | Targeted: `containers`, `images`, `cache`, `all` |

Shell wrappers: `scripts/docker/` (`reset.sh`, `stop.sh`, `container-delete.sh`, `image-delete.sh`, `stats.sh`).

## Install vs verify

- **Install (host):** `./scripts/bootstrap.sh` / `./scripts/install.sh` — runtime deps only; use `shuttle` on macOS.
- **Verify (Docker):** everything in this document — pytest, coverage, smoke, public API checks, live docker.

Host `pytest` is intentionally unsupported. Dev dependencies (`pytest`, `pytest-cov`) install only inside the container copy (`SHUTTLE_BOOTSTRAP_DEV=1`) or in the pre-built image layer.

## Dev / test image

Issue [#9](https://github.com/gardusig/shuttle-cli/issues/9) tracks Docker-based test and onboarding lanes.

The [`Dockerfile`](../Dockerfile) builds **`shuttle-cli:dev`**: Python 3.12 on Debian slim, git, bash, Docker CLI (static binary), and an editable install with dev dependencies. Use it from macOS via Docker Desktop or on Linux with Docker Engine — same image tag everywhere.

```bash
./scripts/docker/build-image.sh   # build shuttle-cli:dev
./scripts/test-unit.sh            # unit tests (CI gate)
./scripts/test-integration.sh     # integration pytest + smoke + live docker
./scripts/docker/shell.sh           # onboard: interactive shell
```

Host repo is mounted read-only; each run copies a fresh tree to `/tmp/shuttle-cli` (see `scripts/docker/common.sh`). Integration tests mount `/var/run/docker.sock` so live `shuttle docker` checks run against your host daemon without a host Python venv.

## CI (GitHub Actions)

[`.github/workflows/test.yml`](../.github/workflows/test.yml) runs on **every pull request** and on pushes to `main`:

| Job | Runner | What runs |
| --- | --- | --- |
| `unit` | `ubuntu-latest` | `shuttle-cli:dev` → `./scripts/test-unit.sh` |
| `integration` | `ubuntu-latest` | same image → `./scripts/test-integration.sh` |

Both jobs must pass before merge (enable **Require status checks** for `Unit tests (Docker)` and `Integration tests (Docker)` in branch protection).

## Run tests

```bash
./scripts/docker/build-image.sh   # optional; skipped when image already exists
./scripts/test-unit.sh            # unit only
./scripts/test-integration.sh     # full integration gate
```

The runner:

1. Builds the local `Dockerfile` (or uses `SHUTTLE_DOCKER_SKIP_BUILD=1` with a pre-built tag).
2. Mounts the repository read-only at `/workspace/src`.
3. Copies the repo into `/tmp/shuttle-cli` inside the container, excluding `.git`, `.venv`, and cache directories.
4. Initializes a disposable git repo, bootstraps a venv inside the copy, then runs the test gate.

Because tests run from the copied tree in `/tmp`, commands like `shuttle git start` and bookmark export fixtures cannot mutate your host checkout.

## Smoke coverage

The container smoke test checks:

- `scripts/integration/check_public_endpoints.py` — every public CLI command (56 checks): read-only paths, write-gate refusals, and `--yes` success paths with **remote git mocked** (`fetch` / `push` / `ls-remote` never hit the network)
- `python -m shuttle --help` and `--version`
- placeholder endpoints: `backup`, `restore`, `drives`, `notion`, `bookmarks`
- shell syntax for `scripts/chrome`, `scripts/git`, and `scripts/integration`
- Chrome bookmark export/import using local fixture files and `SHUTTLE_SKIP_CHROME_AUTOMATION=1`
- `shuttle git start` inside a temporary git repository
