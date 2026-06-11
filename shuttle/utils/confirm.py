"""Confirmation gates — prefer shuttle.internal.write.gate for new code."""

from __future__ import annotations

from shuttle.internal.write.gate import confirm_prompt, require_write_gate, write_gate

__all__ = ["require_confirmation", "require_write_gate", "write_gate"]


def require_confirmation(
    message: str,
    *,
    yes: bool = False,
    default_no: bool = True,
) -> None:
    """Simple confirm without inventory delimiter (prefer require_write_gate)."""
    del default_no  # always default No via confirm_prompt
    confirm_prompt(message, yes=yes)
