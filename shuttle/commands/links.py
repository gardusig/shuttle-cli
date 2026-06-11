from __future__ import annotations

import typer
from rich import print as rprint

from shuttle.utils.catalog import (
    QUICK_DEFAULTS,
    TOP_LEVEL_COMMANDS,
    chrome_script_entries,
    doc_entries,
    git_script_entries,
)
from shuttle.utils.config import project_root

links_app = typer.Typer(help="Index of docs, scripts, and quick defaults.", invoke_without_command=True)


@links_app.callback(invoke_without_command=True)
def links_root() -> None:
    """Print full shuttle-cli index (docs, scripts, defaults)."""
    root = project_root()
    rprint("[bold]shuttle-cli index[/bold]")
    rprint(f"repo: {root}\n")

    rprint("[bold]Quick defaults[/bold] (no prompts — just run)")
    for cmd, note in QUICK_DEFAULTS:
        rprint(f"  [cyan]shuttle {cmd}[/cyan] — {note}")
    rprint("  docs/workflows.md · docs/quick-defaults.md · docs/large-files.md")

    rprint("\n[bold]Top-level commands[/bold]")
    for name, desc in TOP_LEVEL_COMMANDS:
        rprint(f"  [cyan]shuttle {name}[/cyan] — {desc}")

    rprint("\n[bold]Documentation[/bold]")
    for entry in doc_entries(root):
        rprint(f"  {entry.doc}")

    rprint("\n[bold]Git scripts[/bold] → [dim]scripts/git/[/dim] (see docs/git.md)")
    for entry in git_script_entries(root):
        line = f"  {entry.script} → {entry.cli}"
        if entry.label == "large files":
            line += " — [dim]docs/large-files.md[/dim]"
        rprint(line)

    rprint("\n[bold]Chrome scripts[/bold] → [dim]scripts/chrome/[/dim] (see docs/bookmarks.md)")
    for entry in chrome_script_entries(root):
        rprint(f"  {entry.script} — {entry.note}")

    rprint("\n[bold]Other scripts[/bold]")
    for rel, note in (
        ("scripts/bootstrap.sh", "venv + deps"),
        ("scripts/install.sh", "install to ~/.local/bin"),
        ("scripts/test-in-docker.sh", "Docker integration run"),
    ):
        path = root / rel
        if path.is_file():
            rprint(f"  {rel} — {note}")

    rprint("\n[dim]Tip: shuttle git docs lists markdown paths for @git-docs[/dim]")
