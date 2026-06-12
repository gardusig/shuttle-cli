from __future__ import annotations

import typer

from shuttle import __version__
from shuttle.commands.backup import backup_app
from shuttle.commands.bookmarks import bookmarks_app
from shuttle.commands.chrome import chrome_app
from shuttle.commands.docker import docker_app
from shuttle.commands.drive import drive_app
from shuttle.commands.gh import gh_app
from shuttle.commands.git import git_app
from shuttle.commands.links import links_app
from shuttle.commands.notion import notion_app
from shuttle.commands.restore import restore_app
from shuttle.utils.logger import setup_logging

app = typer.Typer(
    name="shuttle",
    help="Git shortcuts and drive (tag zips) for macOS. Run `shuttle links` for docs and scripts.",
    no_args_is_help=True,
)

app.add_typer(links_app, name="links")
app.add_typer(git_app, name="git")
app.add_typer(gh_app, name="gh")
app.add_typer(backup_app, name="backup", hidden=True)
app.add_typer(restore_app, name="restore")
app.add_typer(drive_app, name="drive")
app.add_typer(notion_app, name="notion")
app.add_typer(chrome_app, name="chrome")
app.add_typer(bookmarks_app, name="bookmarks", hidden=True)
app.add_typer(docker_app, name="docker")


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
        typer.echo("\nFull index: shuttle links  |  docs/README.md")
        raise typer.Exit()
    ctx.obj = {"verbose": verbose}


# Short alias: shuttle g <cmd> == shuttle git <cmd>
app.add_typer(git_app, name="g", hidden=True)
