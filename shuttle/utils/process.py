from __future__ import annotations

import subprocess
from collections.abc import Sequence


class GitCommandError(RuntimeError):
    def __init__(self, cmd: Sequence[str], returncode: int, stderr: str) -> None:
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"git command failed ({returncode}): {' '.join(self.cmd)}\n{stderr}")


def run_git(
    args: Sequence[str],
    *,
    cwd: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = ["git", *args]
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise GitCommandError(cmd, result.returncode, result.stderr.strip())
    return result


class GhCommandError(RuntimeError):
    def __init__(self, cmd: Sequence[str], returncode: int, stderr: str) -> None:
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"gh command failed ({returncode}): {' '.join(self.cmd)}\n{stderr}")


def run_gh(
    args: Sequence[str],
    *,
    cwd: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = ["gh", *args]
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise GhCommandError(cmd, result.returncode, result.stderr.strip())
    return result
