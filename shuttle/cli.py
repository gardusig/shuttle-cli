from __future__ import annotations

import typer

from shuttle import __version__
from shuttle.commands.backup import backup_app
from shuttle.commands.bookmarks import bookmarks_app
from shuttle.commands.drives import drives_app
from shuttle.commands.git import git_app
from shuttle.commands.notion import notion_app
from shuttle.commands.restore import restore_app
from shuttle.utils.logger import setup_logging

app = typer.Typer(
    name="shuttle",
    help="Git shortcuts, backups, and sync workflows for macOS.",
    no_args_is_help=True,
)

app.add_typer(git_app, name="git")
app.add_typer(backup_app, name="backup")
app.add_typer(restore_app, name="restore")
app.add_typer(drives_app, name="drives")
app.add_typer(notion_app, name="notion")
app.add_typer(bookmarks_app, name="bookmarks")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit."),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    setup_logging(verbose=verbose)
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None and not version:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    ctx.obj = {"verbose": verbose}


# Short alias: shuttle g <cmd> == shuttle git <cmd>
app.add_typer(git_app, name="g", hidden=True)
