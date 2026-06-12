# GitHub integration (`shuttle gh`)

Deterministic GitHub operations for agents and humans. Wraps authenticated **`gh`** with JSON-first output and write gates (same model as `shuttle git`).

**Integration partner:** [cursor-skills](https://github.com/gardusig/cursor-skills) — `@gh-*` skills invoke these commands instead of embedding raw `gh` bash fences.

## Prerequisites

- `gh` installed and authenticated (`gh auth status`)
- `shuttle` on PATH

## Global flags

| Flag | Default | Purpose |
| --- | --- | --- |
| `--repo owner/name` | gh context | Target repository |
| `--format json\|table` | `json` | Output shape (agents use json) |
| `--yes` / `-y` | off | Skip interactive write gate (use after Cursor **Proceed**) |

## Double-gate contract

| Context | Cursor skill | shuttle write |
| --- | --- | --- |
| Agent after **Proceed** | AskQuestion in chat | append **`--yes`** |
| Human in terminal | — | interactive gate or **`--yes`** |
| Read-only | no gate | no **`--yes`** |

## Issue commands

### Read (no gate)

```bash
shuttle gh issue list --state open --limit 30 --format json
shuttle gh issue view 42 --format json
shuttle gh issue search "label:bug" --format json
```

### Write (gate unless `--yes`)

```bash
shuttle gh issue create --title "1 — Epic" --body-file body.md --label epic:foo --yes
shuttle gh issue edit 42 --title "1.1 — Child" --yes
shuttle gh issue close 42 --comment "Done" --yes
shuttle gh issue delete 42 --yes
shuttle gh issue comment 42 --body "Note" --yes
shuttle gh issue batch --file batch.yaml --yes
```

### Batch YAML shape

```yaml
operations:
  - action: create
    title: "1 — Epic title"
    body_file: .cursor/gh/issue/epic.md
    labels: ["epic:slug", "issue-type:epic"]
  - action: create
    title: "1.1 — Child"
    body_file: .cursor/gh/issue/child.md
    labels: ["epic:slug", "issue-type:child"]
  - action: edit
    number: 100
    body_file: .cursor/gh/issue/epic-updated.md
```

## Label commands

```bash
shuttle gh label list --format json
shuttle gh label create my-label --color ff0000 --yes
shuttle gh label delete my-label --yes
shuttle gh label sync --manifest .cursor/gh/labels.manifest.yaml --yes
shuttle gh label sync --manifest .cursor/gh/labels.manifest.yaml --prune-orphans --yes
```

## Pull request commands

```bash
shuttle gh pr list --format json
shuttle gh pr view 10 --format json
shuttle gh pr diff 10
shuttle gh pr create --title "…" --body-file pr.md --yes
shuttle gh pr edit 10 --body-file pr.md --yes
shuttle gh pr close 10 --yes
shuttle gh pr merge 10 --merge-method squash --yes
```

## Repo commands

```bash
shuttle gh --format json repo view
shuttle gh --format json repo view --json-fields nameWithOwner,owner,issueTemplates,pullRequestTemplates
```

## Backlog commands

Sequence titles use **`N — Title`** (epic) and **`N.M — Title`** (child).

```bash
shuttle gh backlog tree --format json
shuttle gh backlog next --format json
shuttle gh backlog resequence --file plan.yaml --yes
```

Resequence plan YAML:

```yaml
renames:
  - number: 42
    title: "1.2 — Renamed child"
```

## JSON output examples

**`backlog next`:**

```json
{
  "number": 71,
  "title": "1.1 — PR prevalidate",
  "url": "https://github.com/owner/repo/issues/71",
  "sequence": "1.1 —"
}
```

**`backlog tree`:**

```json
{
  "repo": "owner/repo",
  "roots": [{"number": 70, "title": "1 — Epic", "sequence": "1 —"}],
  "epics": {"epic:slug": [{"number": 71, "title": "1.1 — Child"}]}
}
```

## Tests

Unit tests mock the gh provider: `tests/test_gh_commands.py`.

Run: `./scripts/test-unit.sh`

## See also

- [architecture.md](architecture.md) — CLI → Service → Provider
- [cursor-skills docs/gh.md](https://github.com/gardusig/cursor-skills/blob/main/docs/gh.md)
- shuttle-cli epic **01** — GitHub integration
