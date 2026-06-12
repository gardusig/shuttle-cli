"""Inventory of docs, scripts, and CLI entrypoints for `shuttle links`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shuttle.utils.config import project_root


@dataclass(frozen=True)
class CatalogEntry:
    label: str
    cli: str | None = None
    script: str | None = None
    doc: str | None = None
    note: str | None = None


QUICK_DEFAULTS = (
    ("git start", "issue start: align main + branch (wip-YYMMDD-NNN or issue slug); --no-prep to branch in place"),
    ("git commit", "message defaults to '.'"),
    ("git push", "add + commit + push; on main starts random branch — use --yes -y to skip prompt"),
    ("git reset", "return to synced main + prune merged branches; --main-only for main sync only — --yes"),
    ("git stash push", "message defaults to '.'"),
    ("git tag", "name defaults to today's date (YYYY-MM-DD)"),
)

# Lifecycle shortcuts: command → shell wrapper + doc (see docs/workflows.md).
WORKFLOW_SHORTCUTS: tuple[tuple[str, str, str, str], ...] = (
    ("git reset", "reset.sh", "docs/workflows.md", "return to synced main + prune branches"),
    ("git start", "start.sh", "docs/workflows.md", "issue start: align main + named branch"),
    ("git push", "push.sh", "docs/workflows.md", "push current branch; start on main"),
)

WORKFLOW_CHAIN = "reset → start → push → (merge PR) → reset"

QUICK_DEFAULT_SCRIPTS: dict[str, str] = {
    "git start": "scripts/git/start.sh",
    "git commit": "scripts/git/commit.sh",
    "git push": "scripts/git/push.sh",
    "git reset": "scripts/git/reset.sh",
    "git stash push": "scripts/git/stash.sh",
    "git tag": "scripts/git/tag.sh",
}


GIT_SCRIPT_COMMANDS: tuple[tuple[str, str], ...] = (
    ("branch.sh", "git branch"),
    ("branch-clear.sh", "git branch-clear"),
    ("branch-delete.sh", "git branch-delete"),
    ("branch-delete-all.sh", "git branch-delete-all"),
    ("cherry-pick.sh", "git cherry-pick"),
    ("commit.sh", "git commit"),
    ("docs.sh", "git docs"),
    ("large-files.sh", "git large-files"),
    ("main.sh", "git main"),
    ("post-merge-cleanup.sh", "git post-merge-cleanup"),
    ("pull.sh", "git pull"),
    ("push.sh", "git push"),
    ("rebase.sh", "git rebase"),
    ("reset.sh", "git reset"),
    ("revert.sh", "git revert"),
    ("review.sh", "git review"),
    ("start.sh", "git start"),
    ("stash.sh", "git stash"),
    ("tag.sh", "git tag"),
    ("zip.sh", "git zip"),
)

CHROME_SCRIPTS: tuple[tuple[str, str], ...] = (
    ("export-bookmarks.sh", "export → data/bookmarks/bookmarks.html"),
    ("import-bookmarks.sh", "restore from data/bookmarks/bookmarks.html"),
    ("wait-download.sh", "poll Downloads for newest HTML export"),
)

TOP_LEVEL_COMMANDS: tuple[tuple[str, str], ...] = (
    ("git / g", "git shortcuts (see shuttle git --help)"),
    ("backup", "backup workflows (placeholder)"),
    ("restore", "restore workflows (placeholder)"),
    ("drives", "cloud drive sync (placeholder)"),
    ("notion", "Notion sync (placeholder)"),
    ("bookmarks", "Chrome bookmark script pointers"),
    ("links", "this index — docs, scripts, defaults"),
    ("docker", "containers/images — ps, top, df, clean (see shuttle docker --help)"),
)


def doc_entries(root: Path | None = None) -> list[CatalogEntry]:
    base = root or project_root()
    docs_dir = base / "docs"
    entries: list[CatalogEntry] = []
    readme = base / "README.md"
    if readme.is_file():
        entries.append(CatalogEntry("Root README", doc=str(readme.relative_to(base))))
    if docs_dir.is_dir():
        for path in sorted(docs_dir.rglob("*.md")):
            rel = path.relative_to(base)
            entries.append(CatalogEntry(path.stem.replace("-", " ").title(), doc=str(rel)))
    return entries


def git_script_entries(root: Path | None = None) -> list[CatalogEntry]:
    base = root or project_root()
    git_dir = base / "scripts" / "git"
    entries: list[CatalogEntry] = []
    for script_name, cli_cmd in GIT_SCRIPT_COMMANDS:
        script_path = git_dir / script_name
        rel = str(script_path.relative_to(base)) if script_path.is_file() else None
        entries.append(
            CatalogEntry(
                script_name.replace(".sh", "").replace("-", " "),
                cli=f"shuttle {cli_cmd}",
                script=rel,
                doc="docs/git.md",
            )
        )
    return entries


def chrome_script_entries(root: Path | None = None) -> list[CatalogEntry]:
    base = root or project_root()
    chrome_dir = base / "scripts" / "chrome"
    entries: list[CatalogEntry] = []
    for script_name, note in CHROME_SCRIPTS:
        script_path = chrome_dir / script_name
        rel = str(script_path.relative_to(base)) if script_path.is_file() else None
        entries.append(
            CatalogEntry(
                script_name.replace(".sh", "").replace("-", " "),
                script=rel,
                doc="docs/bookmarks.md",
                note=note,
            )
        )
    return entries
