"""Registry and mocked integration checks for shuttle docker commands."""

from __future__ import annotations

from shuttle.integration.docker_integration import (
    DOCKER_SUBCOMMANDS,
    assert_every_docker_subcommand_has_ok_check,
    docker_checks,
    run_all_docker_checks,
)
from shuttle.integration.public_commands import assert_public_command_registry_complete

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_docker_subcommands_have_checks() -> None:
    assert_public_command_registry_complete()
    covered = {c.args[1] for c in docker_checks() if len(c.args) >= 2}
    assert set(DOCKER_SUBCOMMANDS) <= covered
    assert_every_docker_subcommand_has_ok_check()


def test_mocked_docker_integration_passes() -> None:
    errors = run_all_docker_checks(ROOT)
    assert errors == [], "\n---\n".join(errors)
