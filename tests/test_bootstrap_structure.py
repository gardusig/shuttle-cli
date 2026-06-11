"""Issue #3 bootstrap structure checks."""

from __future__ import annotations

import importlib
from pathlib import Path

from typer.testing import CliRunner

from shuttle.cli import app

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()

PROVIDER_MODULES = [
    "shuttle.providers.github",
    "shuttle.providers.notion",
    "shuttle.providers.chrome",
    "shuttle.providers.google_drive",
    "shuttle.providers.proton_drive",
    "shuttle.providers.icloud_drive",
    "shuttle.providers.onedrive",
]

MODEL_MODULES = [
    "shuttle.models.backup",
    "shuttle.models.bookmark",
    "shuttle.models.repository",
    "shuttle.models.task",
]

SERVICE_MODULES = [
    "shuttle.services.drive_sync",
    "shuttle.services.notion_sync",
    "shuttle.services.bookmark_sync",
    "shuttle.services.git_archive",
]

UTIL_MODULES = [
    "shuttle.utils.fs",
    "shuttle.utils.hashing",
    "shuttle.utils.retry",
    "shuttle.utils.yaml",
    "shuttle.utils.zip",
    "shuttle.utils.confirm",
]

INTERNAL_MODULES = [
    "shuttle.internal.read.safety",
    "shuttle.internal.read.git",
    "shuttle.internal.write.gate",
    "shuttle.internal.write.git",
]

CURSOR_SKILLS_GIT_SCRIPTS = [
    "scripts/git/branch.sh",
    "scripts/git/branch-delete.sh",
    "scripts/git/branch-delete-all.sh",
    "scripts/git/branch-clear.sh",
    "scripts/git/cherry-pick.sh",
    "scripts/git/commit.sh",
    "scripts/git/docs.sh",
    "scripts/git/large-files.sh",
    "scripts/git/main.sh",
    "scripts/git/post-merge-cleanup.sh",
    "scripts/git/pull.sh",
    "scripts/git/push.sh",
    "scripts/git/ship.sh",
    "scripts/git/prep.sh",
    "scripts/git/kick.sh",
    "scripts/git/land.sh",
    "scripts/git/rebase.sh",
    "scripts/git/reset.sh",
    "scripts/git/revert.sh",
    "scripts/git/review.sh",
    "scripts/git/start.sh",
    "scripts/git/stash.sh",
    "scripts/git/tag.sh",
    "scripts/git/zip.sh",
]

REQUIRED_PATHS = [
    "config/config.yaml",
    "config/repositories.yaml",
    "config/drives.yaml",
    "data/backups/.gitkeep",
    "data/notion/.gitkeep",
    "data/bookmarks/.gitkeep",
    "scripts/bootstrap.sh",
    "scripts/install.sh",
    "scripts/chrome/export-bookmarks.sh",
    "scripts/git/_common.sh",
    "shuttle/cli.py",
    "shuttle/__main__.py",
    *CURSOR_SKILLS_GIT_SCRIPTS,
]


def test_required_paths_exist() -> None:
    for rel in REQUIRED_PATHS:
        assert (ROOT / rel).exists(), f"missing {rel}"


def test_placeholder_modules_import() -> None:
    for name in (
        PROVIDER_MODULES + MODEL_MODULES + SERVICE_MODULES + UTIL_MODULES + INTERNAL_MODULES
    ):
        importlib.import_module(name)


def test_top_level_commands_registered() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("backup", "restore", "git", "drives", "notion", "bookmarks"):
        assert cmd in result.stdout


def test_config_loader() -> None:
    from shuttle.utils.config import load_config

    cfg = load_config(ROOT / "config")
    assert cfg.repositories
    assert cfg.drives.google is True
    assert cfg.chrome.profile == "Default"
