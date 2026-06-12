"""Unit tests for shuttle.services.docker_runtime."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from shuttle.services.docker_runtime import (
    DockerError,
    format_bytes,
    list_container_stats,
    list_containers,
    list_images,
    parse_cpu_percent,
    parse_docker_size,
    parse_mem_usage,
    remove_all_containers,
    reset_docker,
    stop_containers,
)


def test_format_bytes() -> None:
    assert format_bytes(512) == "512 B"
    assert format_bytes(2048) == "2.0 KB"
    assert format_bytes(5 * 1024**3) == "5.0 GB"


def test_parse_docker_size_and_mem_usage() -> None:
    assert parse_docker_size("50MiB") == 50 * 1024**2
    assert parse_docker_size("1.5GB") == int(1.5 * 1000**3)
    used, limit = parse_mem_usage("50MiB / 2GiB")
    assert used == 50 * 1024**2
    assert limit == 2 * 1024**3
    assert parse_cpu_percent("12.34%") == 12.34


@patch("shuttle.services.docker_runtime.run_docker")
def test_list_containers_sorted(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        MagicMock(stdout="abc\ndef\n", returncode=0),
        MagicMock(
            stdout="\n".join(
                [
                    json.dumps(
                        {
                            "Id": "abc123",
                            "Name": "/small",
                            "State": {"Status": "exited"},
                            "SizeRw": 100,
                            "SizeRootFs": 1000,
                        }
                    ),
                    json.dumps(
                        {
                            "Id": "def456",
                            "Name": "/big",
                            "State": {"Status": "running"},
                            "SizeRw": 5000,
                            "SizeRootFs": 9000,
                        }
                    ),
                ]
            ),
            returncode=0,
        ),
    ]
    rows = list_containers(all_containers=True)
    assert [row.display_name for row in rows] == ["big", "small"]
    assert rows[0].size_bytes == 5000


@patch("shuttle.services.docker_runtime.run_docker")
def test_list_images_sorted(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        MagicMock(stdout="img1\n", returncode=0),
        MagicMock(
            stdout=json.dumps(
                {
                    "Id": "sha256:img1",
                    "RepoTags": ["my/app:latest"],
                    "Size": 42_000_000,
                }
            )
            + "\n",
            returncode=0,
        ),
    ]
    rows = list_images()
    assert rows[0].name == "my/app:latest"
    assert rows[0].size == 42_000_000


@patch("shuttle.services.docker_runtime.run_docker")
def test_list_container_stats(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        MagicMock(stdout="abc\n", returncode=0),
        MagicMock(
            stdout=json.dumps(
                {
                    "ID": "abc123",
                    "Name": "web",
                    "CPUPerc": "5.00%",
                    "MemUsage": "10MiB / 1GiB",
                    "MemPerc": "0.98%",
                }
            )
            + "\n",
            returncode=0,
        ),
    ]
    rows = list_container_stats()
    assert rows[0].display_name == "web"
    assert rows[0].cpu_percent == 5.0
    assert rows[0].mem_used_bytes == 10 * 1024**2


@patch("shuttle.services.docker_runtime.run_docker")
def test_stop_containers(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        MagicMock(stdout="a\n", returncode=0),
        MagicMock(stdout="", returncode=0),
    ]
    stopped = stop_containers()
    assert stopped == ["a"]
    assert mock_run.call_args_list[-1].args[0][0] == "stop"


@patch("shuttle.services.docker_runtime.run_docker")
def test_reset_docker(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        MagicMock(stdout="", returncode=0),  # ps -q (stop)
        MagicMock(stdout="", returncode=0),  # ps -a (remove)
        MagicMock(stdout="reclaimed\n", returncode=0),  # image prune
        MagicMock(stdout="cache\n", returncode=0),  # builder prune
    ]
    summary = reset_docker()
    assert summary.image_prune_output == "reclaimed"
    assert summary.cache_prune_output == "cache"


@patch("shuttle.services.docker_runtime.run_docker")
def test_remove_all_containers(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        MagicMock(stdout="a\nb\n", returncode=0),
        MagicMock(stdout="", returncode=0),
    ]
    removed = remove_all_containers()
    assert removed == ["a", "b"]
    assert mock_run.call_args_list[-1].args[0][:2] == ["rm", "-f"]


@patch("shuttle.services.docker_runtime.shutil.which", return_value=None)
def test_run_docker_missing_binary(_which: MagicMock) -> None:
    from shuttle.services.docker_runtime import run_docker

    with pytest.raises(RuntimeError, match="PATH"):
        run_docker(["ps"])


@patch("shuttle.services.docker_runtime.shutil.which", return_value="/usr/bin/docker")
def test_run_docker_raises_on_failure(_which: MagicMock) -> None:
    from shuttle.services.docker_runtime import run_docker

    with patch("shuttle.services.docker_runtime.subprocess.run") as mock_proc:
        mock_proc.return_value = MagicMock(returncode=1, stderr="boom", stdout="")
        with pytest.raises(DockerError, match="boom"):
            run_docker(["ps"])
