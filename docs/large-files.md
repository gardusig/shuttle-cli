# Largest files in the repo

Find heavy paths before they land in git history or slow down clones.

## CLI

```bash
# Top 20 tracked files (git index)
shuttle git large-files

# Top 50
shuttle git large-files -n 50

# Include untracked / build artifacts in working tree
shuttle git large-files --worktree

# Shell wrapper (cursor-skills @git-large-files)
./scripts/git/large-files.sh --worktree -n 30
```

Output is size in bytes (right-aligned) and path relative to the repo root.

## When to use which mode

| Mode | Scans | Use when |
| --- | --- | --- |
| Default | `git ls-files` (tracked only) | Auditing what is already committed |
| `--worktree` | All files under the repo (except `.git`) | Finding local blobs, caches, or accidental downloads |

## Typical workflow

1. Run `shuttle git large-files --worktree -n 30` on a dirty tree before commit.
2. Add offenders to `.gitignore` or remove them.
3. Re-run on tracked files only to confirm the index is lean.

Related: [Git commands](git.md) · [Quick defaults](quick-defaults.md) · `shuttle links`
