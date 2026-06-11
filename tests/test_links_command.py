"""shuttle links index command."""

from typer.testing import CliRunner

from shuttle.cli import app

runner = CliRunner()


def test_links_lists_docs_and_defaults() -> None:
    result = runner.invoke(app, ["links"])
    assert result.exit_code == 0
    assert "Quick defaults" in result.stdout
    assert "docs/large-files.md" in result.stdout
    assert "scripts/git/start.sh" in result.stdout
    assert "scripts/chrome/export-bookmarks.sh" in result.stdout
    assert "wip-YYMMDD" in result.stdout


def test_root_help_mentions_links() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "links" in result.stdout
