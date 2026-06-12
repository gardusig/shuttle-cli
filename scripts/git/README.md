# Git scripts

Shell wrappers for each [cursor-skills git skill](https://github.com/gardusig/cursor-skills/tree/main/skills/git). Each script delegates to `shuttle git <command>`.

| Script | cursor-skills skill | CLI |
| --- | --- | --- |
| `branch.sh` | `git/branch` | `shuttle git branch` |
| `branch-delete.sh` | `git/branch/delete` | `shuttle git branch-delete` |
| `branch-delete-all.sh` | `git/branch/delete/all` | `shuttle git branch-delete-all` |
| `branch-clear.sh` | `git/branch/clear` | `shuttle git branch-clear` |
| `cherry-pick.sh` | `git/cherry/pick` | `shuttle git cherry-pick` |
| `commit.sh` | `git/commit` | `shuttle git commit` |
| `docs.sh` | `git/docs` | `shuttle git docs` |
| `large-files.sh` | `git/large/files` | `shuttle git large-files` |
| `main.sh` | `git/main` | `shuttle git main` |
| `post-merge-cleanup.sh` | `git/post/merge/cleanup` | `shuttle git post-merge-cleanup` |
| `pull.sh` | `git/pull` | `shuttle git pull` |
| `push.sh` | `git/push` | `shuttle git push` |
| `reset.sh` | `git/reset` | `shuttle git reset` |
| `rebase.sh` | `git/rebase` | `shuttle git rebase` |
| `reset.sh` | `git/reset` | `shuttle git reset` |
| `revert.sh` | `git/revert` | `shuttle git revert` |
| `review.sh` | `git/review` | `shuttle git review` |
| `start.sh` | `git/start` | `shuttle git start` |
| `stash.sh` | `git/stash` | `shuttle git stash` |
| `tag.sh` | `git/tag` | `shuttle git tag` |
| `zip.sh` | `git/zip` | `shuttle git zip` |

Usage:

```bash
./scripts/git/commit.sh -m "wip"
./scripts/git/review.sh          # shell syntax + Docker unit tests
./scripts/git/review.sh --quick  # shell syntax only
```

Set `SHUTTLE_BIN` to override the shuttle executable.

Verification never runs host `pytest`; `review` delegates to `./scripts/test-unit.sh` in Docker when not `--quick`.
