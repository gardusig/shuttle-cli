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
    "shuttle.services.backup_repository",
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
    "scripts/git/rebase.sh",
    "scripts/git/reset.sh",
    "scripts/git/revert.sh",
    "scripts/git/review.sh",
    "scripts/git/start.sh",
    "scripts/git/stash.sh",
    "scripts/git/tag.sh",
    "scripts/git/tag-list.sh",
    "scripts/git/tag-push.sh",
    "scripts/git/zip.sh",
    "scripts/backup/status.sh",
    "scripts/drive/status.sh",
    "scripts/drive/ingest.sh",
    "scripts/drive/upload.sh",
    "scripts/drive/sync.sh",
]

DOCKER_VERIFY_PATHS = [
    "Dockerfile",
    "scripts/docker/common.sh",
    "scripts/docker/run-unit.sh",
    "scripts/docker/run-integration.sh",
    "scripts/test-unit.sh",
    "scripts/test-integration.sh",
    ".github/workflows/test.yml",
]

DOCKER_VERIFY_PATHS = [
    "Dockerfile",
    "scripts/docker/common.sh",
    "scripts/docker/run-unit.sh",
    "scripts/docker/run-integration.sh",
    "scripts/test-unit.sh",
    "scripts/test-integration.sh",
    ".github/workflows/test.yml",
]

REQUIRED_PATHS = [
    "config/config.yaml",
    "config/ci/config.yaml",
    "config/ci/drives.yaml",
    "config/drives.yaml",
    "data/backups/.gitkeep",
    "data/notion/.gitkeep",
    "data/bookmarks/.gitkeep",
    "scripts/bootstrap.sh",
    "scripts/install.sh",
    *DOCKER_VERIFY_PATHS,
    "scripts/chrome/ingest.sh",
    "scripts/chrome/deploy.sh",
    "scripts/chrome/export.sh",
    "scripts/chrome/import.sh",
    "scripts/chrome/export-bookmarks.sh",
    "data/tasks/.gitkeep",
    "scripts/notion/ingest.sh",
    "scripts/notion/deploy.sh",
    "scripts/notion/sync.sh",
    "scripts/notion/download.sh",
    "scripts/notion/upload.sh",
    "scripts/notion/export.sh",
    "scripts/notion/import.sh",
    "scripts/notion/cleanup.sh",
    "scripts/git/_common.sh",
    "shuttle/cli.py",
    "shuttle/__main__.py",
    *CURSOR_SKILLS_GIT_SCRIPTS,
]


def test_required_paths_exist() -> None:
    for rel in REQUIRED_PATHS:
        assert (ROOT / rel).exists(), f"missing {rel}"


def test_bootstrap_is_runtime_only_by_default() -> None:
    bootstrap = (ROOT / "scripts/bootstrap.sh").read_text()
    assert "SHUTTLE_BOOTSTRAP_DEV" in bootstrap
    assert 'pip install -e ".[dev]"' in bootstrap
    assert 'pip install -e .' in bootstrap


def test_placeholder_modules_import() -> None:
    for name in (
        PROVIDER_MODULES + MODEL_MODULES + SERVICE_MODULES + UTIL_MODULES + INTERNAL_MODULES
    ):
        importlib.import_module(name)


def test_top_level_commands_registered() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("restore", "git", "drive", "notion", "chrome"):
        assert cmd in result.stdout


def test_config_loader() -> None:
    from shuttle.utils.config import load_config

    cfg = load_config(ROOT / "config")
    assert cfg.backup.repositories
    assert cfg.drives.google.enabled is True
    assert cfg.chrome.profile == "Default"
