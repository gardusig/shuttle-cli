import typer

bookmarks_app = typer.Typer(help="Chrome bookmarks sync (placeholder).", no_args_is_help=False)


@bookmarks_app.callback(invoke_without_command=True)
def bookmarks_root() -> None:
    typer.echo("bookmarks: use scripts/chrome/export-bookmarks.sh and import-bookmarks.sh (issue #1)")
