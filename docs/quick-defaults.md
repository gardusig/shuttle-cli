# Quick defaults

Shuttle favors **suggested values** over prompts so common flows are one command.

| Command | Default when omitted | Example |
| --- | --- | --- |
| `shuttle git start` | Branch `wip-YYMMDD-NNN` (daily sequence) | `shuttle git start` → `wip-260611-001` |
| `shuttle git commit` | Message `.` | `shuttle git commit` |
| `shuttle git push` | Commit message `.` if dirty | `shuttle git push --yes` |
| `shuttle git ship` | Add + commit + push with branch summary gate | `shuttle git ship --yes` |
| `shuttle git prep` | Align main (fetch, reset, clean) | `shuttle git prep --yes` |
| `shuttle git kick` | Prep + new branch (`wip-YYMMDD-NNN` or your slug) | `shuttle git kick issue-9-docker --yes` |
| `shuttle git land` | After merge: main + delete merged branches | `shuttle git land --yes` |
| `shuttle git stash push` | Message `.` | `shuttle git stash push` |
| `shuttle git tag` | Name `YYYY-MM-DD` (today) | `shuttle git tag` |
| `shuttle git zip` | Tag `YYYY-MM-DD` (today) | `shuttle git zip` → `data/backups/TAG.zip` |

## Branch names

`wip-260611-001`, `wip-260611-002`, … increment per day based on existing local branches. Pass an explicit name only when you care:

```bash
shuttle git start my-feature
```

## Shell wrappers

Scripts under `scripts/git/` forward flags to the CLI and inherit the same defaults:

```bash
./scripts/git/start.sh          # auto branch name
./scripts/git/commit.sh         # message '.'
./scripts/git/large-files.sh    # see docs/large-files.md
```

Full index: `shuttle links` · [Git commands](git.md)
