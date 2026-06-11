"""Write-side git helpers — always call write_gate before mutating."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from shuttle.internal.read.git import GitWorktreeSnapshot, git_worktree_snapshot
from shuttle.internal.write.gate import require_write_gate
from shuttle.services.git_shortcuts import GitShortcuts

T = TypeVar("T")


def gated_git_write(
    svc: GitShortcuts,
    operation: str,
    fn: Callable[[], T],
    *,
    yes: bool = False,
    question: str | None = None,
    extra_lines: list[str] | None = None,
) -> T:
    """Run read inventory, show write gate, then execute mutation."""
    snapshot = git_worktree_snapshot(svc)
    require_write_gate(
        operation,
        snapshot.summary_lines(),
        question=question,
        yes=yes,
        extra_lines=extra_lines,
    )
    return fn()


def read_git_snapshot(svc: GitShortcuts) -> GitWorktreeSnapshot:
    """Read-only worktree snapshot (no gate)."""
    return git_worktree_snapshot(svc)
