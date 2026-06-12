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
        "scripts/docker/common.sh",
        "scripts/docker/build-image.sh",
        "scripts/docker/run-unit.sh",
        "scripts/docker/run-integration.sh",
        "scripts/test-unit.sh",
        "scripts/test-integration.sh",
        "scripts/integration/smoke.sh",
        "scripts/integration/check_public_commands.py",
        "scripts/integration/check_public_endpoints.py",
        "scripts/integration/check_docker_commands.py",
    ):
        path = ROOT / rel
        assert path.exists(), f"missing {rel}"
        assert path.stat().st_size > 0, f"empty {rel}"


def test_docker_harness_mentions_readonly_mount() -> None:
    common = (ROOT / "scripts/docker/common.sh").read_text()
    bootstrap = (ROOT / "scripts/bootstrap.sh").read_text()
    assert ":ro" in common
    assert "/tmp/shuttle-cli" in common
    assert "--exclude='.git'" in common
    assert "--exclude='.venv'" in common
    assert "SHUTTLE_DOCKER_SKIP_BUILD" in common
    assert "docker.sock" in common
    assert "SHUTTLE_BOOTSTRAP_DEV" in bootstrap


def test_ci_workflow_runs_on_pull_request_with_both_jobs() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text()
    assert "pull_request:" in workflow
    assert "unit:" in workflow or "name: Unit tests" in workflow
    assert "integration:" in workflow or "name: Integration tests" in workflow
    assert "test-unit.sh" in workflow
    assert "test-integration.sh" in workflow
    assert "shuttle-cli:dev" in workflow


def test_docker_smoke_runs_public_command_checker() -> None:
    smoke = (ROOT / "scripts/integration/smoke.sh").read_text()
    assert "check_public_commands.py" in smoke
    assert "SHUTTLE_SKIP_CHROME_AUTOMATION=1" in smoke


def test_ci_workflow_runs_live_docker_in_container() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text()
    assert "test-integration.sh" in workflow
    assert "setup-python" not in workflow
    assert "bootstrap.sh" not in workflow


def test_public_command_registry_covers_all_commands() -> None:
    from shuttle.integration.public_commands import assert_public_command_registry_complete

    assert_public_command_registry_complete()


@pytest.mark.integration
def test_run_docker_unit_when_enabled() -> None:
    if os.environ.get("SHUTTLE_RUN_DOCKER_TESTS") != "1":
        pytest.skip("set SHUTTLE_RUN_DOCKER_TESTS=1 to run Docker unit harness")
    if shutil.which("docker") is None:
        pytest.skip("docker is not installed")

    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "test-unit.sh")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
def test_run_docker_integration_when_enabled() -> None:
    if os.environ.get("SHUTTLE_RUN_DOCKER_TESTS") != "1":
        pytest.skip("set SHUTTLE_RUN_DOCKER_TESTS=1 to run Docker integration")
    if shutil.which("docker") is None:
        pytest.skip("docker is not installed")

    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "test-integration.sh")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
