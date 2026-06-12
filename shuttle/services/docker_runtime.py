"""Local Docker introspection and cleanup via the docker CLI."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass

_SIZE_RE = re.compile(
    r"^([\d.]+)\s*(B|KB|MB|GB|TB|KiB|MiB|GiB|TiB)$",
    re.IGNORECASE,
)

_SIZE_UNITS = {
    "B": 1,
    "KB": 1000,
    "MB": 1000**2,
    "GB": 1000**3,
    "TB": 1000**4,
    "KIB": 1024,
    "MIB": 1024**2,
    "GIB": 1024**3,
    "TIB": 1024**4,
}


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


def parse_docker_size(value: str) -> int:
    """Parse docker size strings (e.g. 12.5MiB, 1.2GB)."""
    match = _SIZE_RE.match(value.strip())
    if not match:
        return 0
    amount = float(match.group(1))
    unit = match.group(2).upper()
    multiplier = _SIZE_UNITS.get(unit, 1)
    return int(amount * multiplier)


def parse_mem_usage(value: str) -> tuple[int, int]:
    """Parse docker stats MemUsage like '50MiB / 2GiB'."""
    parts = [part.strip() for part in value.split("/", maxsplit=1)]
    used = parse_docker_size(parts[0]) if parts else 0
    limit = parse_docker_size(parts[1]) if len(parts) > 1 else 0
    return used, limit


def parse_cpu_percent(value: str) -> float:
    cleaned = value.strip().rstrip("%")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


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
class ContainerStatsRow:
    id: str
    name: str
    cpu_percent: float
    mem_used_bytes: int
    mem_limit_bytes: int
    mem_percent: float

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


@dataclass(frozen=True)
class ResetSummary:
    stopped: list[str]
    removed_containers: list[str]
    image_prune_output: str
    cache_prune_output: str


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


def list_container_stats() -> list[ContainerStatsRow]:
    """Live CPU/memory for running containers (docker stats --no-stream)."""
    ids = _container_ids(all_containers=False)
    if not ids:
        return []
    result = run_docker(
        [
            "stats",
            "--no-stream",
            "--format",
            "{{json .}}",
            *ids,
        ]
    )
    rows: list[ContainerStatsRow] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        mem_used, mem_limit = parse_mem_usage(str(data.get("MemUsage") or ""))
        rows.append(
            ContainerStatsRow(
                id=str(data.get("ID") or data.get("Container") or "")[:12],
                name=str(data.get("Name") or ""),
                cpu_percent=parse_cpu_percent(str(data.get("CPUPerc") or "0")),
                mem_used_bytes=mem_used,
                mem_limit_bytes=mem_limit,
                mem_percent=parse_cpu_percent(str(data.get("MemPerc") or "0")),
            )
        )
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


def stop_containers(*, names: Sequence[str] | None = None) -> list[str]:
    """Stop running containers (all, or the given names/ids)."""
    if names:
        run_docker(["stop", *names])
        return list(names)
    ids = _container_ids(all_containers=False)
    if not ids:
        return []
    run_docker(["stop", *ids])
    return ids


def remove_containers(*, names: Sequence[str] | None = None) -> list[str]:
    """Remove containers (all, or the given names/ids)."""
    if names:
        run_docker(["rm", "-f", *names])
        return list(names)
    ids = _container_ids(all_containers=True)
    if not ids:
        return []
    run_docker(["rm", "-f", *ids])
    return ids


def remove_all_containers() -> list[str]:
    return remove_containers()


def prune_images(*, all_unused: bool = False) -> str:
    args = ["image", "prune", "-f"]
    if all_unused:
        args.append("-a")
    return run_docker(args).stdout.strip()


def prune_build_cache() -> str:
    return run_docker(["builder", "prune", "-f"]).stdout.strip()


def reset_docker(*, all_images: bool = True) -> ResetSummary:
    """Stop everything, remove all containers, prune images and build cache."""
    stopped = stop_containers()
    removed = remove_all_containers()
    image_out = prune_images(all_unused=all_images)
    cache_out = prune_build_cache()
    return ResetSummary(
        stopped=stopped,
        removed_containers=removed,
        image_prune_output=image_out,
        cache_prune_output=cache_out,
    )
