"""Chrome browser integrations (bookmarks today; more later)."""

from __future__ import annotations

import os
import subprocess

import typer
from rich import print as rprint

from shuttle.utils.config import bookmarks_file_path, chrome_downloads_dir, project_root

chrome_app = typer.Typer(help="Chrome browser — bookmarks and future integrations.", no_args_is_help=True)
bookmarks_app = typer.Typer(help="Bookmark ingest / deploy (local-centric).", no_args_is_help=True)


def _bookmarks_env() -> dict[str, str]:
    env = os.environ.copy()
    env["SHUTTLE_ROOT"] = str(project_root())
    env["SHUTTLE_BOOKMARKS_FILE"] = str(bookmarks_file_path())
    env["SHUTTLE_DOWNLOADS_DIR"] = str(chrome_downloads_dir())
    return env


def _run_bookmarks_script(name: str) -> None:
    script = project_root() / "scripts" / "chrome" / name
    if not script.is_file():
        raise typer.Exit(f"Script not found: {script}")
    try:
        subprocess.run([str(script)], env=_bookmarks_env(), check=True)
    except subprocess.CalledProcessError as exc:
        raise typer.Exit(exc.returncode) from exc


def bookmarks_ingest_from_chrome() -> None:
    """Chrome → local: ingest bookmarks HTML into configured path."""
    dest = bookmarks_file_path()
    _run_bookmarks_script("export-bookmarks.sh")
    rprint(f"[green]ingested[/green] → {dest}")


def bookmarks_deploy_to_chrome() -> None:
    """Local → Chrome: deploy backup file into Chrome."""
    src = bookmarks_file_path()
    if not src.is_file():
        raise typer.Exit(
            f"Backup not found: {src}\nRun `shuttle chrome bookmarks ingest` first."
        )
    _run_bookmarks_script("import-bookmarks.sh")
    rprint(f"[green]deployed[/green] to Chrome from {src}")


@bookmarks_app.command("ingest")
def bookmarks_ingest_cmd() -> None:
    """Chrome → local: ingest bookmarks HTML to configured path."""
    bookmarks_ingest_from_chrome()


@bookmarks_app.command("deploy")
def bookmarks_deploy_cmd() -> None:
    """Local → Chrome: deploy backup into Chrome."""
    bookmarks_deploy_to_chrome()


@bookmarks_app.command("import", hidden=True)
def legacy_import_cmd() -> None:
    """Deprecated: remote-centric local→Chrome; use `shuttle chrome bookmarks deploy`."""
    bookmarks_deploy_to_chrome()


@bookmarks_app.command("export", hidden=True)
def legacy_export_cmd() -> None:
    """Deprecated: remote-centric Chrome→local; use `shuttle chrome bookmarks ingest`."""
    bookmarks_ingest_from_chrome()


chrome_app.add_typer(bookmarks_app, name="bookmarks")
