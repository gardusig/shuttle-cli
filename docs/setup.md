# Setup (macOS)

## Requirements

- Python **3.12+**
- `git` on PATH
- Optional: `gh` for GitHub (used by cursor-skills, not shuttle-cli)

## Development install

```bash
git clone https://github.com/gardusig/shuttle-cli.git
cd shuttle-cli
./scripts/bootstrap.sh
source .venv/bin/activate
python -m shuttle --help
```

## User install

```bash
./scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
shuttle --version
```

## Troubleshooting

- **`git` not in a repository** — run commands from a git worktree root.
- **Refusing to push** — pass `--yes` to confirm: `shuttle git push --yes`.
- **Dirty tree on `main`** — pass `--yes` to destructive align/reset commands.
- **`shuttle git start` deleted my files** — use `--no-prep` to branch in place; default `start` aligns main first.
