# Architecture

From [issue #3](https://github.com/gardusig/shuttle-cli/issues/3):

```
CLI → Command → Workflow / Service → Provider → External API
```

## Current implementation

- **`shuttle/cli.py`** — Typer app, command registration
- **`shuttle/commands/git.py`** — git subcommands (thin)
- **`shuttle/services/git_shortcuts.py`** — git business logic + subprocess calls
- **`shuttle/utils/process.py`** — `run_git` wrapper
- **`shuttle/internal/read/`** — read-only inventory (worktree snapshot, operation classification)
- **`shuttle/internal/write/`** — write gate with delimiter + Q&A before mutations
- **`shuttle/utils/confirm.py`** — thin re-export of write gate helpers
- **`shuttle/commands/{backup,restore,...}`** — placeholders for future workflows
- **`scripts/chrome/`** — bookmark export/import (issue #1)

Providers stay unimplemented until backup/sync issues land. Git operations use local `git` only.

## Verification

| Layer | Where it runs | Entry |
| --- | --- | --- |
| Unit (≥80% coverage, excludes `shuttle/integration`) | `shuttle-cli:dev` container | `./scripts/test-unit.sh` |
| Integration (full pytest, smoke, public APIs, live docker) | same image + host socket | `./scripts/test-integration.sh` |
| Local CLI usage | host `.venv` (runtime only) | `./scripts/bootstrap.sh`, `./scripts/install.sh` |

Harness: `scripts/docker/common.sh` copies the repo to `/tmp/shuttle-cli` inside an ephemeral container so git resets and fixtures never touch the host checkout. See [docker.md](docker.md).
