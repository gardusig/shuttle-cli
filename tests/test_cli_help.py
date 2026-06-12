from typer.testing import CliRunner

from shuttle.cli import app

runner = CliRunner()


def test_root_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "git" in result.stdout
    assert "docker" in result.stdout


def test_docker_help() -> None:
    result = runner.invoke(app, ["docker", "--help"])
    assert result.exit_code == 0
    for cmd in (
        "ps",
        "stats",
        "containers",
        "images",
        "top",
        "df",
        "stop",
        "container-delete",
        "image-delete",
        "reset",
        "clean",
    ):
        assert cmd in result.stdout


def test_git_help() -> None:
    result = runner.invoke(app, ["git", "--help"])
    assert result.exit_code == 0
    for cmd in (
        "commit",
        "push",
        "pull",
        "start",
        "main",
        "branch-delete",
        "tag",
        "zip",
        "large-files",
        "review",
        "docs",
    ):
        assert cmd in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
