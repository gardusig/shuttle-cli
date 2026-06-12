#!/usr/bin/env python3
"""Integration check: shuttle docker CLI (mocked or live host daemon)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shuttle.integration.docker_integration import (  # noqa: E402
    docker_checks,
    run_all_docker_checks,
    run_live_docker_checks,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run against the host Docker daemon (requires docker + network for pull).",
    )
    args = parser.parse_args()

    if args.live:
        errors = run_live_docker_checks(ROOT)
        label = "Live docker integration"
    else:
        errors = run_all_docker_checks(ROOT)
        label = "Docker integration (mocked)"

    if errors:
        print(f"{label} failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    count = len(docker_checks()) if not args.live else "live"
    print(f"{label} passed ({count} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
