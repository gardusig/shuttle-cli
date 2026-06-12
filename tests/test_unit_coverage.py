"""Unit tests for coverage gaps outside integration packages."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.commands.git import _branch_preview_lines
from shuttle.internal.read.safety import OperationKind, classify_operation
from shuttle.services.git_shortcuts import GitShortcuts

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()
PATCH = "shuttle.services.git_shortcuts.run_git"
SNAPSHOT = "shuttle.commands.git.git_worktree_snapshot"


def test_package_main_entrypoint() -> None:
    """shuttle.__main__ runs the Typer app (python -m shuttle)."""
    result = subprocess.run(
        [sys.executable, "-m", "shuttle", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "git" in result.stdout


def test_branch_preview_lines_truncates() -> None:
    branches = [f"branch-{i}" for i in range(25)]
    lines = _branch_preview_lines("preview", branches, limit=3)
    assert lines[0] == "preview: 25"
    assert lines[1] == "  - branch-0"
    assert any("more)" in line for line in lines)


def test_classify_unknown_operation_is_gated() -> None:
    assert classify_operation("novel-op") == OperationKind.WRITE_GATED


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: feat", "dirty: true"]
    return snap


@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_main_only_message(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--main-only"])
    assert result.exit_code == 0
    assert "synced with remote" in result.stdout


@patch.object(GitShortcuts, "reset", return_value=["a"])
def test_git_reset_prune_message(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes"])
    assert "removed 1 branch" in result.stdout


@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "current_branch", return_value="feat")
@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_discard_intent(
    _reset: MagicMock,
    _branch: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--discard"])
    assert result.exit_code == 0
    assert "discard uncommitted" in result.stdout


@patch.object(GitShortcuts, "branch_delete")
def test_git_branch_delete_action(
    mock_delete: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "branch", "delete", "old", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.stdout
    mock_delete.assert_called_once()


@patch("shuttle.utils.process.run_git")
def test_git_branch_rename(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    result = runner.invoke(app, ["git", "branch", "rename", "--rename", "new-name"])
    assert result.exit_code == 0
    assert "renamed" in result.stdout


@patch.object(GitShortcuts, "push")
@patch.object(GitShortcuts, "start", return_value="feat-push")
def test_git_start_no_prep_with_push(mock_start: MagicMock, mock_push: MagicMock) -> None:
    result = runner.invoke(
        app,
        ["git", "start", "feat-push", "--no-prep", "--push", "--yes"],
    )
    assert result.exit_code == 0
    mock_start.assert_called_once_with(
        "feat-push",
        yes=True,
        keep_ignored=False,
        prep=False,
        no_push=False,
    )


@patch.object(GitShortcuts, "stash_pop")
@patch.object(GitShortcuts, "stash_apply")
def test_git_stash_apply_and_pop(mock_apply: MagicMock, mock_pop: MagicMock) -> None:
    apply_result = runner.invoke(app, ["git", "stash", "apply", "--index", "1"])
    assert apply_result.exit_code == 0
    mock_apply.assert_called_once_with(1)
    pop_result = runner.invoke(app, ["git", "stash", "pop", "--index", "2"])
    assert pop_result.exit_code == 0
    mock_pop.assert_called_once_with(2)


@patch(PATCH)
def test_reset_all_local_deletes_every_branch(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    svc = GitShortcuts(top="/tmp/repo")
    with (
        patch.object(svc, "_prepare_leave_branch"),
        patch.object(svc, "sync_main"),
        patch.object(svc, "local_branch_names", return_value=["a", "b"]),
    ):
        deleted = svc.reset(yes=True, all_local=True)
    assert deleted == ["a", "b"]
    assert mock_run.call_count == 2


@patch(PATCH)
def test_sync_main_fallback_when_pull_fails(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        MagicMock(returncode=1, stdout="", stderr=""),  # pull --ff-only fails
        MagicMock(returncode=0, stdout="", stderr=""),  # rev-parse
        MagicMock(returncode=0, stdout="", stderr=""),  # reset --hard
        MagicMock(returncode=0, stdout="", stderr=""),  # clean
    ]
    svc = GitShortcuts(top="/tmp/repo")
    with (
        patch.object(svc, "is_dirty", return_value=False),
        patch.object(svc, "checkout_main"),
        patch.object(svc, "fetch_all"),
        patch.object(svc, "has_upstream", return_value=True),
        patch.object(svc, "canonical_main_ref", return_value="origin/main"),
    ):
        svc.sync_main(yes=True, keep_ignored=True)
    assert ["reset", "--hard", "origin/main"] in [c.args[0] for c in mock_run.call_args_list]
