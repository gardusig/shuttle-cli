"""Behavior tests for every public shuttle CLI endpoint."""

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
    snap.summary_lines.return_value = ["branch: test", "dirty: false"]
    return snap


def _mock_snapshot(snapshot: MagicMock):
    return patch(GIT_SNAPSHOT_PATCH, return_value=snapshot)


# --- Root ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("args", "needle"),
    [
        (["backup"], "backup: not implemented yet"),
        (["restore"], "restore: not implemented yet"),
        (["drives"], "drives: not implemented yet"),
        (["notion"], "notion: not implemented yet"),
        (["bookmarks"], "scripts/chrome/export-bookmarks.sh"),
        (["links"], "Quick defaults"),
    ],
)
def test_placeholder_top_level_commands(args: list[str], needle: str) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert needle in result.stdout


def test_root_lists_all_top_level_groups() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("links", "git", "backup", "restore", "drives", "notion", "bookmarks"):
        assert name in result.stdout


@patch.object(GitShortcuts, "commit", return_value=True)
def test_hidden_git_alias_commit(mock_commit: MagicMock) -> None:
    result = runner.invoke(app, ["g", "commit", "-m", "alias"])
    assert result.exit_code == 0
    mock_commit.assert_called_once_with("alias", paths=None)


# --- Git: read / safe write ---------------------------------------------------


@patch("shuttle.commands.git.run_review", return_value=0)
def test_git_review_passes(mock_review: MagicMock) -> None:
    result = runner.invoke(app, ["git", "review", "--no-install"])
    assert result.exit_code == 0
    assert "review passed" in result.stdout
    mock_review.assert_called_once_with(install=False, quick=False)


@patch("shuttle.commands.git.run_review", return_value=0)
def test_git_review_quick(mock_review: MagicMock) -> None:
    result = runner.invoke(app, ["git", "review", "--no-install", "--quick"])
    assert result.exit_code == 0
    mock_review.assert_called_once_with(install=False, quick=True)


@patch("shuttle.commands.git.run_review", return_value=1)
def test_git_review_fails(mock_review: MagicMock) -> None:
    result = runner.invoke(app, ["git", "review", "--no-install"])
    assert result.exit_code == 1
    assert "review failed" in result.stdout


def test_git_docs_lists_inventory() -> None:
    result = runner.invoke(app, ["git", "docs"])
    assert result.exit_code == 0
    assert "Documentation inventory" in result.stdout
    assert "README.md" in result.stdout
    assert "No files modified" in result.stdout


@patch.object(GitShortcuts, "commit", return_value=False)
def test_git_commit_nothing_to_commit(mock_commit: MagicMock) -> None:
    result = runner.invoke(app, ["git", "commit"])
    assert result.exit_code == 0
    assert "nothing to commit" in result.stdout


@patch.object(GitShortcuts, "pull")
def test_git_pull(mock_pull: MagicMock) -> None:
    result = runner.invoke(app, ["git", "pull"])
    assert result.exit_code == 0
    assert "pull complete" in result.stdout
    mock_pull.assert_called_once()


@patch.object(GitShortcuts, "stash_list", return_value="stash@{0}: wip")
def test_git_stash_list(mock_list: MagicMock) -> None:
    result = runner.invoke(app, ["git", "stash", "list"])
    assert result.exit_code == 0
    assert "stash@{0}" in result.stdout
    mock_list.assert_called_once()


@patch.object(GitShortcuts, "branch_list", return_value="* main\n  feature")
def test_git_branch_list(mock_list: MagicMock) -> None:
    result = runner.invoke(app, ["git", "branch", "list"])
    assert result.exit_code == 0
    assert "main" in result.stdout
    mock_list.assert_called_once()


@patch.object(GitShortcuts, "large_files", return_value=[(1024, "big.bin")])
def test_git_large_files(mock_large: MagicMock) -> None:
    result = runner.invoke(app, ["git", "large-files", "-n", "1"])
    assert result.exit_code == 0
    assert "big.bin" in result.stdout
    mock_large.assert_called_once_with(1, worktree=False)


@patch.object(GitShortcuts, "start", return_value="feature-a")
def test_git_start_safe_by_default(mock_start: MagicMock) -> None:
    result = runner.invoke(app, ["git", "start", "feature-a"])
    assert result.exit_code == 0
    assert "feature-a" in result.stdout
    mock_start.assert_called_once_with(
        "feature-a",
        align_main=False,
        yes=False,
        no_push=True,
    )


# --- Git: gated writes refuse without --yes -----------------------------------


@pytest.mark.parametrize(
    "args",
    [
        ["git", "push"],
        ["git", "main"],
        ["git", "reset"],
        ["git", "branch-delete", "old"],
        ["git", "branch-delete-all"],
        ["git", "branch-clear"],
        ["git", "post-merge-cleanup"],
        ["git", "stash", "drop"],
        ["git", "stash", "clear"],
        ["git", "rebase"],
        ["git", "revert", "abc123"],
        ["git", "cherry-pick", "abc123"],
    ],
)
def test_gated_git_commands_refuse_without_yes(args: list[str], snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, args)
    assert result.exit_code != 0


# --- Git: gated writes proceed with --yes -------------------------------------


@patch.object(GitShortcuts, "align_main")
def test_git_main_with_yes(mock_align: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "main", "--yes"])
    assert result.exit_code == 0
    assert "main aligned" in result.stdout
    mock_align.assert_called_once_with(yes=True, keep_ignored=False)


@patch.object(GitShortcuts, "reset")
def test_git_reset_with_yes(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes"])
    assert result.exit_code == 0
    assert "reset complete" in result.stdout
    mock_reset.assert_called_once_with(None, yes=True, keep_ignored=False)


@patch.object(GitShortcuts, "branch_delete")
def test_git_branch_delete_with_yes(mock_delete: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "branch-delete", "old", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.stdout
    mock_delete.assert_called_once_with("old", force=False, remote=True, yes=True)


@patch.object(GitShortcuts, "branch_delete_all_merged", return_value=["a", "b"])
def test_git_branch_delete_all_with_yes(mock_delete: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "branch-delete-all", "--yes"])
    assert result.exit_code == 0
    assert "deleted 2 branches" in result.stdout
    mock_delete.assert_called_once_with(yes=True)


@patch.object(GitShortcuts, "remote_branch_names", return_value=[])
@patch.object(GitShortcuts, "local_branch_names", return_value=["feat-a", "wip"])
@patch.object(GitShortcuts, "clear_branches_local", return_value=["feat-a", "wip"])
def test_git_branch_clear_with_yes(
    mock_clear: MagicMock,
    mock_local: MagicMock,
    mock_remote: MagicMock,
    snapshot: MagicMock,
) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "branch-clear", "--yes"])
    assert result.exit_code == 0
    assert "cleared 2 local branch" in result.stdout
    mock_clear.assert_called_once_with(yes=True, keep_ignored=False)
    mock_remote.assert_called_once()


@patch.object(GitShortcuts, "delete_remote_branches", return_value=["feat-a"])
@patch.object(GitShortcuts, "remote_branch_names", return_value=["feat-a"])
@patch.object(GitShortcuts, "local_branch_names", return_value=[])
@patch.object(GitShortcuts, "clear_branches_local", return_value=[])
def test_git_branch_clear_delete_remote_with_yes(
    mock_clear: MagicMock,
    mock_local: MagicMock,
    mock_remote: MagicMock,
    mock_delete_remote: MagicMock,
    snapshot: MagicMock,
) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "branch-clear", "--yes", "--delete-remote"])
    assert result.exit_code == 0
    assert "deleted 1 remote branch" in result.stdout
    mock_delete_remote.assert_called_once_with(yes=True)


@patch.object(GitShortcuts, "post_merge_cleanup", return_value=["merged"])
def test_git_post_merge_cleanup_with_yes(mock_cleanup: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "post-merge-cleanup", "--yes"])
    assert result.exit_code == 0
    assert "cleanup done" in result.stdout
    mock_cleanup.assert_called_once_with(yes=True)


@patch.object(GitShortcuts, "stash_drop")
def test_git_stash_drop_with_yes(mock_drop: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "stash", "drop", "--yes"])
    assert result.exit_code == 0
    assert "stash dropped" in result.stdout
    mock_drop.assert_called_once_with(0, yes=True)


@patch.object(GitShortcuts, "rebase")
def test_git_rebase_with_yes(mock_rebase: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "rebase", "--yes"])
    assert result.exit_code == 0
    assert "rebase step complete" in result.stdout
    mock_rebase.assert_called_once()


@patch.object(GitShortcuts, "revert")
def test_git_revert_with_yes(mock_revert: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "revert", "abc123", "--yes"])
    assert result.exit_code == 0
    assert "revert step complete" in result.stdout
    mock_revert.assert_called_once()


@patch.object(GitShortcuts, "cherry_pick")
def test_git_cherry_pick_with_yes(mock_pick: MagicMock, snapshot: MagicMock) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "cherry-pick", "abc123", "--yes"])
    assert result.exit_code == 0
    assert "cherry-pick step complete" in result.stdout
    mock_pick.assert_called_once()


@patch.object(GitShortcuts, "tag_exists_local", return_value=False)
@patch.object(GitShortcuts, "tag_exists_remote", return_value=False)
@patch.object(GitShortcuts, "remote_exists", return_value=False)
@patch.object(GitShortcuts, "create_tag")
def test_git_tag_local_only(
    mock_create: MagicMock,
    _remote: MagicMock,
    _remote_tag: MagicMock,
    _local: MagicMock,
) -> None:
    result = runner.invoke(app, ["git", "tag", "2026-06-11"])
    assert result.exit_code == 0
    assert "2026-06-11" in result.stdout
    mock_create.assert_called_once_with("2026-06-11", replace=False)


@patch.object(GitShortcuts, "tag_exists_local", return_value=False)
@patch.object(GitShortcuts, "tag_exists_remote", return_value=False)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "create_tag")
@patch.object(GitShortcuts, "push_tag")
def test_git_tag_push_requires_yes(
    mock_push: MagicMock,
    mock_create: MagicMock,
    _remote: MagicMock,
    _remote_tag: MagicMock,
    _local: MagicMock,
    snapshot: MagicMock,
) -> None:
    with _mock_snapshot(snapshot):
        result = runner.invoke(app, ["git", "tag", "--push"])
    assert result.exit_code != 0
    mock_create.assert_called_once()
    mock_push.assert_not_called()


@patch.object(GitShortcuts, "branch_prune")
def test_git_branch_prune_no_gate(mock_prune: MagicMock) -> None:
    result = runner.invoke(app, ["git", "branch", "prune"])
    assert result.exit_code == 0
    assert "pruned" in result.stdout
    mock_prune.assert_called_once()


@patch.object(GitShortcuts, "stash_push")
def test_git_stash_push_no_gate(mock_push: MagicMock) -> None:
    result = runner.invoke(app, ["git", "stash", "push", "-m", "wip"])
    assert result.exit_code == 0
    assert "stashed" in result.stdout
    mock_push.assert_called_once_with("wip")


# --- Registry: every git subcommand appears in help ---------------------------


GIT_PUBLIC_COMMANDS = (
    "main",
    "pull",
    "commit",
    "push",
    "start",
    "stash",
    "branch",
    "branch-delete",
    "branch-delete-all",
    "branch-clear",
    "post-merge-cleanup",
    "rebase",
    "reset",
    "revert",
    "cherry-pick",
    "tag",
    "zip",
    "review",
    "docs",
    "large-files",
)


@pytest.mark.parametrize("command", GIT_PUBLIC_COMMANDS)
def test_git_help_lists_every_public_command(command: str) -> None:
    result = runner.invoke(app, ["git", "--help"])
    assert result.exit_code == 0
    assert command in result.stdout


@patch.object(GitShortcuts, "rebase")
def test_git_rebase_continue_skips_gate(mock_rebase: MagicMock) -> None:
    result = runner.invoke(app, ["git", "rebase", "--continue"])
    assert result.exit_code == 0
    mock_rebase.assert_called_once()


def test_invalid_git_stash_action() -> None:
    result = runner.invoke(app, ["git", "stash", "nope"])
    assert result.exit_code != 0
