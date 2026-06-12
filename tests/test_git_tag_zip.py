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


@patch("shuttle.commands.git._reconcile_tag_push")
@patch.object(GitShortcuts, "prepare_for_tag")
@patch.object(GitShortcuts, "tag_exists_local", return_value=False)
@patch.object(GitShortcuts, "create_tag")
def test_git_tag_creates_and_pushes(
    mock_create: MagicMock,
    _local: MagicMock,
    mock_prepare: MagicMock,
    mock_push: MagicMock,
) -> None:
    result = runner.invoke(app, ["git", "tag", "2026-06-11"])
    assert result.exit_code == 0
    assert "2026-06-11" in result.stdout
    mock_prepare.assert_called_once_with(yes=False)
    mock_create.assert_called_once_with("2026-06-11", replace=False)
    mock_push.assert_called_once()


@patch("shuttle.commands.git._reconcile_tag_push")
@patch.object(GitShortcuts, "prepare_for_tag")
@patch.object(GitShortcuts, "tag_exists_local", return_value=True)
@patch.object(GitShortcuts, "create_tag")
def test_git_tag_replace_requires_gate(
    mock_create: MagicMock,
    _local: MagicMock,
    mock_prepare: MagicMock,
    _push: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "tag", "2026-06-11"])
    assert result.exit_code != 0
    mock_create.assert_not_called()


@patch("shuttle.commands.git._reconcile_tag_push")
@patch.object(GitShortcuts, "prepare_for_tag")
@patch.object(GitShortcuts, "tag_exists_local", return_value=True)
@patch.object(GitShortcuts, "create_tag")
def test_git_tag_replace_with_yes(
    mock_create: MagicMock,
    _local: MagicMock,
    mock_prepare: MagicMock,
    _push: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "tag", "2026-06-11", "--yes"])
    assert result.exit_code == 0
    mock_create.assert_called_once_with("2026-06-11", replace=True)


@patch.object(GitShortcuts, "list_local_tags", return_value=["2026-06-10", "2026-06-11"])
@patch.object(GitShortcuts, "list_remote_tags", return_value=["2026-06-10"])
def test_git_tag_list(_remote: MagicMock, _local: MagicMock) -> None:
    result = runner.invoke(app, ["git", "tag", "list"])
    assert result.exit_code == 0
    assert "Local tags" in result.stdout
    assert "Remote tags" in result.stdout
    assert "2026-06-11" in result.stdout


@patch.object(GitShortcuts, "tag_push_action", return_value="push")
@patch.object(GitShortcuts, "push_tag")
def test_git_tag_push(mock_push: MagicMock, _action: MagicMock, snapshot: MagicMock) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "tag", "push", "2026-06-11", "--yes"])
    assert result.exit_code == 0
    assert "pushed" in result.stdout
    mock_push.assert_called_once_with("2026-06-11", force=False)


@patch.object(GitShortcuts, "tag_push_action", return_value="skip")
@patch.object(GitShortcuts, "push_tag")
def test_git_tag_push_skip(mock_push: MagicMock, _action: MagicMock) -> None:
    result = runner.invoke(app, ["git", "tag", "push", "2026-06-11", "--yes"])
    assert result.exit_code == 0
    assert "skip" in result.stdout
    mock_push.assert_not_called()


@patch.object(GitShortcuts, "tag_push_action", return_value="no-remote")
@patch.object(GitShortcuts, "push_tag")
def test_git_tag_push_no_remote(mock_push: MagicMock, _action: MagicMock) -> None:
    result = runner.invoke(app, ["git", "tag", "push", "2026-06-11", "--yes"])
    assert result.exit_code == 0
    assert "no origin" in result.stdout.lower()
    mock_push.assert_not_called()


@patch.object(GitShortcuts, "tag_push_action", return_value="force")
@patch.object(GitShortcuts, "push_tag")
def test_git_tag_push_force(mock_push: MagicMock, _action: MagicMock, snapshot: MagicMock) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "tag", "push", "2026-06-11", "--yes"])
    assert result.exit_code == 0
    assert "force-pushed" in result.stdout
    mock_push.assert_called_once_with("2026-06-11", force=True)


@patch.object(GitShortcuts, "tag_push_action", return_value="missing-local")
def test_git_tag_push_missing_local(_action: MagicMock) -> None:
    result = runner.invoke(app, ["git", "tag", "push", "missing", "--yes"])
    assert result.exit_code != 0
    assert "Tag not found" in result.stdout


@patch.object(GitShortcuts, "prepare_for_tag", side_effect=RuntimeError("dirty tree"))
def test_git_tag_prepare_failure(mock_prepare: MagicMock) -> None:
    result = runner.invoke(app, ["git", "tag", "2026-06-12"])
    assert result.exit_code != 0
    assert "dirty tree" in result.stdout
    mock_prepare.assert_called_once()


@patch.object(GitShortcuts, "tag_exists_local", return_value=False)
@patch.object(GitShortcuts, "zip_tag")
def test_git_zip_requires_tag(mock_zip: MagicMock, _exists: MagicMock) -> None:
    result = runner.invoke(app, ["git", "zip", "missing-tag"])
    assert result.exit_code != 0
    assert "Tag not found" in result.stdout
    mock_zip.assert_not_called()


@patch.object(GitShortcuts, "tag_exists_local", return_value=True)
@patch.object(GitShortcuts, "repo_basename", return_value="repo")
@patch.object(GitShortcuts, "zip_tag")
def test_git_zip_with_tag(
    mock_zip: MagicMock,
    _basename: MagicMock,
    _exists: MagicMock,
    tmp_path: Path,
) -> None:
    dest = tmp_path / "repo-2026-06-11.zip"

    def _archive(tag: str, out: Path) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"zip")
        return out

    mock_zip.side_effect = _archive
    with patch("shuttle.commands.git.default_zip_path", return_value=dest):
        result = runner.invoke(app, ["git", "zip", "2026-06-11"])
    assert result.exit_code == 0
    assert ".zip" in result.stdout
    mock_zip.assert_called_once()


@pytest.mark.requires_git
def test_prepare_for_tag_commits_dirty_feature_work_before_sync() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
        (repo / "README.md").write_text("main\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "main"], check=True, capture_output=True)
        main_sha = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "main"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(["git", "-C", str(repo), "checkout", "-b", "feature"], check=True, capture_output=True)
        (repo / "wip.txt").write_text("uncommitted\n", encoding="utf-8")

        svc = GitShortcuts(top=str(repo))
        svc.prepare_for_tag(yes=True)

        assert svc.current_branch() == "main"
        assert svc.head_sha() == main_sha
        feature_tip = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "feature"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{feature_tip}:wip.txt"],
            capture_output=True,
        ).returncode == 0


@pytest.mark.requires_git
def test_prepare_for_tag_aligns_feature_branch_to_main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
        (repo / "README.md").write_text("main\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "main"], check=True, capture_output=True)
        main_sha = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "main"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(["git", "-C", str(repo), "checkout", "-b", "feature"], check=True, capture_output=True)
        (repo / "feature.txt").write_text("wip\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "feature.txt"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "feature"], check=True, capture_output=True)

        svc = GitShortcuts(top=str(repo))
        svc.prepare_for_tag(yes=True)

        assert svc.current_branch() == "main"
        assert svc.head_sha() == main_sha


@pytest.mark.requires_git
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


@pytest.mark.requires_git
def test_tag_push_action_states() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
        (repo / "README.md").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "tag", "-a", "v1", "-m", "v1"], check=True)
        svc = GitShortcuts(top=str(repo))
        assert svc.tag_push_action("v1") == "no-remote"
        assert svc.tag_push_action("missing") == "missing-local"
