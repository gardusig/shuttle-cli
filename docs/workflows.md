# Common usage flows

Visual maps for everyday `shuttle` workflows. Command details live in [git.md](git.md) and [quick-defaults.md](quick-defaults.md).

## Full issue lifecycle

The four workflow shortcuts map to how you actually work with GitHub issues:

```mermaid
flowchart TD
    subgraph before [1 — Before work]
        P["shuttle git prep<br/>main · fetch · reset · clean -fdx"]
    end

    subgraph start [2 — Start issue]
        K["shuttle git kick issue-9-slug<br/>prep + new branch"]
    end

    subgraph loop [3 — During work]
        D["edit files"]
        S["shuttle git ship<br/>add · commit · push"]
        Y["shuttle git pull<br/>stay current on main"]
        D --> S
        S --> D
        Y --> D
    end

    subgraph after [4 — After merge]
        L["shuttle git land --yes<br/>main · delete merged branches"]
        L2["shuttle git land --yes --all-local<br/>delete every local branch except main"]
    end

    P --> K --> loop
    loop --> PR["open PR · merge on GitHub"]
    PR --> L
    L --> P
```

| Phase | Shortcut | What it does | Older equivalent |
| --- | --- | --- | --- |
| Before work | `git prep` | `main` + fetch + reset --hard + clean -fdx | `git main --yes` |
| Start issue | `git kick [branch]` | prep + `checkout -b` | `git start --align-main --yes` |
| Publish WIP | `git ship` | add + commit + push (branch summary gate) | `git commit` + `git push --yes` |
| Stay current | `git pull` | fetch + merge upstream/main into feature branch | — |
| After merge | `git land` | prep + delete **merged** branches (+ remote) | `git post-merge-cleanup --yes` |
| Nuclear local | `git land --all-local` | prep + delete **all** local branches except main | `git branch-clear --yes` |

All destructive steps show the **write gate** (branch, dirty state, intent) before running. Pass `--yes` in scripts/CI.

### Example session

```bash
# Monday: clean slate
shuttle git prep --yes

# Pick up GitHub issue #9
shuttle git kick issue-9-docker --yes

# Loop until PR is ready
shuttle git ship          # interactive
shuttle git pull          # optional: merge latest main
shuttle git ship --yes

# After PR merged
shuttle git land --yes
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
        C["shuttle git kick<br/>or git start"]
        D["edit files"]
        E["shuttle git ship"]
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
    C -->|no| D["shuttle git ship"]
    C -->|yes| E["resolve conflicts"]
    E --> D
```

## Write gate (destructive / remote)

```mermaid
flowchart TD
    A["ship / prep / kick / land / push …"] --> B["read worktree snapshot"]
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
    B -->|default| C["shuttle git land --yes<br/>merged branches only"]
    B -->|nuclear local| D["shuttle git land --yes --all-local"]
    B -->|legacy| E["shuttle git post-merge-cleanup --yes"]
    B -->|remote too| F["shuttle git branch-clear --yes --delete-remote"]
```

## Health check & bookmarks

```mermaid
flowchart LR
    subgraph review [Workspace health]
        R1["shuttle git review"]
        R2["bootstrap · shellcheck · pytest"]
        R1 --> R2
    end

    subgraph bookmarks [Chrome bookmarks]
        B1["./scripts/chrome/export-bookmarks.sh"]
        B2["data/bookmarks/bookmarks.html"]
        B3["./scripts/chrome/import-bookmarks.sh"]
        B1 --> B2 --> B3
    end

    subgraph docker [Isolated checks]
        D1["./scripts/test-in-docker.sh"]
        D2["copy repo · pytest · smoke"]
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
