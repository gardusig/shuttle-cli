import typer

notion_app = typer.Typer(help="Notion sync (placeholder).", no_args_is_help=False)


@notion_app.callback(invoke_without_command=True)
def notion_root() -> None:
    typer.echo("notion: not implemented yet (see issue #3)")
