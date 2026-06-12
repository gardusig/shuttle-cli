# Git commands

`shuttle git` wraps common local git workflows. Commit message defaults to `.`.

Each command maps to a [cursor-skills git skill](https://github.com/gardusig/cursor-skills/tree/main/skills/git) and has a shell wrapper under `scripts/git/`:

| Skill | Script | Command |
| --- | --- | --- |
| `@git-branch` | `scripts/git/branch.sh` | `shuttle git branch` |
| `@git-branch-delete` | `scripts/git/branch-delete.sh` | `shuttle git branch-delete` |
| `@git-branch-delete-all` | `scripts/git/branch-delete-all.sh` | `shuttle git branch-delete-all` |
| `@git-branch-clear` | `scripts/git/branch-clear.sh` | `shuttle git branch-clear` |
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
| `@git-zip` | `scripts/git/zip.sh` | `shuttle git zip` |

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
| `git push` | `--yes` or interactive prompt (shows branch + intent summary) |
| `git reset` | `--yes` or interactive prompt (commits dirty branch work by default) |
| `git main` (align main only) | `--yes` or interactive prompt |
| `git branch-delete` | `--yes` or interactive prompt |
| `git branch-clear` | `--yes` or interactive prompt; optional second prompt for remote branches |
| `git stash drop/clear` | `--yes` or interactive prompt |
| `git tag --push` | `--yes` or interactive prompt |

No confirmation needed:

- `git commit`
- `git start --no-prep` (creates branch from current state)
- `git pull`
- `git stash push/list/apply/pop`

## Start a branch

Default (issue workflow — align main + branch):

```bash
shuttle git start issue-9-docker --yes
```

Branch from the **current** working tree without reset/clean:

```bash
shuttle git start my-feature --no-prep
```

## Return to synced main

```bash
shuttle git reset --yes              # commit dirty branch work, sync main, prune merged branches
shuttle git reset --yes --main-only  # sync main only (keep local branches)
shuttle git reset --yes --discard    # drop uncommitted work on current branch
```

On a feature branch with uncommitted edits, `reset` commits with `.` (or `-m`) before checking out `main`. Then it fetches, fast-forwards `main` when upstream exists (else hard-resets to `origin/main`), and cleans the worktree.

## Publish

```bash
shuttle git push              # interactive: branch summary → add + commit + push
shuttle git push --yes        # non-interactive
shuttle git commit -m "wip"   # commit only (no push)
```

`push` shows a write gate with branch, dirty state, commit message, and intent (`add → commit → push`) before running. On `main`, it starts a random branch first unless you pass `--allow-main`.

## Clear all branches (nuclear local reset)

`branch-delete-all` removes only **merged** branches. `branch-clear` is stronger:

```bash
shuttle git branch-clear
```

1. Write gate — confirms hard reset + clean, checkout `main`, delete **every** local branch except `main` (lists branches in the prompt).
2. Second prompt — optionally delete all remote branches on `origin` except `main` (default: keep remotes).

Non-interactive full wipe:

```bash
shuttle git branch-clear --yes --delete-remote
```

## Tag and zip

```bash
shuttle git tag                    # annotated tag YYYY-MM-DD on HEAD
shuttle git tag --push --yes       # non-interactive push
shuttle git zip                    # zip today's tag → data/backups/YYYY-MM-DD.zip
shuttle git zip 2026-06-11 -o out.zip
```

Interactive `tag` flow:

1. Default name is **today's date** (`YYYY-MM-DD`).
2. If the tag exists **locally** → prompt to replace (write gate).
3. If `origin` exists → prompt to **push** (default no).
4. If the tag exists on **origin** and you push → prompt to **force-push**.

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
