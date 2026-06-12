"""Local Docker introspection and cleanup via the docker CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass


class DockerError(RuntimeError):
    def __init__(self, cmd: Sequence[str], returncode: int, stderr: str) -> None:
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"docker command failed ({returncode}): {' '.join(self.cmd)}\n{stderr}"
        )


def docker_available() -> bool:
    return shutil.which("docker") is not None


def ensure_docker() -> None:
    if not docker_available():
        raise RuntimeError("docker is not installed or not on PATH")


def run_docker(
    args: Sequence[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    ensure_docker()
    cmd = ["docker", *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise DockerError(cmd, result.returncode, result.stderr.strip())
    return result


def format_bytes(size: int) -> str:
    if size < 0:
        size = 0
    if size < 1024:
        return f"{size} B"
    value = float(size)
    for unit in ("KB", "MB", "GB", "TB"):
        value /= 1024.0
        if value < 1024.0 or unit == "TB":
            return f"{value:.1f} {unit}"
    return f"{value:.1f} TB"


@dataclass(frozen=True)
class ContainerRow:
    id: str
    name: str
    status: str
    size_rw: int
    size_rootfs: int

    @property
    def size_bytes(self) -> int:
        return self.size_rw if self.size_rw > 0 else self.size_rootfs

    @property
    def display_name(self) -> str:
        return self.name.lstrip("/")


@dataclass(frozen=True)
class ImageRow:
    id: str
    repository: str
    tag: str
    size: int

    @property
    def name(self) -> str:
        if self.repository == "<none>":
            return self.id[:12]
        if self.tag in {"", "<none>"}:
            return self.repository
        return f"{self.repository}:{self.tag}"


def _container_ids(*, all_containers: bool) -> list[str]:
    args = ["ps", "-q"]
    if all_containers:
        args.append("-a")
    out = run_docker(args).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def list_containers(
    *,
    all_containers: bool = False,
    running_only: bool = False,
) -> list[ContainerRow]:
    ids = _container_ids(all_containers=all_containers or not running_only)
    if not ids:
        return []
    result = run_docker(
        [
            "inspect",
            "--format",
            "{{json .}}",
            *ids,
        ]
    )
    rows: list[ContainerRow] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        state = data.get("State") or {}
        status = state.get("Status", "unknown")
        if running_only and status != "running":
            continue
        name = (data.get("Name") or data.get("Id", ""))[:64]
        rows.append(
            ContainerRow(
                id=str(data.get("Id", ""))[:12],
                name=name,
                status=status,
                size_rw=int(data.get("SizeRw") or 0),
                size_rootfs=int(data.get("SizeRootFs") or 0),
            )
        )
    rows.sort(key=lambda row: row.size_bytes, reverse=True)
    return rows


def list_images() -> list[ImageRow]:
    result = run_docker(["images", "-q"])
    ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not ids:
        return []
    inspect = run_docker(
        [
            "inspect",
            "--format",
            "{{json .}}",
            *ids,
        ]
    )
    rows: list[ImageRow] = []
    for line in inspect.stdout.splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        repo_tags = data.get("RepoTags") or []
        if repo_tags and repo_tags != ["<none>:<none>"]:
            ref = repo_tags[0]
            repository, _, tag = ref.partition(":")
        else:
            repository, tag = "<none>", "<none>"
        rows.append(
            ImageRow(
                id=str(data.get("Id", ""))[:12],
                repository=repository,
                tag=tag or "<none>",
                size=int(data.get("Size") or 0),
            )
        )
    rows.sort(key=lambda row: row.size, reverse=True)
    return rows


def system_df() -> str:
    return run_docker(["system", "df"]).stdout.strip()


def remove_all_containers() -> list[str]:
    ids = _container_ids(all_containers=True)
    if not ids:
        return []
    run_docker(["rm", "-f", *ids])
    return ids


def prune_images(*, all_unused: bool = False) -> str:
    args = ["image", "prune", "-f"]
    if all_unused:
        args.append("-a")
    return run_docker(args).stdout.strip()


def prune_build_cache() -> str:
    return run_docker(["builder", "prune", "-f"]).stdout.strip()
