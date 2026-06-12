# shuttle-cli

macOS CLI: **`shuttle git`** · **`shuttle drive`** · **`shuttle chrome`** · **`shuttle notion`**.

## Requirements

| Tool | Needed for |
| --- | --- |
| **macOS** | Primary target for local use |
| **Python 3.12+** | Local install (`bootstrap.sh` creates a venv) |
| **[Homebrew](https://brew.sh/)** | Recommended way to install Python and git on macOS |
| **git** | `shuttle git` (run from inside a repository) |
| **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** | Verification only — unit/integration tests in `shuttle-cli:dev` |

Install Python and git with Homebrew:

```bash
brew install python@3.12 git
```

Optional: `gh` (GitHub CLI) for [cursor-skills](https://github.com/gardusig/cursor-skills) workflows — not required by shuttle-cli itself.

## Configuration (global)

Shuttle reads **`config/config.yaml`** in the clone, or **`~/.config/shuttle-cli/`** after install. Override the directory with `SHUTTLE_CONFIG_DIR`.

Copy the bundled `config/` tree and edit paths for your machine before daily use:

| Setting | Config key | Purpose |
| --- | --- | --- |
| **Git repositories** | `backup.repositories[].path` | Repos for `shuttle drive ingest` / `drive status` |
| **Tag zip folder** | `backup.tags_dir` | Local store (default: iCloud `git-tags/`) — source for `drive upload` |
| **Cloud upload roots** | `drives.yaml` → `google` / `onedrive` / `proton` | Remote folder names per provider |
| **Notion task folder** | `notion.task_directory` | Local markdown tasks (`data/tasks/`) |
| **Notion database** | `notion.database_id` | Existing board ID + `NOTION_TOKEN` env |
| **Chrome bookmarks file** | `chrome.bookmarks_file` | HTML backup (`chrome bookmarks ingest`) |
| **Chrome downloads** | `chrome.downloads_dir` | Folder polled when ingesting from Chrome |

Example `config.yaml`:

```yaml
backup:
  tags_dir: ~/Library/Mobile Documents/com~apple~CloudDocs/git-tags
  repositories:
    - path: ~/git-local/shuttle-cli
    - path: ~/git-local/my-other-repo

notion:
  database_id: your-notion-database-id
  task_directory: data/tasks

chrome:
  profile: Default
  bookmarks_file: ~/git-local/shuttle-cli/data/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
```

Cloud providers: `config/drives.yaml`. Notion token: **`export NOTION_TOKEN=...`** (never commit).

Environment overrides (optional): `SHUTTLE_BOOKMARKS_FILE`, `SHUTTLE_DOWNLOADS_DIR`, `SHUTTLE_CONFIG_DIR`, `NOTION_TOKEN`.

## Install (macOS)

Local setup is for **using** shuttle only (runtime deps). **Verification** always runs in Docker — same image locally and in CI.

```bash
./scripts/bootstrap.sh          # venv + runtime install
source .venv/bin/activate
python -m shuttle --help
```

Optional install to `~/.local/bin`:

```bash
./scripts/install.sh
shuttle git --help
shuttle drive --help
```

Do not run `pytest` on the host; use `./scripts/test-unit.sh` and `./scripts/test-integration.sh` instead.

## Common git commands

Run from inside a repository (`cd` into the repo first).

| Task | Command |
| --- | --- |
| **Sync main** (before/after work) | `shuttle git reset --yes` (`--main-only` to skip branch prune) |
| **Start issue** (align main + branch) | `shuttle git start issue-9-slug --yes` |
| **During work** (add + commit + push) | `shuttle git push --yes` (on `main`, starts random branch first) |
| Branch in place (no align) | `shuttle git start [name] --no-prep` |
| Commit only | `shuttle git commit` |
| Sync feature branch | `shuttle git pull` |
| Delete merged branch | `shuttle git branch-delete BRANCH --yes` |
| Clear all branches (keep `main`) | `shuttle git branch-clear --yes` |
| Tag on main (default: today) | `shuttle git tag` · `shuttle git tag list` · `shuttle git tag push` |
| Zip one tag (cwd repo) | `shuttle git zip` · `shuttle git zip TAG` |

Short alias: `shuttle g push --yes` == `shuttle git push --yes`.

Shell wrappers: `scripts/git/` (e.g. `./scripts/git/review.sh`). See [docs/git.md](docs/git.md).

**Safety:** destructive actions (reset, clean, delete, push) require `--yes` or an interactive confirmation. Default `shuttle git start` aligns main then branches; pass `--no-prep` to branch from the current state.

## Drive (`shuttle drive`)

Local hub: **iCloud** `git-tags/{repo}/{tag}.zip` (via `backup.tags_dir`). Cloud: append-only upload to Google Drive, OneDrive, Proton.

| Task | Command |
| --- | --- |
| **Status** (git tags vs local zips) | `shuttle drive status` |
| **Ingest** (zip all tags → local store) | `shuttle drive ingest` (all repos in config) or `shuttle drive ingest PATH` |
| List local zips | `shuttle drive list` · `shuttle drive list PATH` |
| Delete local zip | `shuttle drive delete PATH TAG --yes` |
| **Upload** to cloud | `shuttle drive upload` · `shuttle drive upload google` · `onedrive` · `proton` |
| **Sync** (ingest all + upload all) | `shuttle drive sync` |

Typical end-of-day:

```bash
shuttle git tag --yes && shuttle git zip    # single repo (cwd)
shuttle drive upload                        # push missing zips to cloud
```

Multi-repo:

```bash
shuttle drive sync                          # ingest all repos + upload all clouds
# or step by step:
shuttle drive ingest
shuttle drive status
shuttle drive upload
```

`git zip` is the quick path for the current repo; `drive ingest` iterates configured repositories (or one `PATH`). See [docs/drive.md](docs/drive.md) · [issue #4](https://github.com/gardusig/shuttle-cli/issues/4).

Shell wrappers: `scripts/drive/` (`status.sh`, `ingest.sh`, `upload.sh`, `sync.sh`).

## Chrome (`shuttle chrome`)

Browser integrations; **bookmarks** is the first subcommand. Path: **`chrome.bookmarks_file`** in config.

| Direction | Command |
| --- | --- |
| **Chrome → local** | `shuttle chrome bookmarks ingest` |
| **Local → Chrome** | `shuttle chrome bookmarks deploy` |

```bash
shuttle chrome bookmarks ingest   # Chrome → local HTML file
shuttle chrome bookmarks deploy   # local file → Chrome
```

Shell wrappers: `./scripts/chrome/ingest.sh` · `./scripts/chrome/deploy.sh` (deprecated: `import.sh` / `export.sh`).

See [docs/bookmarks.md](docs/bookmarks.md) · epic [#24](https://github.com/gardusig/shuttle-cli/issues/24) (shell scripts: [#1](https://github.com/gardusig/shuttle-cli/issues/1)).

## Notion (`shuttle notion`)

Local tasks: **`notion.task_directory`** (`data/tasks/`). Auth: **`NOTION_TOKEN`** + `notion.database_id`.

| Command | Purpose |
| --- | --- |
| `shuttle notion ingest` | Notion → `data/tasks/{id}.md` |
| `shuttle notion deploy --yes` | Local tasks → Notion |
| `shuttle notion sync` | Ingest from Notion, then deploy local tasks |
| `shuttle notion cleanup --yes` | Archive all database pages |

See [docs/notion.md](docs/notion.md) · epic [#2](https://github.com/gardusig/shuttle-cli/issues/2) · children [#20](https://github.com/gardusig/shuttle-cli/issues/20)–[#23](https://github.com/gardusig/shuttle-cli/issues/23).

## Docker

Local Docker monitor and cleanup (requires `docker` on PATH; no container start):

| Task | Command |
| --- | --- |
| **Dashboard** (CPU, memory, storage) | `shuttle docker top` |
| **By domain** | `shuttle docker stats --by cpu` / `memory` / `storage` |
| **Storage lists** | `shuttle docker images` · `shuttle docker containers` · `shuttle docker df` |
| **Stop running** | `shuttle docker stop --yes` |
| **Delete containers** | `shuttle docker container-delete --yes` |
| **Prune images** | `shuttle docker image-delete --yes` (`--all-images` for all unused) |
| **Full reset** | `shuttle docker reset --yes` |
| Targeted cleanup | `shuttle docker clean containers --yes` · `clean images` · `clean all` |

Shell wrappers live in `scripts/docker/` (e.g. `./scripts/docker/reset.sh --yes`).

Destructive commands use the write gate; pass `--yes` in scripts.

## Verify (Docker)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) on macOS (or Docker Engine on Linux). The `shuttle-cli:dev` Linux image is the only supported test environment:

```bash
./scripts/docker/build-image.sh   # build once (or auto-build on first test run)
./scripts/test-unit.sh            # unit tests (≥80% coverage)
./scripts/test-integration.sh     # full pytest + smoke + live docker
./scripts/docker/shell.sh         # onboard: interactive shell in container
```

See [docs/docker.md](docs/docker.md).

## Docs

- [Setup](docs/setup.md)
- [Git commands](docs/git.md)
- [Drive (local + cloud)](docs/drive.md)
- [Chrome](docs/bookmarks.md) · [Notion](docs/notion.md)
- [Docker integration](docs/docker.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)

## Related

- [cursor-skills](https://github.com/gardusig/cursor-skills) — `@gh-*` AI workflows for issues/PRs
- Cloud drive epic: [shuttle-cli #4](https://github.com/gardusig/shuttle-cli/issues/4)
- Bootstrap spec: [shuttle-cli #3](https://github.com/gardusig/shuttle-cli/issues/3)
- Chrome: [shuttle-cli #24](https://github.com/gardusig/shuttle-cli/issues/24) · bookmarks scripts [#1](https://github.com/gardusig/shuttle-cli/issues/1)
- Docker integration: [shuttle-cli #9](https://github.com/gardusig/shuttle-cli/issues/9)
