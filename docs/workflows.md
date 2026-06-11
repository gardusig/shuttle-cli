# Common usage flows

Visual maps for everyday `shuttle` workflows. Command details live in [git.md](git.md) and [quick-defaults.md](quick-defaults.md).

## Feature work (start → publish)

Default branch name and commit message — no prompts until push.

```mermaid
flowchart LR
    subgraph setup [Setup once]
        A["./scripts/bootstrap.sh"]
        B["./scripts/install.sh"]
        A --> B
    end

    subgraph daily [Daily loop]
        C["shuttle git start<br/>auto wip-YYMMDD-NNN"]
        D["edit files"]
        E["shuttle git large-files<br/>optional audit"]
        F["shuttle git commit<br/>message '.'"]
        G{"push?"}
        H["shuttle git push --yes<br/>write gate"]
        I["open PR / merge"]
        C --> D --> E --> F --> G
        G -->|yes| H --> I
        G -->|later| D
    end

    B --> C
```

## Sync with main

Stay current while on a feature branch.

```mermaid
flowchart TD
    A["on feature branch"] --> B["shuttle git pull<br/>fetch + merge upstream + main"]
    B --> C{conflicts?}
    C -->|no| D["shuttle git commit"]
    C -->|yes| E["resolve conflicts"]
    E --> D
    D --> F["shuttle git push --yes"]
```

## Write gate (destructive / remote)

Read inventory first, then confirm before mutating.

```mermaid
flowchart TD
    A["shuttle git push / main / reset<br/>branch-delete / branch-clear …"] --> B["read worktree snapshot<br/>branch · dirty · status"]
    B --> C["--- shuttle write gate ---"]
    C --> D{"--yes or<br/>interactive confirm?"}
    D -->|no| E["Aborted"]
    D -->|yes| F["run git mutation"]
    F --> G["done"]
```

Safe by default: `shuttle git start` does **not** reset or clean unless you pass `--align-main --yes`.

## After merge (cleanup)

```mermaid
flowchart TD
    A["PR merged on GitHub"] --> B["shuttle git main --yes<br/>align local main"]
    B --> C["shuttle git branch-delete FEATURE --yes<br/>one branch"]
    B --> D["shuttle git post-merge-cleanup --yes<br/>align + delete merged"]
    B --> E["shuttle git branch-clear<br/>nuclear: keep main only"]
    E --> F{"also delete<br/>origin branches?"}
    F -->|confirm| G["remote branches removed"]
    F -->|skip| H["local only"]
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
        D3["CI: docker-integration job"]
        D1 --> D2
        D3 --> D1
    end
```

## Discover commands

```mermaid
flowchart TD
    A["shuttle --help"] --> B["shuttle links<br/>full index"]
    B --> C["docs/README.md"]
    B --> D["scripts/git/*.sh"]
    B --> E["scripts/chrome/*.sh"]
    A --> F["shuttle git --help"]
    F --> G["shuttle git docs"]
```

See also: [Architecture](architecture.md) · [Docker integration](docker.md) · `shuttle links`
