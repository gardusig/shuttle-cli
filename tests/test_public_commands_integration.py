"""Every public CLI command must pass dockerized integration (registry + execution)."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from shuttle.integration.docker_integration import (
    DOCKER_SUBCOMMANDS,
    docker_subcommands_with_ok_check,
)
from shuttle.integration.public_commands import (
    assert_public_command_registry_complete,
    registered_top_level_commands,
    run_all_public_command_checks,
)
from shuttle.integration.public_endpoints import (
    TOP_LEVEL_COMMANDS,
    git_subcommands_with_ok_check,
    prepare_git_repo,
)

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".integration-scratch"


def test_top_level_commands_match_cli_registration() -> None:
    assert registered_top_level_commands() == set(TOP_LEVEL_COMMANDS)


def test_public_command_registry_is_complete() -> None:
    assert_public_command_registry_complete()
    assert git_subcommands_with_ok_check()  # exercised inside assert
    assert docker_subcommands_with_ok_check() == set(DOCKER_SUBCOMMANDS)


def test_docker_smoke_runs_public_command_checker() -> None:
    smoke = (ROOT / "scripts" / "integration" / "smoke.sh").read_text()
    assert "check_public_commands.py" in smoke


def test_docker_harness_includes_public_command_checker() -> None:
    path = ROOT / "scripts" / "integration" / "check_public_commands.py"
    assert path.is_file() and path.stat().st_size > 0


@pytest.mark.integration
def test_all_public_commands_in_dockerized_integration() -> None:
    SCRATCH.mkdir(exist_ok=True)
    git_dir = Path(tempfile.mkdtemp(prefix="shuttle-public-", dir=SCRATCH))
    try:
        prepare_git_repo(git_dir)
        errors = run_all_public_command_checks(ROOT, git_root=git_dir)
    finally:
        shutil.rmtree(git_dir, ignore_errors=True)
        shutil.rmtree(git_dir.parent / f"{git_dir.name}-origin.git", ignore_errors=True)
    assert errors == [], "\n---\n".join(errors)
