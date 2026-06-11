"""Issue #1 bookmark shell script tests (isolated temp dirs)."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "bookmarks.html"
CHROME_DIR = ROOT / "scripts" / "chrome"


def _run_script(name: str, env: dict[str, str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    script = CHROME_DIR / name
    merged = {**os.environ, **env}
    return subprocess.run(
        ["bash", str(script)],
        cwd=ROOT,
        env=merged,
        capture_output=True,
        text=True,
        check=check,
    )


@pytest.fixture
def sandbox(tmp_path: Path) -> dict[str, Path]:
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    data_bookmarks = tmp_path / "data" / "bookmarks"
    data_bookmarks.mkdir(parents=True)
    return {
        "root": tmp_path,
        "downloads": downloads,
        "bookmarks_file": data_bookmarks / "bookmarks.html",
    }


def test_wait_download_selects_newest_html(sandbox: dict[str, Path]) -> None:
    older = sandbox["downloads"] / "older.html"
    newer = sandbox["downloads"] / "newer.html"
    older.write_text("<html>old</html>")
    time.sleep(1.1)
    newer.write_text("<html>new</html>")

    result = _run_script(
        "wait-download.sh",
        {
            "SHUTTLE_DOWNLOADS_DIR": str(sandbox["downloads"]),
            "SHUTTLE_DOWNLOAD_TIMEOUT": "5",
        },
    )
    assert result.returncode == 0
    assert result.stdout.strip().endswith("newer.html")


def test_wait_download_ignores_crdownload(sandbox: dict[str, Path]) -> None:
    partial = sandbox["downloads"] / "bookmarks.html.crdownload"
    partial.write_text("partial")
    result = _run_script(
        "wait-download.sh",
        {
            "SHUTTLE_DOWNLOADS_DIR": str(sandbox["downloads"]),
            "SHUTTLE_DOWNLOAD_TIMEOUT": "2",
        },
        check=False,
    )
    assert result.returncode != 0


def test_export_from_fixture(sandbox: dict[str, Path]) -> None:
    result = _run_script(
        "export-bookmarks.sh",
        {
            "SHUTTLE_ROOT": str(sandbox["root"]),
            "SHUTTLE_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "SHUTTLE_SKIP_CHROME_AUTOMATION": "1",
            "SHUTTLE_BOOKMARKS_FIXTURE": str(FIXTURE),
        },
    )
    assert result.returncode == 0
    assert sandbox["bookmarks_file"].exists()
    assert "Shuttle Test Bookmark" in sandbox["bookmarks_file"].read_text()


def test_export_overwrites_previous_backup(sandbox: dict[str, Path]) -> None:
    sandbox["bookmarks_file"].write_text("<html>stale</html>")
    _run_script(
        "export-bookmarks.sh",
        {
            "SHUTTLE_ROOT": str(sandbox["root"]),
            "SHUTTLE_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "SHUTTLE_SKIP_CHROME_AUTOMATION": "1",
            "SHUTTLE_BOOKMARKS_FIXTURE": str(FIXTURE),
        },
    )
    content = sandbox["bookmarks_file"].read_text()
    assert "stale" not in content
    assert "Shuttle Test Bookmark" in content


def test_export_from_downloads_dir(sandbox: dict[str, Path]) -> None:
    downloaded = sandbox["downloads"] / "bookmarks_export.html"
    downloaded.write_text(FIXTURE.read_text())
    result = _run_script(
        "export-bookmarks.sh",
        {
            "SHUTTLE_ROOT": str(sandbox["root"]),
            "SHUTTLE_DOWNLOADS_DIR": str(sandbox["downloads"]),
            "SHUTTLE_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "SHUTTLE_SKIP_CHROME_AUTOMATION": "1",
        },
    )
    assert result.returncode == 0
    assert sandbox["bookmarks_file"].exists()
    assert "Shuttle Test Bookmark" in sandbox["bookmarks_file"].read_text()
    assert not downloaded.exists()


def test_import_succeeds_with_backup(sandbox: dict[str, Path]) -> None:
    sandbox["bookmarks_file"].write_text(FIXTURE.read_text())
    result = _run_script(
        "import-bookmarks.sh",
        {
            "SHUTTLE_ROOT": str(sandbox["root"]),
            "SHUTTLE_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "SHUTTLE_SKIP_CHROME_AUTOMATION": "1",
        },
    )
    assert result.returncode == 0
    assert "Import complete" in result.stdout


def test_import_fails_without_backup(sandbox: dict[str, Path]) -> None:
    result = _run_script(
        "import-bookmarks.sh",
        {
            "SHUTTLE_ROOT": str(sandbox["root"]),
            "SHUTTLE_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "SHUTTLE_SKIP_CHROME_AUTOMATION": "1",
        },
        check=False,
    )
    assert result.returncode != 0
    assert "Backup not found" in result.stderr + result.stdout
