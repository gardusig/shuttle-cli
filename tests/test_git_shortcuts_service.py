"""Unit tests for GitShortcuts service methods (mocked git)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shuttle.services.git_shortcuts import GitShortcuts
from shuttle.utils.process import GitCommandError

PATCH = "shuttle.services.git_shortcuts.run_git"


def _ok(stdout: str = "", returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.stdout = stdout
    result.stderr = ""
    result.returncode = returncode
    return result


@pytest.fixture
def svc() -> GitShortcuts:
    return GitShortcuts(top="/repo")


@patch(PATCH)
def test_init_uses_shuttle_git_root(mock_run: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHUTTLE_GIT_ROOT", "/from-env")
    s = GitShortcuts()
    assert s.top == "/from-env"
    mock_run.assert_not_called()


@patch(PATCH)
def test_canonical_main_upstream(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with patch.object(svc, "remote_exists", side_effect=lambda name: name == "upstream"):
        assert svc.canonical_main_ref() == "upstream/main"


@patch(PATCH)
def test_fetch_all_with_upstream_and_prune(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with patch.object(svc, "remote_exists", return_value=True):
        svc.fetch_all(prune=True)
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0].args[0] == ["fetch", "origin", "--prune"]
    assert mock_run.call_args_list[1].args[0] == ["fetch", "upstream", "--prune"]


@patch(PATCH)
def test_checkout_main_fallback_to_origin(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.side_effect = [
        _ok(returncode=1),
        _ok(),
        _ok(),
    ]
    with patch.object(svc, "remote_exists", return_value=True):
        svc.checkout_main()
    assert mock_run.call_args_list[1].args[0] == ["checkout", "-B", "main", "origin/main"]


@patch(PATCH)
def test_checkout_main_raises_without_origin(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok(returncode=1)
    with patch.object(svc, "remote_exists", return_value=False):
        with pytest.raises(GitCommandError):
            svc.checkout_main()


@patch(PATCH)
def test_align_main_dirty_without_yes(mock_run: MagicMock, svc: GitShortcuts) -> None:
    with patch.object(svc, "is_dirty", return_value=True):
        with pytest.raises(RuntimeError, match="dirty"):
            svc.align_main(yes=False)
    mock_run.assert_not_called()


@patch(PATCH)
def test_align_main_success(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with (
        patch.object(svc, "is_dirty", return_value=False),
        patch.object(svc, "checkout_main"),
        patch.object(svc, "fetch_all"),
        patch.object(svc, "canonical_main_ref", return_value="origin/main"),
    ):
        svc.align_main(yes=True, keep_ignored=True)
    hard_reset = [c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["reset", "--hard"]]
    clean = [c.args[0] for c in mock_run.call_args_list if c.args[0][0] == "clean"]
    assert hard_reset == [["reset", "--hard", "origin/main"]]
    assert clean == [["clean", "-fd"]]


@patch(PATCH)
def test_commit_with_paths_and_skip_empty(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.side_effect = [_ok(), _ok(returncode=0)]
    assert svc.commit("msg", paths=["a.py"]) is False
    assert mock_run.call_args_list[0].args[0] == ["add", "--", "a.py"]


@patch(PATCH)
def test_commit_creates_when_staged(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.side_effect = [_ok(), _ok(returncode=1), _ok()]
    assert svc.commit("msg") is True
    assert mock_run.call_args_list[-1].args[0] == ["commit", "-m", "msg"]


@patch(PATCH)
def test_push_requires_yes(mock_run: MagicMock, svc: GitShortcuts) -> None:
    with pytest.raises(RuntimeError, match="confirmation"):
        svc.push(yes=False)
    mock_run.assert_not_called()


@patch(PATCH)
def test_push_refuses_main(mock_run: MagicMock, svc: GitShortcuts) -> None:
    with patch.object(svc, "current_branch", return_value="main"):
        with pytest.raises(RuntimeError, match="main"):
            svc.push(yes=True)
    mock_run.assert_not_called()


@patch(PATCH)
def test_push_commits_dirty_then_pushes(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with (
        patch.object(svc, "current_branch", return_value="feat"),
        patch.object(svc, "is_dirty", return_value=True),
        patch.object(svc, "commit", return_value=True) as mock_commit,
        patch.object(svc, "remote_exists", return_value=True),
    ):
        svc.push(yes=True)
    mock_commit.assert_called_once()
    assert mock_run.call_args.args[0] == ["push", "-u", "origin", "HEAD"]


@patch(PATCH)
def test_push_no_origin(mock_run: MagicMock, svc: GitShortcuts) -> None:
    with (
        patch.object(svc, "current_branch", return_value="feat"),
        patch.object(svc, "is_dirty", return_value=False),
        patch.object(svc, "remote_exists", return_value=False),
    ):
        with pytest.raises(RuntimeError, match="origin"):
            svc.push(yes=True)


@patch(PATCH)
def test_pull_merges_upstream_and_branch(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with (
        patch.object(svc, "fetch_all"),
        patch.object(svc, "has_upstream", return_value=True),
        patch.object(svc, "canonical_main_ref", return_value="origin/main"),
        patch.object(svc, "current_branch", return_value="feat"),
    ):
        svc.pull(merge_branch="other")
    merges = [c.args[0] for c in mock_run.call_args_list if c.args[0][0] == "merge"]
    assert ["merge", "@{u}"] in merges
    assert ["merge", "other"] in merges


@patch(PATCH)
def test_start_with_align_and_push(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with (
        patch.object(svc, "align_main") as mock_align,
        patch.object(svc, "push") as mock_push,
    ):
        name = svc.start("feat", align_main=True, yes=True, no_push=False)
    assert name == "feat"
    mock_align.assert_called_once_with(yes=True)
    mock_push.assert_called_once()


@patch(PATCH)
def test_stash_operations(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok("stash@{0}: wip\n")
    svc.stash_push("wip")
    svc.stash_apply(1)
    svc.stash_pop(2)
    assert mock_run.call_args_list[0].args[0] == ["stash", "push", "-m", "wip"]
    assert mock_run.call_args_list[1].args[0] == ["stash", "apply", "stash@{1}"]
    assert mock_run.call_args_list[2].args[0] == ["stash", "pop", "stash@{2}"]
    assert "stash@{0}" in svc.stash_list()


@patch(PATCH)
def test_stash_drop_and_clear_require_yes(mock_run: MagicMock, svc: GitShortcuts) -> None:
    with pytest.raises(RuntimeError):
        svc.stash_drop(yes=False)
    with pytest.raises(RuntimeError):
        svc.stash_clear(yes=False)
    mock_run.assert_not_called()


@patch(PATCH)
def test_branch_delete_and_remote(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with (
        patch.object(svc, "current_branch", return_value="main"),
        patch.object(svc, "remote_exists", return_value=True),
    ):
        svc.branch_delete("old", yes=True)
    assert ["branch", "-d", "old"] in [c.args[0] for c in mock_run.call_args_list]


@patch(PATCH)
def test_branch_delete_current_raises(mock_run: MagicMock, svc: GitShortcuts) -> None:
    with patch.object(svc, "current_branch", return_value="feat"):
        with pytest.raises(RuntimeError, match="current"):
            svc.branch_delete("feat", yes=True)


@patch(PATCH)
def test_branch_delete_all_merged(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok("  merged\n* main\n")
    with (
        patch.object(svc, "branch_prune"),
        patch.object(svc, "current_branch", return_value="main"),
        patch.object(svc, "branch_delete") as mock_del,
    ):
        deleted = svc.branch_delete_all_merged(yes=True)
    assert deleted == ["merged"]
    mock_del.assert_called_once_with("merged", force=False, remote=True, yes=True)


@patch(PATCH)
def test_local_and_remote_branch_names(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.side_effect = [
        _ok("feat\nmain\n"),
        _ok("origin/feat\norigin/main\norigin/HEAD\n"),
    ]
    with patch.object(svc, "remote_exists", return_value=True):
        assert svc.local_branch_names() == ["feat"]
        assert svc.remote_branch_names() == ["feat"]


@patch(PATCH)
def test_clear_branches_local(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with (
        patch.object(svc, "align_main"),
        patch.object(svc, "local_branch_names", return_value=["a", "b"]),
    ):
        deleted = svc.clear_branches_local(yes=True)
    assert deleted == ["a", "b"]
    assert mock_run.call_count == 2


@patch(PATCH)
def test_delete_remote_branches(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.side_effect = [_ok(returncode=0), _ok(returncode=1)]
    with (
        patch.object(svc, "remote_exists", return_value=True),
        patch.object(svc, "fetch_all"),
        patch.object(svc, "remote_branch_names", return_value=["a", "b"]),
    ):
        deleted = svc.delete_remote_branches(yes=True)
    assert deleted == ["a"]


@patch(PATCH)
def test_rebase_abort_continue_and_onto(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    svc.rebase(abort=True)
    svc.rebase(continue_=True)
    with patch.object(svc, "fetch_all"):
        svc.rebase(onto="origin/main")
    assert mock_run.call_args_list[0].args[0] == ["rebase", "--abort"]
    assert mock_run.call_args_list[1].args[0] == ["rebase", "--continue"]
    assert mock_run.call_args_list[-1].args[0] == ["rebase", "origin/main"]


@patch(PATCH)
def test_reset_fallback_ref(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.side_effect = [_ok(returncode=1), _ok(), _ok()]
    with patch.object(svc, "fetch_all"), patch.object(svc, "canonical_main_ref", return_value="origin/main"):
        svc.reset(yes=True)
    assert ["reset", "--hard", "origin/main"] in [c.args[0] for c in mock_run.call_args_list]


@patch(PATCH)
def test_revert_and_cherry_pick(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    svc.revert("abc", abort=True)
    svc.revert("abc", continue_=True)
    svc.revert("abc", merge_parent=1)
    svc.cherry_pick("def", abort=True)
    svc.cherry_pick("def", continue_=True)
    svc.cherry_pick("ghi")
    assert ["revert", "--no-edit", "-m", "1", "abc"] in [c.args[0] for c in mock_run.call_args_list]
    assert ["cherry-pick", "--no-edit", "ghi"] in [c.args[0] for c in mock_run.call_args_list]


@patch(PATCH)
def test_tag_exists_checks(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.side_effect = [_ok(returncode=1), _ok("ref\n")]
    with patch.object(svc, "remote_exists", return_value=True):
        assert svc.tag_exists_local("t") is False
        assert svc.tag_exists_remote("t") is True
    with patch.object(svc, "remote_exists", return_value=False):
        assert svc.tag_exists_remote("t") is False


@patch(PATCH)
def test_create_and_push_tag(mock_run: MagicMock, svc: GitShortcuts) -> None:
    mock_run.return_value = _ok()
    with patch.object(svc, "tag_exists_local", return_value=False):
        svc.create_tag("t")
    with patch.object(svc, "tag_exists_local", return_value=True):
        with pytest.raises(RuntimeError, match="already exists"):
            svc.create_tag("t", replace=False)
        svc.create_tag("t", replace=True)
    with patch.object(svc, "remote_exists", return_value=True):
        svc.push_tag("t", force=False)
        svc.push_tag("t2", force=True)
    with patch.object(svc, "remote_exists", return_value=False):
        with pytest.raises(RuntimeError, match="origin"):
            svc.push_tag("t")


@patch(PATCH)
def test_large_files_tracked_and_worktree(mock_run: MagicMock, svc: GitShortcuts, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    tracked = repo / "big.bin"
    tracked.write_bytes(b"x" * 10)
    other = repo / "untracked.txt"
    other.write_text("small", encoding="utf-8")
    svc = GitShortcuts(top=str(repo))
    mock_run.return_value = _ok(f"big.bin\0")
    rows = svc.large_files(5, worktree=False)
    assert rows[0][1] == "big.bin"
    rows_wt = svc.large_files(5, worktree=True)
    assert any(name.endswith("big.bin") for _, name in rows_wt)


@patch(PATCH)
def test_post_merge_cleanup(mock_run: MagicMock, svc: GitShortcuts) -> None:
    with (
        patch.object(svc, "align_main"),
        patch.object(svc, "branch_delete_all_merged", return_value=["x"]),
    ):
        assert svc.post_merge_cleanup(yes=True) == ["x"]
