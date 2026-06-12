"""Tests for shuttle git push (add + commit + push shortcut)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.commands.git import _push_plan
from shuttle.services.git_shortcuts import GitShortcuts

runner = CliRunner()
GIT_SNAPSHOT_PATCH = "shuttle.commands.git.git_worktree_snapshot"


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: feat-x", "dirty: true"]
    return snap


def test_push_plan_on_main_starts_branch_first() -> None:
    svc = MagicMock()
    svc.current_branch.return_value = "main"
    svc.local_branch_names.return_value = []
    svc.is_dirty.return_value = True
    svc.remote_exists.return_value = True
    question, lines = _push_plan(svc, "wip", allow_main=False)
    assert question.startswith("Start 'wip-")
    assert "commit, and push to origin?" in question
    assert any(line.startswith("target_branch: wip-") for line in lines)
    assert "from_branch: main" in lines


def test_push_plan_on_feature_branch() -> None:
    svc = MagicMock()
    svc.current_branch.return_value = "feat-x"
    svc.is_dirty.return_value = False
    svc.remote_exists.return_value = True
    question, lines = _push_plan(svc, ".", allow_main=False)
    assert question == "Commit and push 'feat-x' to origin?"
    assert "branch: feat-x" in lines


@patch.object(GitShortcuts, "push")
def test_git_push_requires_yes(mock_push: MagicMock) -> None:
    result = runner.invoke(app, ["git", "push"])
    assert result.exit_code != 0
    mock_push.assert_not_called()


@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "current_branch", return_value="feat-x")
@patch.object(GitShortcuts, "push", return_value="feat-x")
def test_git_push_with_yes(
    mock_push: MagicMock,
    _branch: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes", "-m", "wip"])
    assert result.exit_code == 0
    assert "pushed" in result.stdout
    assert "intent: git add -A" in result.stdout
    assert "branch: feat-x" in result.stdout
    mock_push.assert_called_once_with(allow_main=False, message="wip", yes=True)


@patch.object(GitShortcuts, "current_branch", return_value="main")
@patch.object(GitShortcuts, "local_branch_names", return_value=[])
@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "push", return_value="wip-260611-001")
def test_git_push_on_main_starts_first(
    mock_push: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    _branches: MagicMock,
    _current: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes", "-m", "wip"])
    assert result.exit_code == 0
    assert "target_branch: wip-" in result.stdout
    assert "from_branch: main" in result.stdout
    assert "intent: start 'wip-" in result.stdout
    assert "Push changes from 'main'" not in result.stdout
    mock_push.assert_called_once_with(allow_main=False, message="wip", yes=True)


@patch.object(GitShortcuts, "push", return_value="feat-x")
def test_git_push_shows_write_gate(mock_push: MagicMock, snapshot: MagicMock) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes"])
    assert result.exit_code == 0
    assert "--- shuttle write gate ---" in result.stdout
    assert "operation: push" in result.stdout
    mock_push.assert_called_once()
