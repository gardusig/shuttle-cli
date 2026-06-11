import typer

backup_app = typer.Typer(help="Backup workflows (placeholder).", no_args_is_help=False)


@backup_app.callback(invoke_without_command=True)
def backup_root() -> None:
    """Run backup workflow (not implemented)."""
    typer.echo("backup: not implemented yet (see issue #3)")
