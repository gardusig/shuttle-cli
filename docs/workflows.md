# Common usage flows

Visual maps for everyday `shuttle` workflows. Command details live in [git.md](git.md) and [quick-defaults.md](quick-defaults.md).

## Full issue lifecycle

```mermaid
flowchart TD
    subgraph before [1 — Before work]
        P["shuttle git reset --yes --main-only<br/>sync main"]
    end

    subgraph start [2 — Start issue]
        K["shuttle git start issue-9-slug --yes<br/>align main + new branch"]
    end

    subgraph loop [3 — During work]
        D["edit files"]
        S["shuttle git push<br/>add · commit · push"]
        Y["shuttle git pull<br/>stay current on main"]
        D --> S
        S --> D
        Y --> D
    end

    subgraph after [4 — After merge]
        L["shuttle git reset --yes<br/>sync main · delete merged branches"]
        L2["shuttle git reset --yes --all-local<br/>delete every local branch except main"]
    end

    P --> K --> loop
    loop --> PR["open PR · merge on GitHub"]
    PR --> L
    L --> P
```

| Phase | Shortcut | What it does | Older equivalent |
| --- | --- | --- | --- |
| Sync main | `git reset --yes --main-only` | checkout `main`, fetch, pull/ff or hard-reset, clean worktree | `git main --yes` |
| Start issue | `git start [branch] --yes` | align main + `checkout -b` | — |
| Publish WIP | `git push --yes` | add + commit + push current branch; on `main`, start random branch first | `git commit` + `git push` |
| Stay current | `git pull` | fetch + merge upstream/main into feature branch | — |
| After merge | `git reset --yes` | return to synced main + delete **merged** branches (+ remote) | `git post-merge-cleanup --yes` |
| Nuclear local | `git reset --yes --all-local` | synced main + delete **all** local branches except main | `git branch-clear --yes` |

All destructive steps show the **write gate** (branch, dirty state, intent) before running. Pass `--yes` / `-y` to skip the prompt (summary still prints).

**Leaving a feature branch:** `reset` commits uncommitted work on the current branch (message `.` by default) before syncing `main`. Pass `--discard` to drop uncommitted changes instead.

### Example session

```bash
# Monday: synced main
shuttle git reset --yes --main-only

# Pick up GitHub issue #9
shuttle git start issue-9-docker --yes

# Loop until PR is ready
shuttle git push          # interactive
shuttle git pull          # optional: merge latest main
shuttle git push --yes

# After PR merged
shuttle git reset --yes
```

## Feature work (start → publish)

```mermaid
flowchart LR
    subgraph setup [Setup once]
        A["./scripts/bootstrap.sh"]
        B["./scripts/install.sh"]
        A --> B
    end

    subgraph daily [Daily loop]
        C["shuttle git start --no-prep"]
        D["edit files"]
        E["shuttle git push"]
        F{"more work?"}
        G["open PR / merge"]
        C --> D --> E --> F
        F -->|yes| D
        F -->|no| G
    end

    B --> C
```

## Sync with main (on feature branch)

```mermaid
flowchart TD
    A["on feature branch"] --> B["shuttle git pull<br/>fetch + merge upstream + main"]
    B --> C{conflicts?}
    C -->|no| D["shuttle git push"]
    C -->|yes| E["resolve conflicts"]
    E --> D
```

## Write gate (destructive / remote)

```mermaid
flowchart TD
    A["push / reset / start …"] --> B["read worktree snapshot"]
    B --> C["intent summary<br/>branch · dirty · plan"]
    C --> D["--- shuttle write gate ---"]
    D --> E{"--yes or confirm?"}
    E -->|no| F["Aborted"]
    E -->|yes| G["run git steps"]
```

## After merge (cleanup options)

```mermaid
flowchart TD
    A["PR merged on GitHub"] --> B{"how aggressive?"}
    B -->|default| C["shuttle git reset --yes<br/>merged branches only"]
    B -->|nuclear local| D["shuttle git reset --yes --all-local"]
    B -->|legacy| E["shuttle git post-merge-cleanup --yes"]
    B -->|remote too| F["shuttle git branch-clear --yes --delete-remote"]
```

## Health check & bookmarks

```mermaid
flowchart LR
    subgraph review [Workspace health]
        R1["shuttle git review"]
        R2["shell syntax · test-unit.sh in Docker"]
        R1 --> R2
    end

    subgraph bookmarks [Chrome bookmarks]
        B1["./scripts/chrome/export-bookmarks.sh"]
        B2["data/bookmarks/bookmarks.html"]
        B3["./scripts/chrome/import-bookmarks.sh"]
        B1 --> B2 --> B3
    end

    subgraph docker [Isolated checks]
        D1["./scripts/test-integration.sh"]
        D2["copy repo · pytest · smoke · live docker"]
        D1 --> D2
    end
```

## Discover commands

```mermaid
flowchart TD
    A["shuttle --help"] --> B["shuttle links<br/>full index"]
    B --> C["docs/README.md"]
    B --> D["scripts/git/*.sh"]
    A --> F["shuttle git --help"]
```

See also: [Architecture](architecture.md) · [Docker integration](docker.md) · `shuttle links`
