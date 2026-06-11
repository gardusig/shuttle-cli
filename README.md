# shuttle-cli

macOS CLI for **git shortcuts** (deterministic, no AI) and future backup/sync workflows.

## Quickstart (macOS)

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
python -m shuttle --help
```

Optional install to `~/.local/bin`:

```bash
./scripts/install.sh
shuttle git --help
```

## Common git commands

| Task | Command |
| --- | --- |
| **Before work** (clean main) | `shuttle git prep` |
| **Start issue** (prep + branch) | `shuttle git kick issue-9-slug` |
| **During work** (add + commit + push) | `shuttle git ship` |
| **After merge** (main + prune branches) | `shuttle git land --yes` |
| Start branch (no prep) | `shuttle git start [name]` |
| Commit only | `shuttle git commit` |
| Push only | `shuttle git push --yes` |
| Sync feature branch | `shuttle git pull` |
| Delete merged branch | `shuttle git branch-delete BRANCH --yes` |
| Clear all branches (keep `main`) | `shuttle git branch-clear --yes` |
| Tag release | `shuttle git tag` (today's date) · `shuttle git zip TAG` |

Short alias: `shuttle g push --yes` == `shuttle git push --yes`.

Shell wrappers for every [cursor-skills git skill](https://github.com/gardusig/cursor-skills/tree/main/skills/git) live in `scripts/git/` (e.g. `./scripts/git/review.sh`).

**Safety:** destructive actions (reset, clean, delete, push) require `--yes` or an interactive confirmation. `shuttle git start` creates a branch from the current state without reset/clean unless you pass `--align-main --yes`.

## Chrome bookmarks

```bash
./scripts/chrome/export-bookmarks.sh   # → data/bookmarks/bookmarks.html
./scripts/chrome/import-bookmarks.sh   # restore from backup
```

See [docs/bookmarks.md](docs/bookmarks.md).

## Docker integration

Run CLI and shell smoke checks in a disposable container copy:

```bash
./scripts/test-in-docker.sh
```

CI runs **unit** (macOS pytest) and **integration** (Docker) on every pull request. See [docs/docker.md](docs/docker.md).

## Docs

- [Setup](docs/setup.md)
- [Git commands](docs/git.md)
- [Chrome bookmarks](docs/bookmarks.md)
- [Docker integration](docs/docker.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)

## Related

- [cursor-skills](https://github.com/gardusig/cursor-skills) — `@gh-*` AI workflows for issues/PRs
- Bootstrap spec: [shuttle-cli #3](https://github.com/gardusig/shuttle-cli/issues/3)
- Bookmarks: [shuttle-cli #1](https://github.com/gardusig/shuttle-cli/issues/1)
- Docker integration: [shuttle-cli #9](https://github.com/gardusig/shuttle-cli/issues/9)
