"""Git safety gate tests."""

from unittest.mock import MagicMock, patch

import pytest

from shuttle.services.git_shortcuts import GitShortcuts


def test_push_refuses_without_yes() -> None:
    svc = GitShortcuts(top="/tmp")
    with pytest.raises(RuntimeError, match="confirmation"):
        svc.push(yes=False)


def test_reset_refuses_without_yes() -> None:
    svc = GitShortcuts(top="/tmp")
    with pytest.raises(RuntimeError, match="--yes"):
        svc.reset(yes=False)


def test_branch_delete_refuses_without_yes() -> None:
    svc = GitShortcuts(top="/tmp")
    with pytest.raises(RuntimeError, match="--yes"):
        svc.branch_delete("feature", yes=False)


@patch("shuttle.services.git_shortcuts.run_git")
def test_start_does_not_align_main_by_default(mock_run: MagicMock) -> None:
    svc = GitShortcuts(top="/tmp")
    mock_run.return_value.stdout = "feature\n"
    with patch.object(svc, "align_main") as mock_align:
        with patch.object(svc, "current_branch", return_value="main"):
            svc.start("feature", align_main=False)
            mock_align.assert_not_called()
