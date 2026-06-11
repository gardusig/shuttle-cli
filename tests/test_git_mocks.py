"""Tests for integration remote git mocking."""

from __future__ import annotations

import subprocess

from shuttle.integration.git_mocks import patch_remote_git
from shuttle.utils import process as process_mod


def test_patch_remote_git_blocks_push() -> None:
    with patch_remote_git():
        result = process_mod.run_git(["push", "origin", "main"], check=True)
    assert result.returncode == 0
    assert result.stdout == ""


def test_patch_remote_git_blocks_fetch() -> None:
    with patch_remote_git():
        result = process_mod.run_git(["fetch", "origin"], check=True)
    assert result.returncode == 0


def test_patch_remote_git_blocks_ls_remote() -> None:
    with patch_remote_git():
        result = process_mod.run_git(["ls-remote", "origin"], check=True)
    assert result.returncode == 0


def test_patch_remote_git_allows_local_status(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    with patch_remote_git():
        result = process_mod.run_git(["status", "--short"], cwd=str(repo), check=True)
    assert result.returncode == 0
