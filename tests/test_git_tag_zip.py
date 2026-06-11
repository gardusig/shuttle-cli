"""Git tag and zip command tests."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.git_shortcuts import GitShortcuts

runner = CliRunner()
GIT_SNAPSHOT_PATCH = "shuttle.commands.git.git_worktree_snapshot"


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: main", "dirty: false"]
    return snap


@patch.object(GitShortcuts, "tag_exists_local", return_value=False)
@patch.object(GitShortcuts, "tag_exists_remote", return_value=False)
@patch.object(GitShortcuts, "remote_exists", return_value=False)
@patch.object(GitShortcuts, "create_tag")
def test_git_tag_creates_local_tag(
    mock_create: MagicMock,
    _remote: MagicMock,
    _remote_tag: MagicMock,
    _local: MagicMock,
) -> None:
    result = runner.invoke(app, ["git", "tag", "2026-06-11"])
    assert result.exit_code == 0
    assert "2026-06-11" in result.stdout
    mock_create.assert_called_once_with("2026-06-11", replace=False)


@patch.object(GitShortcuts, "tag_exists_local", return_value=True)
@patch.object(GitShortcuts, "create_tag")
def test_git_tag_replace_requires_gate(
    mock_create: MagicMock,
    _local: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "tag", "2026-06-11"])
    assert result.exit_code != 0
    mock_create.assert_not_called()


@patch.object(GitShortcuts, "tag_exists_local", return_value=True)
@patch.object(GitShortcuts, "tag_exists_remote", return_value=False)
@patch.object(GitShortcuts, "remote_exists", return_value=False)
@patch.object(GitShortcuts, "create_tag")
def test_git_tag_replace_with_yes(
    mock_create: MagicMock,
    _remote: MagicMock,
    _remote_tag: MagicMock,
    _local: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "tag", "2026-06-11", "--replace-local", "--yes"])
    assert result.exit_code == 0
    mock_create.assert_called_once_with("2026-06-11", replace=True)


@patch.object(GitShortcuts, "tag_exists_local", return_value=False)
@patch.object(GitShortcuts, "tag_exists_remote", return_value=False)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "create_tag")
@patch.object(GitShortcuts, "push_tag")
def test_git_tag_push_with_yes(
    mock_push: MagicMock,
    mock_create: MagicMock,
    _remote: MagicMock,
    _remote_tag: MagicMock,
    _local: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "tag", "2026-06-11", "--push", "--yes"])
    assert result.exit_code == 0
    mock_create.assert_called_once()
    mock_push.assert_called_once_with("2026-06-11", force=False)


@patch.object(GitShortcuts, "tag_exists_local", return_value=False)
@patch.object(GitShortcuts, "zip_tag")
def test_git_zip_requires_tag(mock_zip: MagicMock, _exists: MagicMock) -> None:
    result = runner.invoke(app, ["git", "zip", "missing-tag"])
    assert result.exit_code != 0
    assert "Tag not found" in result.stdout
    mock_zip.assert_not_called()


@patch.object(GitShortcuts, "tag_exists_local", return_value=True)
@patch.object(GitShortcuts, "zip_tag")
def test_git_zip_with_tag(mock_zip: MagicMock, _exists: MagicMock) -> None:
    def _archive(tag: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"zip")
        return dest

    mock_zip.side_effect = _archive
    result = runner.invoke(app, ["git", "zip", "2026-06-11"])
    assert result.exit_code == 0
    assert ".zip" in result.stdout
    mock_zip.assert_called_once()


def test_zip_tag_creates_archive() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
        (repo / "README.md").write_text("hi\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "tag", "-a", "2026-06-11", "-m", "2026-06-11"], check=True)
        out = repo / "out.zip"
        svc = GitShortcuts(top=str(repo))
        path = svc.zip_tag("2026-06-11", out)
        assert path.is_file()
        assert path.stat().st_size > 0
