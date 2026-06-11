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


def test_docker_smoke_uses_isolated_bookmark_paths() -> None:
    smoke = (ROOT / "scripts" / "integration" / "smoke.sh").read_text()
    assert "mktemp -d" in smoke
    assert "SHUTTLE_SKIP_CHROME_AUTOMATION=1" in smoke
    assert "SHUTTLE_DOWNLOADS_DIR" in smoke
    assert "python -m shuttle git start smoke-branch" in smoke


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
