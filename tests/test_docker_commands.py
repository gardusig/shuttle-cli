"""CLI tests for shuttle docker commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.docker_runtime import (
    ContainerRow,
    ContainerStatsRow,
    ImageRow,
    ResetSummary,
)

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
    "shuttle.commands.docker.list_container_stats",
    return_value=[
        ContainerStatsRow("abc", "web", 12.5, 50_000_000, 2_000_000_000, 2.4),
    ],
)
def test_docker_stats_cpu(mock_stats: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "stats", "--by", "cpu"])
    assert result.exit_code == 0
    assert "web" in result.stdout
    assert "12.5%" in result.stdout
    mock_stats.assert_called_once()


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
    "shuttle.commands.docker.list_container_stats",
    return_value=[ContainerStatsRow("a", "run", 1.0, 100, 1000, 10.0)],
)
@patch(
    "shuttle.commands.docker.list_containers",
    side_effect=[
        [ContainerRow("b", "/stop", "exited", 300, 400)],
    ],
)
def test_docker_top(mock_list: MagicMock, _stats: MagicMock, _images: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "top", "-n", "1"])
    assert result.exit_code == 0
    assert "CPU" in result.stdout
    assert "run" in result.stdout
    mock_list.assert_called_once_with(all_containers=True)


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.stop_containers")
@patch(
    "shuttle.commands.docker.list_containers",
    return_value=[ContainerRow("a", "/web", "running", 100, 200)],
)
def test_docker_stop_requires_yes(
    _list: MagicMock,
    mock_stop: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "stop"])
    assert result.exit_code != 0
    mock_stop.assert_not_called()


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.stop_containers", return_value=["a"])
@patch(
    "shuttle.commands.docker.list_containers",
    return_value=[ContainerRow("a", "/web", "running", 100, 200)],
)
def test_docker_stop_with_yes(
    _list: MagicMock,
    mock_stop: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "stop", "--yes"])
    assert result.exit_code == 0
    assert "stopped 1 container" in result.stdout
    mock_stop.assert_called_once_with(names=None)


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.remove_containers")
@patch("shuttle.commands.docker.list_containers", return_value=[])
def test_docker_container_delete_requires_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "container-delete"])
    assert result.exit_code != 0
    mock_remove.assert_not_called()


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.remove_containers", return_value=["a", "b"])
@patch("shuttle.commands.docker.list_containers", return_value=[])
def test_docker_container_delete_with_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "container-delete", "--yes"])
    assert result.exit_code == 0
    assert "deleted 2 container" in result.stdout
    mock_remove.assert_called_once_with(names=None)


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.reset_docker")
@patch("shuttle.commands.docker.list_containers", return_value=[])
def test_docker_reset_requires_yes(
    _list: MagicMock,
    mock_reset: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "reset"])
    assert result.exit_code != 0
    mock_reset.assert_not_called()


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch(
    "shuttle.commands.docker.reset_docker",
    return_value=ResetSummary(["a"], ["a", "b"], "reclaimed", "cache"),
)
@patch("shuttle.commands.docker.list_containers", return_value=[])
def test_docker_reset_with_yes(
    _list: MagicMock,
    mock_reset: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "reset", "--yes"])
    assert result.exit_code == 0
    assert "build cache prune" in result.stdout
    mock_reset.assert_called_once_with(all_images=True)


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.remove_containers")
@patch("shuttle.commands.docker.list_containers", return_value=[])
def test_docker_clean_containers_requires_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "containers"])
    assert result.exit_code != 0
    mock_remove.assert_not_called()


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.remove_containers", return_value=["a", "b"])
@patch("shuttle.commands.docker.list_containers", return_value=[])
def test_docker_clean_containers_with_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "containers", "--yes"])
    assert result.exit_code == 0
    assert "removed 2 container" in result.stdout
    mock_remove.assert_called_once_with()


@patch("shuttle.commands.docker.docker_available", return_value=True)
@patch("shuttle.commands.docker.prune_images", return_value="Total reclaimed: 1GB")
@patch("shuttle.commands.docker.list_containers", return_value=[])
@patch("shuttle.commands.docker.list_images", return_value=[])
def test_docker_image_delete_all(
    _list_images: MagicMock,
    _list_containers: MagicMock,
    mock_prune: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "image-delete", "--yes", "--all-images"])
    assert result.exit_code == 0
    assert "Total reclaimed" in result.stdout
    mock_prune.assert_called_once_with(all_unused=True)
