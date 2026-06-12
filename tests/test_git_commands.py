from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.git_shortcuts import GitShortcuts

runner = CliRunner()


@patch.object(GitShortcuts, "commit", return_value=True)
def test_git_commit(mock_commit: MagicMock) -> None:
    result = runner.invoke(app, ["git", "commit"])
    assert result.exit_code == 0
    mock_commit.assert_called_once_with(".", paths=None)


@patch.object(GitShortcuts, "push")
def test_git_push_requires_yes(mock_push: MagicMock) -> None:
    result = runner.invoke(app, ["git", "push"])
    assert result.exit_code != 0
    mock_push.assert_not_called()


@patch.object(GitShortcuts, "push", return_value="feat")
def test_git_push_with_yes(mock_push: MagicMock) -> None:
    result = runner.invoke(app, ["git", "push", "--yes"])
    assert result.exit_code == 0
    assert "pushed" in result.stdout
    mock_push.assert_called_once_with(allow_main=False, message=".", yes=True)


@patch.object(GitShortcuts, "start", return_value="feature-x")
def test_git_start_no_prep_without_yes(mock_start: MagicMock) -> None:
    result = runner.invoke(app, ["git", "start", "feature-x", "--no-prep"])
    assert result.exit_code == 0
    mock_start.assert_called_once_with(
        "feature-x",
        yes=False,
        keep_ignored=False,
        prep=False,
        no_push=True,
    )


@patch.object(GitShortcuts, "start", return_value="feature-x")
def test_git_start_prep_requires_yes(mock_start: MagicMock) -> None:
    result = runner.invoke(app, ["git", "start", "feature-x"])
    assert result.exit_code != 0
    mock_start.assert_not_called()


@patch.object(GitShortcuts, "canonical_main_ref", return_value="origin/main")
@patch.object(GitShortcuts, "remote_exists", return_value=False)
def test_canonical_main_same_repo(_remote: MagicMock, canonical: MagicMock) -> None:
    svc = GitShortcuts(top="/tmp")
    assert svc.canonical_main_ref() == "origin/main"


@patch("shuttle.services.git_shortcuts.run_git")
def test_repo_root(mock_run: MagicMock) -> None:
    mock_run.return_value.stdout = "/repo\n"
    assert GitShortcuts.repo_root() == "/repo"
