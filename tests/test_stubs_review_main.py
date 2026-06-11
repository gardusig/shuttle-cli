"""Coverage for placeholders, review runner, __main__, and gated git writes."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from shuttle.internal.write.git import gated_git_write, read_git_snapshot
from shuttle.providers import chrome, github, google_drive, icloud_drive, notion, onedrive, proton_drive
from shuttle.services import bookmark_sync, drive_sync, git_archive, notion_sync
from shuttle.services.git_review import run_review

STUB_CALLS: list[tuple[Callable[..., Any], tuple[Any, ...]]] = [
    (chrome.export_bookmarks, ("Default", "/tmp")),
    (chrome.import_bookmarks, ("Default", "/tmp")),
    (github.archive_repository, ("/repo",)),
    (github.clone_repository, ("https://x", "/dest")),
    (github.checkout_tag, ("/repo", "v1")),
    (google_drive.upload, ("/a", "/b")),
    (google_drive.download, ("/b", "/a")),
    (google_drive.list_files, ("",)),
    (google_drive.delete, ("/b",)),
    (icloud_drive.upload, ("/a", "/b")),
    (icloud_drive.download, ("/b", "/a")),
    (icloud_drive.list_files, ("",)),
    (icloud_drive.delete, ("/b",)),
    (notion.export_tasks, ("db", "/dest")),
    (notion.import_tasks, ("db", "/src")),
    (onedrive.upload, ("/a", "/b")),
    (onedrive.download, ("/b", "/a")),
    (onedrive.list_files, ("",)),
    (onedrive.delete, ("/b",)),
    (proton_drive.upload, ("/a", "/b")),
    (proton_drive.download, ("/b", "/a")),
    (proton_drive.list_files, ("prefix",)),
    (proton_drive.delete, ("/b",)),
    (bookmark_sync.export_bookmarks, ("Default", "/tmp")),
    (bookmark_sync.import_bookmarks, ("Default", "/tmp")),
    (drive_sync.upload_backup, ("/local", "google")),
    (drive_sync.download_latest, ("google", "/dest")),
    (notion_sync.export_tasks, ("db", "/dest")),
    (notion_sync.import_tasks, ("db", "/src")),
    (git_archive.archive_repository, ("/repo",)),
]


@pytest.mark.parametrize("fn,args", STUB_CALLS)
def test_placeholder_raises_not_implemented(fn: Callable[..., Any], args: tuple[Any, ...]) -> None:
    with pytest.raises(NotImplementedError):
        fn(*args)


def test_main_module_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "shuttle", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "git" in result.stdout


def test_run_review_quick_skips_pytest() -> None:
    assert run_review(install=False, quick=True) == 0


@patch("shuttle.services.git_review.subprocess.run")
def test_run_review_runs_pytest(mock_run: MagicMock, tmp_path) -> None:
    root = tmp_path
    scripts = root / "scripts"
    scripts.mkdir()
    (scripts / "noop.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    venv_bin = root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").write_text("", encoding="utf-8")
    mock_run.return_value = MagicMock(returncode=0)
    with patch("shuttle.services.git_review.project_root", return_value=root):
        assert run_review(install=False, quick=False) == 0


def test_gated_git_write_with_yes() -> None:
    svc = MagicMock()
    with patch("shuttle.internal.write.git.git_worktree_snapshot") as mock_snap:
        mock_snap.return_value.summary_lines.return_value = ["branch: main"]
        result = gated_git_write(svc, "push", lambda: 42, yes=True)
    assert result == 42


def test_read_git_snapshot() -> None:
    svc = MagicMock()
    with patch("shuttle.internal.write.git.git_worktree_snapshot") as mock_snap:
        snap = read_git_snapshot(svc)
    assert snap is mock_snap.return_value
