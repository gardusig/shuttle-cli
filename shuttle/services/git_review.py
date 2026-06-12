"""Workspace health checks (cursor-skills @git-review analogue)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from shuttle.utils.config import project_root


def run_review(*, install: bool = True, quick: bool = False) -> int:
    """Syntax-check shell scripts; full mode runs ./scripts/test-unit.sh (Docker, not host pytest)."""
    root = project_root()
    if install and not (root / ".venv" / "bin" / "python").exists():
        subprocess.run(["./scripts/bootstrap.sh"], cwd=root, check=True)

    shell_dirs = [
        root / "scripts",
        root / "scripts" / "chrome",
        root / "scripts" / "git",
        root / "scripts" / "docker",
        root / "scripts" / "integration",
    ]
    for directory in shell_dirs:
        if not directory.is_dir():
            continue
        for script in sorted(directory.glob("*.sh")):
            subprocess.run(["bash", "-n", str(script)], check=True)

    if quick:
        return 0

    result = subprocess.run(["./scripts/test-unit.sh"], cwd=root)
    return result.returncode
