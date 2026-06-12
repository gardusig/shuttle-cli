# Quick defaults

Shuttle favors **suggested values** over prompts so common flows are one command.

| Command | Default when omitted | Example |
| --- | --- | --- |
| `shuttle git start` | Prep + branch `wip-YYMMDD-NNN` or your slug | `shuttle git start issue-9-docker --yes` |
| `shuttle git commit` | Message `.` | `shuttle git commit` |
| `shuttle git push` | Add + commit + push; message `.` if dirty; on `main`, start random branch first | `shuttle git push --yes` |
| `shuttle git reset` | Return to synced main + prune merged branches | `shuttle git reset --yes` |
| `shuttle git reset --main-only` | Sync main only (no branch delete) | `shuttle git reset --yes --main-only` |
| `shuttle git stash push` | Message `.` | `shuttle git stash push` |
| `shuttle git tag` | Name `YYYY-MM-DD` (today) | `shuttle git tag` |
| `shuttle git zip` | Tag `YYYY-MM-DD` (today) | `shuttle git zip` → `data/backups/TAG.zip` |

## Branch names

`wip-260611-001`, `wip-260611-002`, … increment per day based on existing local branches. Pass an explicit name only when you care:

```bash
shuttle git start my-feature --no-prep
```

## Shell wrappers

Scripts under `scripts/git/` forward flags to the CLI and inherit the same defaults:

```bash
./scripts/git/start.sh          # auto branch name
./scripts/git/commit.sh         # message '.'
./scripts/git/large-files.sh    # see docs/large-files.md
```

Full index: `shuttle links` · [Git commands](git.md)
