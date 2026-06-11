import typer

drives_app = typer.Typer(help="Cloud drive sync (placeholder).", no_args_is_help=False)


@drives_app.callback(invoke_without_command=True)
def drives_root() -> None:
    typer.echo("drives: not implemented yet (see issue #3)")
