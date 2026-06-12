"""CLI tests for shuttle chrome bookmarks ingest/deploy."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shuttle.cli import app

runner = CliRunner()


@patch("shuttle.commands.chrome.subprocess.run")
@patch("shuttle.commands.chrome.bookmarks_file_path")
def test_chrome_bookmarks_ingest(mock_path: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
    dest = tmp_path / "bookmarks.html"
    mock_path.return_value = dest
    mock_run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["chrome", "bookmarks", "ingest"])
    assert result.exit_code == 0
    assert "ingested" in result.stdout
    mock_run.assert_called_once()


@patch("shuttle.commands.chrome.subprocess.run")
@patch("shuttle.commands.chrome.bookmarks_file_path")
def test_chrome_bookmarks_deploy(mock_path: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "bookmarks.html"
    src.write_text("<html></html>", encoding="utf-8")
    mock_path.return_value = src
    mock_run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["chrome", "bookmarks", "deploy"])
    assert result.exit_code == 0
    assert "deployed" in result.stdout


@patch("shuttle.commands.chrome.bookmarks_file_path")
def test_chrome_bookmarks_deploy_missing_backup(mock_path: MagicMock, tmp_path: Path) -> None:
    mock_path.return_value = tmp_path / "missing.html"
    result = runner.invoke(app, ["chrome", "bookmarks", "deploy"])
    assert result.exit_code != 0
    assert "Backup not found" in result.stdout


def test_legacy_bookmarks_export_alias_calls_ingest() -> None:
    with patch("shuttle.commands.chrome.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch("shuttle.commands.chrome.bookmarks_file_path", return_value=Path("/tmp/b.html")):
            result = runner.invoke(app, ["bookmarks", "export"])
    assert result.exit_code == 0
    assert "ingested" in result.stdout


@patch("shuttle.commands.chrome.subprocess.run")
@patch("shuttle.commands.chrome.bookmarks_file_path")
def test_chrome_legacy_export_alias_calls_ingest(mock_path: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
    dest = tmp_path / "bookmarks.html"
    mock_path.return_value = dest
    mock_run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["chrome", "bookmarks", "export"])
    assert result.exit_code == 0
    assert "ingested" in result.stdout


@patch("shuttle.commands.chrome.subprocess.run")
@patch("shuttle.commands.chrome.bookmarks_file_path")
def test_chrome_legacy_import_alias_calls_deploy(mock_path: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "bookmarks.html"
    src.write_text("<html></html>", encoding="utf-8")
    mock_path.return_value = src
    mock_run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["chrome", "bookmarks", "import"])
    assert result.exit_code == 0
    assert "deployed" in result.stdout
