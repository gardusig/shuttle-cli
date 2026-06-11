"""Workspace health checks (cursor-skills @git-review analogue)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from shuttle.utils.config import project_root


def run_review(*, install: bool = True, quick: bool = False) -> int:
    """Bootstrap if needed, syntax-check shell scripts, optionally run pytest."""
    root = project_root()
    venv_python = root / ".venv" / "bin" / "python"
    if install and not venv_python.exists():
        subprocess.run(["./scripts/bootstrap.sh"], cwd=root, check=True)

    shell_dirs = [
        root / "scripts",
        root / "scripts" / "chrome",
        root / "scripts" / "git",
        root / "scripts" / "integration",
    ]
    for directory in shell_dirs:
        if not directory.is_dir():
            continue
        for script in sorted(directory.glob("*.sh")):
            subprocess.run(["bash", "-n", str(script)], check=True)

    if quick:
        return 0

    if not venv_python.exists():
        raise RuntimeError("Python venv missing after bootstrap")

    pytest = subprocess.run(
        [str(venv_python), "-m", "pytest", "-q"],
        cwd=root,
    )
    return pytest.returncode
