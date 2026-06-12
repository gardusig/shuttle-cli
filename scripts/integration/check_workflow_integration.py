#!/usr/bin/env python3
"""Integration check: start, push, and reset workflow scenarios."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shuttle.integration.workflow_integration import (  # noqa: E402
    WORKFLOW_CHECKS,
    prepare_workflow_git,
    run_all_workflow_checks,
)

SCRATCH = ROOT / ".integration-scratch"


def main() -> int:
    SCRATCH.mkdir(exist_ok=True)
    git_dir = Path(tempfile.mkdtemp(prefix="shuttle-workflow-", dir=SCRATCH))
    errors: list[str] = []
    try:
        prepare_workflow_git(git_dir)
        errors = run_all_workflow_checks(ROOT, git_dir)
    finally:
        shutil.rmtree(git_dir, ignore_errors=True)
        shutil.rmtree(git_dir.parent / f"{git_dir.name}-origin.git", ignore_errors=True)
    if errors:
        print("Workflow integration failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    count = len(WORKFLOW_CHECKS)
    print(f"Workflow integration passed ({count} scenarios).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
