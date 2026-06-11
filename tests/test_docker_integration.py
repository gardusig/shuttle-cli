"""Docker integration harness checks for issue #9."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_docker_harness_files_exist() -> None:
    for rel in (
        "Dockerfile",
        ".dockerignore",
        "scripts/test-in-docker.sh",
        "scripts/integration/smoke.sh",
        "scripts/integration/check_public_endpoints.py",
    ):
        path = ROOT / rel
        assert path.exists(), f"missing {rel}"
        assert path.stat().st_size > 0, f"empty {rel}"


def test_docker_harness_mentions_readonly_mount() -> None:
    runner = (ROOT / "scripts" / "test-in-docker.sh").read_text()
    assert ":ro" in runner
    assert "/tmp/shuttle-cli" in runner
    assert "--exclude='.git'" in runner
    assert "--exclude='.venv'" in runner
    assert "SHUTTLE_DOCKER_SKIP_BUILD" in runner


def test_ci_workflow_runs_on_pull_request_with_both_jobs() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text()
    assert "pull_request:" in workflow
    assert "unit:" in workflow or "name: Unit tests" in workflow
    assert "integration:" in workflow or "name: Integration tests" in workflow
    assert "test-in-docker.sh" in workflow
    assert "pytest" in workflow


def test_docker_smoke_runs_public_endpoint_checker() -> None:
    smoke = (ROOT / "scripts" / "integration" / "smoke.sh").read_text()
    assert "check_public_endpoints.py" in smoke
    assert "SHUTTLE_SKIP_CHROME_AUTOMATION=1" in smoke


def test_public_endpoint_registry_covers_all_git_commands() -> None:
    from shuttle.integration.public_endpoints import (
        assert_every_git_subcommand_checked,
        assert_every_top_level_command_checked,
        assert_registry_covers_git_commands,
    )

    assert_registry_covers_git_commands()
    assert_every_git_subcommand_checked()
    assert_every_top_level_command_checked()


@pytest.mark.integration
def test_run_docker_integration_when_enabled() -> None:
    if os.environ.get("SHUTTLE_RUN_DOCKER_TESTS") != "1":
        pytest.skip("set SHUTTLE_RUN_DOCKER_TESTS=1 to run Docker integration")
    if shutil.which("docker") is None:
        pytest.skip("docker is not installed")

    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "test-in-docker.sh")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
