"""Internal read/write gate tests."""

from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.internal.read.git import git_worktree_snapshot
from shuttle.internal.read.safety import OperationKind, classify_operation
from shuttle.internal.write.gate import WRITE_GATE_DELIMITER, write_gate
from shuttle.services.git_shortcuts import GitShortcuts

runner = CliRunner()


def test_classify_read_operations() -> None:
    assert classify_operation("review") == OperationKind.READ
    assert classify_operation("docs") == OperationKind.READ


def test_classify_write_safe_operations() -> None:
    assert classify_operation("commit") == OperationKind.WRITE_SAFE
    assert classify_operation("start") == OperationKind.WRITE_SAFE


def test_classify_write_gated_operations() -> None:
    assert classify_operation("push") == OperationKind.WRITE_GATED
    assert classify_operation("ship") == OperationKind.WRITE_GATED
    assert classify_operation("reset") == OperationKind.WRITE_GATED
    assert classify_operation("branch-clear") == OperationKind.WRITE_GATED
    assert classify_operation("branch-clear-remote") == OperationKind.WRITE_GATED


@patch.object(GitShortcuts, "current_branch", return_value="main")
@patch.object(GitShortcuts, "status_short", return_value="")
@patch.object(GitShortcuts, "is_dirty", return_value=False)
@patch.object(GitShortcuts, "has_upstream", return_value=True)
@patch.object(GitShortcuts, "canonical_main_ref", return_value="origin/main")
@patch.object(GitShortcuts, "remote_exists", return_value=True)
def test_git_worktree_snapshot(
    _origin: MagicMock,
    _main: MagicMock,
    _upstream: MagicMock,
    _dirty: MagicMock,
    _status: MagicMock,
    _branch: MagicMock,
) -> None:
    snap = git_worktree_snapshot(GitShortcuts(top="/repo"))
    assert snap.branch == "main"
    assert snap.repo_root == "/repo"
    assert any("branch: main" in line for line in snap.summary_lines())


def test_write_gate_skipped_for_read_operation(capsys: pytest.CaptureFixture[str]) -> None:
    write_gate("review", ["line"], question="Proceed?", yes=False)
    assert WRITE_GATE_DELIMITER not in capsys.readouterr().out


def test_write_gate_refuses_non_interactive_without_yes() -> None:
    with patch("shuttle.internal.write.gate.sys.stdin") as mock_stdin:
        mock_stdin.isatty.return_value = False
        with pytest.raises(typer.Exit):
            write_gate("push", ["branch: main"], question="Push?", yes=False)


@patch.object(GitShortcuts, "push")
def test_push_shows_write_gate_delimiter(mock_push: MagicMock) -> None:
    result = runner.invoke(app, ["git", "push", "--yes"])
    assert result.exit_code == 0
    mock_push.assert_called_once()
    assert WRITE_GATE_DELIMITER in result.stdout
