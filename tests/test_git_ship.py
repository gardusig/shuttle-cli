"""Tests for shuttle git ship (add + commit + push shortcut)."""

from __future__ import annotations

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
    snap.summary_lines.return_value = ["branch: feat-x", "dirty: true"]
    return snap


@patch.object(GitShortcuts, "push")
def test_git_ship_requires_yes(mock_push: MagicMock) -> None:
    result = runner.invoke(app, ["git", "ship"])
    assert result.exit_code != 0
    mock_push.assert_not_called()


@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "current_branch", return_value="feat-x")
@patch.object(GitShortcuts, "push")
def test_git_ship_with_yes(
    mock_push: MagicMock,
    _branch: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "ship", "--yes", "-m", "wip"])
    assert result.exit_code == 0
    assert "shipped" in result.stdout
    assert "intent: git add -A" in result.stdout
    assert "branch: feat-x" in result.stdout
    mock_push.assert_called_once_with(allow_main=False, message="wip", yes=True)


@patch.object(GitShortcuts, "push")
def test_git_ship_shows_write_gate(mock_push: MagicMock, snapshot: MagicMock) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "ship", "--yes"])
    assert result.exit_code == 0
    assert "--- shuttle write gate ---" in result.stdout
    assert "operation: ship" in result.stdout
    mock_push.assert_called_once()
