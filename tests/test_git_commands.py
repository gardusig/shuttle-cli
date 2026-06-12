from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.git_shortcuts import GitShortcuts

runner = CliRunner()


@patch.object(GitShortcuts, "commit", return_value=True)
def test_git_commit(mock_commit: MagicMock) -> None:
    result = runner.invoke(app, ["git", "commit"])
    assert result.exit_code == 0
    assert "committed" in result.stdout
    mock_commit.assert_called_once_with(".", paths=None)


@patch.object(GitShortcuts, "commit", return_value=False)
def test_git_commit_nothing_to_commit(mock_commit: MagicMock) -> None:
    result = runner.invoke(app, ["git", "commit"])
    assert result.exit_code == 0
    assert "nothing to commit" in result.stdout
    mock_commit.assert_called_once_with(".", paths=None)


@patch.object(GitShortcuts, "commit", return_value=True)
def test_git_commit_with_paths(mock_commit: MagicMock) -> None:
    result = runner.invoke(app, ["git", "commit", "--path", "src/a.py", "--path", "src/b.py"])
    assert result.exit_code == 0
    mock_commit.assert_called_once_with(".", paths=["src/a.py", "src/b.py"])


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


@patch.object(GitShortcuts, "push", return_value="main")
def test_git_push_allow_main(mock_push: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--allow-main", "--yes"])
    assert result.exit_code == 0
    mock_push.assert_called_once_with(allow_main=True, message=".", yes=True)


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


@patch.object(GitShortcuts, "start", return_value="feature-x")
def test_git_start_push_refuses_without_yes(mock_start: MagicMock) -> None:
    result = runner.invoke(app, ["git", "start", "feature-x", "--no-prep", "--push"])
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


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: main", "dirty: false"]
    return snap


SNAPSHOT = "shuttle.commands.git.git_worktree_snapshot"


@patch.object(GitShortcuts, "align_main")
def test_git_main_requires_yes(mock_align: MagicMock) -> None:
    result = runner.invoke(app, ["git", "main"])
    assert result.exit_code != 0
    mock_align.assert_not_called()


@patch.object(GitShortcuts, "align_main")
def test_git_main_with_yes(mock_align: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "main", "--yes"])
    assert result.exit_code == 0
    assert "main aligned" in result.stdout
    mock_align.assert_called_once_with(yes=True, keep_ignored=False)


@patch.object(GitShortcuts, "align_main")
def test_git_main_keep_ignored(mock_align: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "main", "--yes", "--keep-ignored"])
    assert result.exit_code == 0
    mock_align.assert_called_once_with(yes=True, keep_ignored=True)


@patch.object(GitShortcuts, "pull")
def test_git_pull(mock_pull: MagicMock) -> None:
    result = runner.invoke(app, ["git", "pull"])
    assert result.exit_code == 0
    assert "pull complete" in result.stdout
    mock_pull.assert_called_once_with(merge_branch=None)


@patch.object(GitShortcuts, "pull")
def test_git_pull_merge_branch(mock_pull: MagicMock) -> None:
    result = runner.invoke(app, ["git", "pull", "--merge", "origin/main"])
    assert result.exit_code == 0
    mock_pull.assert_called_once_with(merge_branch="origin/main")


@patch.object(GitShortcuts, "branch_list", return_value="  main\n* feat\n")
def test_git_branch_list(mock_list: MagicMock) -> None:
    result = runner.invoke(app, ["git", "branch", "list"])
    assert result.exit_code == 0
    assert "feat" in result.stdout
    mock_list.assert_called_once()


@patch.object(GitShortcuts, "stash_list", return_value="stash@{0}: wip")
def test_git_stash_list(mock_list: MagicMock) -> None:
    result = runner.invoke(app, ["git", "stash", "list"])
    assert result.exit_code == 0
    assert "stash@{0}" in result.stdout
    mock_list.assert_called_once()


@patch.object(GitShortcuts, "reset")
def test_git_reset_refuses_without_yes(mock_reset: MagicMock) -> None:
    result = runner.invoke(app, ["git", "reset"])
    assert result.exit_code != 0
    mock_reset.assert_not_called()


@patch.object(GitShortcuts, "reset", return_value=["old-feat"])
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


@patch.object(GitShortcuts, "reset", return_value=["wip"])
def test_git_reset_all_local(mock_reset: MagicMock, snapshot: MagicMock) -> None:
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


@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_discard(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--discard"])
    assert result.exit_code == 0
    mock_reset.assert_called_once_with(
        yes=True,
        keep_ignored=False,
        main_only=False,
        all_local=False,
        branch_message=".",
        discard=True,
    )


@patch.object(GitShortcuts, "branch_delete")
def test_git_branch_delete_refuses(mock_delete: MagicMock) -> None:
    result = runner.invoke(app, ["git", "branch-delete", "old-branch"])
    assert result.exit_code != 0
    mock_delete.assert_not_called()


@patch.object(GitShortcuts, "branch_delete")
def test_git_branch_delete_with_yes(mock_delete: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "branch-delete", "old-branch", "--yes", "--no-remote"])
    assert result.exit_code == 0
    mock_delete.assert_called_once_with("old-branch", force=False, remote=False, yes=True)


@patch.object(GitShortcuts, "stash_push")
def test_git_stash_push(mock_push: MagicMock) -> None:
    result = runner.invoke(app, ["git", "stash", "push", "-m", "wip"])
    assert result.exit_code == 0
    mock_push.assert_called_once_with("wip")


@patch.object(GitShortcuts, "list_local_tags", return_value=["v1"])
@patch.object(GitShortcuts, "list_remote_tags", return_value=[])
def test_git_tag_list(mock_remote: MagicMock, mock_local: MagicMock) -> None:
    result = runner.invoke(app, ["git", "tag", "list"])
    assert result.exit_code == 0
    assert "v1" in result.stdout
    mock_local.assert_called_once()
    mock_remote.assert_called_once()


@patch.object(GitShortcuts, "large_files", return_value=[("100", "big.bin")])
def test_git_large_files(mock_large: MagicMock) -> None:
    result = runner.invoke(app, ["git", "large-files", "-n", "5"])
    assert result.exit_code == 0
    assert "big.bin" in result.stdout
    mock_large.assert_called_once_with(5, worktree=False)


@patch.object(GitShortcuts, "rebase")
def test_git_rebase_refuses(mock_rebase: MagicMock) -> None:
    result = runner.invoke(app, ["git", "rebase", "main"])
    assert result.exit_code != 0
    mock_rebase.assert_not_called()


@patch.object(GitShortcuts, "revert")
def test_git_revert_refuses(mock_revert: MagicMock) -> None:
    result = runner.invoke(app, ["git", "revert", "HEAD"])
    assert result.exit_code != 0
    mock_revert.assert_not_called()


@patch.object(GitShortcuts, "cherry_pick")
def test_git_cherry_pick_refuses(mock_pick: MagicMock) -> None:
    result = runner.invoke(app, ["git", "cherry-pick", "abc123"])
    assert result.exit_code != 0
    mock_pick.assert_not_called()


@patch("shuttle.commands.git.run_review", return_value=0)
def test_git_review_quick(mock_review: MagicMock) -> None:
    result = runner.invoke(app, ["git", "review", "--no-install", "--quick"])
    assert result.exit_code == 0
    assert "review passed" in result.stdout
    mock_review.assert_called_once_with(install=False, quick=True)


@patch.object(GitShortcuts, "tag_exists_local", return_value=True)
@patch.object(GitShortcuts, "repo_basename", return_value="my-repo")
@patch.object(GitShortcuts, "zip_tag")
@patch("shuttle.commands.git.default_tag_name", return_value="2026-06-12")
def test_git_zip_default_tag(
    _default: MagicMock,
    mock_zip: MagicMock,
    _basename: MagicMock,
    _exists: MagicMock,
) -> None:
    mock_zip.return_value = Path("/tmp/my-repo-2026-06-12.zip")
    result = runner.invoke(app, ["git", "zip"])
    assert result.exit_code == 0
    mock_zip.assert_called_once()
    assert mock_zip.call_args.args[0] == "2026-06-12"


@patch.object(GitShortcuts, "create_tag")
@patch.object(GitShortcuts, "tag_exists_local", return_value=False)
@patch.object(GitShortcuts, "prepare_for_tag")
@patch("shuttle.commands.git._reconcile_tag_push")
@patch("shuttle.commands.git.default_tag_name", return_value="2026-06-12")
def test_git_tag_default_name(
    _default: MagicMock,
    _push: MagicMock,
    mock_prepare: MagicMock,
    _local: MagicMock,
    mock_create: MagicMock,
) -> None:
    result = runner.invoke(app, ["git", "tag", "--yes"])
    assert result.exit_code == 0
    mock_create.assert_called_once_with("2026-06-12", replace=False)


@patch.object(GitShortcuts, "current_branch", return_value="kappap")
def test_git_branch_current(mock_branch: MagicMock) -> None:
    result = runner.invoke(app, ["git", "branch-current"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "kappap"
    mock_branch.assert_called_once()


@patch.object(GitShortcuts, "diff_stat", return_value=" 2 files changed\n")
def test_git_diff_stat(mock_diff: MagicMock) -> None:
    result = runner.invoke(app, ["git", "diff-stat", "--base", "main"])
    assert result.exit_code == 0
    assert "files changed" in result.stdout
    mock_diff.assert_called_once_with("main", "HEAD")
