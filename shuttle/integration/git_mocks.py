"""Mock remote git network calls during integration CLI checks."""

from __future__ import annotations

import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

from shuttle.utils import process as process_mod

# Subcommands that contact remotes (fetch/push/ls-remote). Local git still runs for everything else.
_REMOTE_SUBCOMMANDS = frozenset({"fetch", "push", "ls-remote"})


def _is_remote_git_call(args: tuple[str, ...] | list[str]) -> bool:
    return bool(args) and args[0] in _REMOTE_SUBCOMMANDS


def _mock_remote_result(args: tuple[str, ...] | list[str]) -> subprocess.CompletedProcess[str]:
    stdout = ""
    if args[0] == "ls-remote":
        # Pretend no remote tags unless integration setup pushed them for real.
        stdout = ""
    return subprocess.CompletedProcess(
        args=["git", *args],
        returncode=0,
        stdout=stdout,
        stderr="",
    )


@contextmanager
def patch_remote_git() -> Generator[None, None, None]:
    """Prevent integration tests from performing real fetch/push/ls-remote."""
    real_run_git = process_mod.run_git

    def wrapper(
        args: Any,
        *,
        cwd: str | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        seq = tuple(args)
        if _is_remote_git_call(seq):
            result = _mock_remote_result(seq)
            if check and result.returncode != 0:
                raise process_mod.GitCommandError(result.args, result.returncode, result.stderr)
            return result
        return real_run_git(args, cwd=cwd, check=check)

    # Patch every module that binds run_git at import time.
    targets = (
        "shuttle.utils.process.run_git",
        "shuttle.services.git_shortcuts.run_git",
    )
    with patch(targets[0], side_effect=wrapper), patch(targets[1], side_effect=wrapper):
        yield
