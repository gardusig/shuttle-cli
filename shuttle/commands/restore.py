import typer

restore_app = typer.Typer(help="Restore workflows (placeholder).", no_args_is_help=False)


@restore_app.callback(invoke_without_command=True)
def restore_root() -> None:
    typer.echo("restore: not implemented yet (see issue #3)")
