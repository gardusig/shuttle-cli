"""Mock docker CLI calls during integration checks (no daemon required)."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

from shuttle.services import docker_runtime as runtime_mod

_CONTAINER_FIXTURES = [
    {
        "Id": "abc111integration",
        "Name": "/shuttle-mock-running",
        "State": {"Status": "running"},
        "SizeRw": 2_048_000,
        "SizeRootFs": 8_000_000,
    },
    {
        "Id": "def222integration",
        "Name": "/shuttle-mock-stopped",
        "State": {"Status": "exited"},
        "SizeRw": 512_000,
        "SizeRootFs": 4_000_000,
    },
]

_IMAGE_FIXTURES = [
    {
        "Id": "sha256:img111integration",
        "RepoTags": ["shuttle/mock:latest"],
        "Size": 64_000_000,
    },
]

_STATS_FIXTURES = [
    {
        "ID": "abc111integration",
        "Name": "shuttle-mock-running",
        "CPUPerc": "12.50%",
        "MemUsage": "50MiB / 2GiB",
        "MemPerc": "2.44%",
    },
]


def _mock_docker_result(args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = args[0] if args else ""
    if cmd == "ps" and "-q" in args:
        ids = [row["Id"] for row in _CONTAINER_FIXTURES]
        if "-a" not in args:
            ids = [row["Id"] for row in _CONTAINER_FIXTURES if row["State"]["Status"] == "running"]
        stdout = "\n".join(ids) + ("\n" if ids else "")
        return subprocess.CompletedProcess(args=["docker", *args], returncode=0, stdout=stdout, stderr="")
    if cmd == "stats":
        stdout = "\n".join(json.dumps(row) for row in _STATS_FIXTURES) + "\n"
        return subprocess.CompletedProcess(args=["docker", *args], returncode=0, stdout=stdout, stderr="")
    if cmd == "inspect":
        ids: list[str] = []
        skip_next = False
        for token in args[1:]:
            if skip_next:
                skip_next = False
                continue
            if token == "--format":
                skip_next = True
                continue
            ids.append(token)
        stdout_lines: list[str] = []
        for cid in ids:
            for row in _CONTAINER_FIXTURES + _IMAGE_FIXTURES:
                if row["Id"] == cid or row["Id"].startswith(cid) or cid.startswith(row["Id"][:12]):
                    stdout_lines.append(json.dumps(row))
                    break
        stdout = "\n".join(stdout_lines) + ("\n" if stdout_lines else "")
        return subprocess.CompletedProcess(args=["docker", *args], returncode=0, stdout=stdout, stderr="")
    if cmd == "images" and "-q" in args:
        stdout = "\n".join(row["Id"] for row in _IMAGE_FIXTURES) + "\n"
        return subprocess.CompletedProcess(args=["docker", *args], returncode=0, stdout=stdout, stderr="")
    if cmd == "system" and len(args) > 1 and args[1] == "df":
        stdout = "TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE\nImages          1         1         64MB      0B\n"
        return subprocess.CompletedProcess(args=["docker", *args], returncode=0, stdout=stdout, stderr="")
    if cmd in {"rm", "stop"}:
        return subprocess.CompletedProcess(args=["docker", *args], returncode=0, stdout="", stderr="")
    if cmd == "image" and "prune" in args:
        return subprocess.CompletedProcess(
            args=["docker", *args],
            returncode=0,
            stdout="Total reclaimed space: 1.024kB\n",
            stderr="",
        )
    if cmd == "builder" and "prune" in args:
        return subprocess.CompletedProcess(
            args=["docker", *args],
            returncode=0,
            stdout="Total:\t0B\n",
            stderr="",
        )
    return subprocess.CompletedProcess(
        args=["docker", *args],
        returncode=0,
        stdout="",
        stderr="",
    )


@contextmanager
def patch_docker_cli() -> Generator[None, None, None]:
    """Prevent integration tests from calling a real docker daemon."""

    def wrapper(args: Any, *, check: bool = True) -> subprocess.CompletedProcess[str]:
        seq = list(args)
        result = _mock_docker_result(seq)
        if check and result.returncode != 0:
            raise runtime_mod.DockerError(["docker", *seq], result.returncode, result.stderr)
        return result

    with (
        patch.object(runtime_mod.shutil, "which", return_value="/usr/bin/docker"),
        patch.object(runtime_mod, "run_docker", side_effect=wrapper),
    ):
        yield
