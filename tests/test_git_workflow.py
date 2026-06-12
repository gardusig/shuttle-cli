"""Workflow shortcuts: reset, start, push."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.git_shortcuts import GitShortcuts

runner = CliRunner()
SNAPSHOT = "shuttle.commands.git.git_worktree_snapshot"


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: main", "dirty: false"]
    return snap


@patch.object(GitShortcuts, "reset")
def test_git_reset_requires_yes(mock_reset: MagicMock) -> None:
    result = runner.invoke(app, ["git", "reset"])
    assert result.exit_code != 0
    mock_reset.assert_not_called()


@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_main_only_with_yes(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--main-only"])
    assert result.exit_code == 0
    assert "reset" in result.stdout
    mock_reset.assert_called_once_with(
        yes=True,
        keep_ignored=False,
        main_only=True,
        all_local=False,
        branch_message=".",
        discard=False,
    )


@patch.object(GitShortcuts, "start", return_value="issue-9-docker")
@patch.object(GitShortcuts, "local_branch_names", return_value=[])
def test_git_start_with_yes(
    _branches: MagicMock,
    mock_start: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "start", "issue-9-docker", "--yes"])
    assert result.exit_code == 0
    assert "started" in result.stdout
    mock_start.assert_called_once_with(
        "issue-9-docker",
        yes=True,
        keep_ignored=False,
        prep=True,
        no_push=True,
    )


@patch.object(GitShortcuts, "reset", return_value=["feat-a"])
def test_git_reset_with_yes(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes"])
    assert result.exit_code == 0
    assert "reset" in result.stdout
    mock_reset.assert_called_once_with(
        yes=True,
        keep_ignored=False,
        main_only=False,
        all_local=False,
        branch_message=".",
        discard=False,
    )


@patch.object(GitShortcuts, "reset")
def test_git_reset_all_local(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    mock_reset.return_value = ["a", "b"]
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--all-local"])
    assert result.exit_code == 0
    mock_reset.assert_called_once_with(
        yes=True,
        keep_ignored=False,
        main_only=False,
        all_local=True,
        branch_message=".",
        discard=False,
    )
