"""CLI tests for shuttle docker commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.docker_runtime import ContainerRow, ImageRow

runner = CliRunner()


@patch("shuttle.commands.docker.docker_available", return_value=False)
def test_docker_ps_requires_binary(_avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "ps"])
    assert result.exit_code != 0
    assert "PATH" in result.stdout


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch(
    "shuttle.commands.docker.list_containers",
    return_value=[
        ContainerRow("abc", "/web", "running", 2048, 4096),
    ],
)
def test_docker_ps_lists_running(mock_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "ps"])
    assert result.exit_code == 0
    assert "web" in result.stdout
    mock_list.assert_called_once_with(running_only=True)


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch(
    "shuttle.commands.docker.list_images",
    return_value=[ImageRow("sha", "app", "latest", 1_000_000)],
)
def test_docker_images(mock_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "images", "--top", "5"])
    assert result.exit_code == 0
    assert "app:latest" in result.stdout
    mock_list.assert_called_once()


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.list_images", return_value=[])
@patch(
    "shuttle.commands.docker.list_containers",
    side_effect=[
        [ContainerRow("a", "/run", "running", 100, 200)],
        [ContainerRow("b", "/stop", "exited", 300, 400)],
    ],
)
def test_docker_top(mock_list: MagicMock, _images: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "top", "-n", "1"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert mock_list.call_count == 2


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.remove_all_containers")
def test_docker_clean_containers_requires_yes(
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "containers"])
    assert result.exit_code != 0
    mock_remove.assert_not_called()


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.remove_all_containers", return_value=["a", "b"])
@patch("shuttle.commands.docker.list_containers", return_value=[])
def test_docker_clean_containers_with_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "containers", "--yes"])
    assert result.exit_code == 0
    assert "removed 2 container" in result.stdout
    mock_remove.assert_called_once()


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.prune_images", return_value="Total reclaimed: 1GB")
@patch("shuttle.commands.docker.list_containers", return_value=[])
@patch("shuttle.commands.docker.list_images", return_value=[])
def test_docker_clean_images_all(
    _list_images: MagicMock,
    _list_containers: MagicMock,
    mock_prune: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "images", "--yes", "--all-images"])
    assert result.exit_code == 0
    assert "Total reclaimed" in result.stdout
    mock_prune.assert_called_once_with(all_unused=True)
