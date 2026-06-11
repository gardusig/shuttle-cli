# Git commands

`shuttle git` wraps common local git workflows. Commit message defaults to `.`.

Each command maps to a [cursor-skills git skill](https://github.com/gardusig/cursor-skills/tree/main/skills/git) and has a shell wrapper under `scripts/git/`:

| Skill | Script | Command |
| --- | --- | --- |
| `@git-branch` | `scripts/git/branch.sh` | `shuttle git branch` |
| `@git-branch-delete` | `scripts/git/branch-delete.sh` | `shuttle git branch-delete` |
| `@git-branch-delete-all` | `scripts/git/branch-delete-all.sh` | `shuttle git branch-delete-all` |
| `@git-cherry-pick` | `scripts/git/cherry-pick.sh` | `shuttle git cherry-pick` |
| `@git-commit` | `scripts/git/commit.sh` | `shuttle git commit` |
| `@git-docs` | `scripts/git/docs.sh` | `shuttle git docs` |
| `@git-large-files` | `scripts/git/large-files.sh` | `shuttle git large-files` |
| `@git-main` | `scripts/git/main.sh` | `shuttle git main` |
| `@git-post-merge-cleanup` | `scripts/git/post-merge-cleanup.sh` | `shuttle git post-merge-cleanup` |
| `@git-pull` | `scripts/git/pull.sh` | `shuttle git pull` |
| `@git-push` | `scripts/git/push.sh` | `shuttle git push` |
| `@git-rebase` | `scripts/git/rebase.sh` | `shuttle git rebase` |
| `@git-reset` | `scripts/git/reset.sh` | `shuttle git reset` |
| `@git-revert` | `scripts/git/revert.sh` | `shuttle git revert` |
| `@git-review` | `scripts/git/review.sh` | `shuttle git review` |
| `@git-start` | `scripts/git/start.sh` | `shuttle git start` |
| `@git-stash` | `scripts/git/stash.sh` | `shuttle git stash` |
| `@git-tag` | `scripts/git/tag.sh` | `shuttle git tag` |

## Internal read/write

Pattern mirrors [cursor-skills internal read/write](https://github.com/gardusig/cursor-skills/tree/main/skills/internal):

1. **Read** (`shuttle/internal/read/`) — worktree snapshot, no prompts
2. **Write gate** (`shuttle/internal/write/gate.py`) — prints `--- shuttle write gate ---` with repo context, then asks to proceed
3. **Write** — mutation runs only after `--yes` or interactive confirmation

Read-only commands (`review`, `docs`, `branch list`, `stash list`) skip the gate.

## Safety gates

Operations that mutate remote state or discard local work require confirmation:

| Operation | Confirmation |
| --- | --- |
| `git push` | `--yes` or interactive prompt |
| `git main` (reset/clean) | `--yes` or interactive prompt |
| `git reset` | `--yes` or interactive prompt |
| `git branch-delete` | `--yes` or interactive prompt |
| `git stash drop/clear` | `--yes` or interactive prompt |
| `git tag --push` | `--yes` or interactive prompt |

No confirmation needed:

- `git commit`
- `git start` (creates branch from current state)
- `git pull`
- `git stash push/list/apply/pop`

## Start a branch

```bash
shuttle git start my-feature
```

Creates a branch from the **current** working tree. Does not reset or clean.

To align `main` first (destructive):

```bash
shuttle git start my-feature --align-main --yes
```

## Publish

```bash
shuttle git commit -m "wip"
shuttle git push --yes
```

## Review (workspace health)

```bash
shuttle git review
# or
./scripts/git/review.sh
```

Runs bootstrap (if needed), shell syntax checks, and `pytest`. No commit or push.

## Docs inventory

```bash
shuttle git docs
```

Lists markdown paths for sync. In-place edits use cursor-skills `@git-docs`.
