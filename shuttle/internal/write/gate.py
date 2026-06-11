"""Write gate: summary delimiter + Q&A before mutating operations."""

from __future__ import annotations

import sys

import typer

from shuttle.internal.read.safety import OperationKind, classify_operation

WRITE_GATE_DELIMITER = "--- shuttle write gate ---"


def confirm_prompt(question: str, *, yes: bool = False) -> None:
    if yes:
        return
    if not sys.stdin.isatty():
        raise typer.Exit(
            "Refusing write in non-interactive mode. Pass --yes to proceed."
        )
    confirmed = typer.confirm(question, default=False)
    if not confirmed:
        raise typer.Exit("Aborted.")


def write_gate(
    operation: str,
    summary_lines: list[str],
    *,
    question: str,
    yes: bool = False,
    extra_lines: list[str] | None = None,
) -> None:
    """Print read snapshot delimiter, then require confirmation before write."""
    kind = classify_operation(operation)
    if kind != OperationKind.WRITE_GATED:
        return

    typer.echo(WRITE_GATE_DELIMITER)
    typer.echo(f"operation: {operation}")
    for line in summary_lines:
        typer.echo(line)
    if extra_lines:
        for line in extra_lines:
            typer.echo(line)
    typer.echo(WRITE_GATE_DELIMITER)
    confirm_prompt(question, yes=yes)


def require_write_gate(
    operation: str,
    summary_lines: list[str],
    *,
    question: str | None = None,
    yes: bool = False,
    extra_lines: list[str] | None = None,
) -> None:
    """Convenience wrapper with a default question."""
    default_question = f"Proceed with {operation.replace('-', ' ')}?"
    write_gate(
        operation,
        summary_lines,
        question=question or default_question,
        yes=yes,
        extra_lines=extra_lines,
    )
