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


def test_clear_branches_local_refuses_without_yes() -> None:
    svc = GitShortcuts(top="/tmp")
    with pytest.raises(RuntimeError, match="--yes"):
        svc.clear_branches_local(yes=False)


def test_delete_remote_branches_refuses_without_yes() -> None:
    svc = GitShortcuts(top="/tmp")
    with pytest.raises(RuntimeError, match="--yes"):
        svc.delete_remote_branches(yes=False)


@patch("shuttle.services.git_shortcuts.run_git")
def test_start_no_prep_skips_align_main(mock_run: MagicMock) -> None:
    svc = GitShortcuts(top="/tmp")
    mock_run.return_value.stdout = "feature\n"
    with patch.object(svc, "align_main") as mock_align:
        with patch.object(svc, "local_branch_names", return_value=[]):
            svc.start("feature", prep=False)
            mock_align.assert_not_called()
