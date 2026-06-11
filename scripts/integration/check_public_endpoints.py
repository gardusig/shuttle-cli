#!/usr/bin/env python3
"""Integration check: invoke every public shuttle CLI endpoint."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shuttle.integration.public_endpoints import (  # noqa: E402
    endpoint_checks,
    prepare_git_repo,
    run_all_endpoint_checks,
)

SCRATCH = ROOT / ".integration-scratch"


def main() -> int:
    SCRATCH.mkdir(exist_ok=True)
    git_dir = Path(tempfile.mkdtemp(prefix="shuttle-git-", dir=SCRATCH))
    errors: list[str] = []
    try:
        prepare_git_repo(git_dir)
        errors = run_all_endpoint_checks(ROOT, git_root=git_dir)
    finally:
        shutil.rmtree(git_dir, ignore_errors=True)
        shutil.rmtree(git_dir.parent / f"{git_dir.name}-origin.git", ignore_errors=True)
    if errors:
        print("Public endpoint integration failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    count = len(endpoint_checks())
    print(f"Public endpoint integration passed ({count} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
