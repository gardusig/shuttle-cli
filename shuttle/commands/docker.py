"""Docker container and image shortcuts (monitor, stop, delete, reset)."""

from __future__ import annotations

from typing import Literal

import typer
from rich import print as rprint
from rich.table import Table

from shuttle.internal.write.gate import require_write_gate
from shuttle.services.docker_runtime import (
    ContainerRow,
    ContainerStatsRow,
    ImageRow,
    docker_available,
    format_bytes,
    list_container_stats,
    list_containers,
    list_images,
    prune_build_cache,
    prune_images,
    remove_containers,
    reset_docker,
    stop_containers,
    system_df,
)

docker_app = typer.Typer(
    help="Docker monitor and cleanup (no container start).",
    no_args_is_help=True,
)

StatsDomain = Literal["cpu", "memory", "storage", "all"]


def _require_docker() -> None:
    if not docker_available():
        raise typer.Exit("docker is not installed or not on PATH")


def _print_container_table(rows: list[ContainerRow], *, title: str) -> None:
    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("SIZE", justify="right")
    table.add_column("NAME")
    table.add_column("STATUS")
    table.add_column("ID")
    for row in rows:
        table.add_row(
            format_bytes(row.size_bytes),
            row.display_name,
            row.status,
            row.id,
        )
    rprint(table)


def _print_stats_table(rows: list[ContainerStatsRow], *, title: str) -> None:
    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("CPU", justify="right")
    table.add_column("MEM", justify="right")
    table.add_column("MEM %", justify="right")
    table.add_column("NAME")
    table.add_column("ID")
    for row in rows:
        mem = format_bytes(row.mem_used_bytes)
        if row.mem_limit_bytes:
            mem = f"{mem} / {format_bytes(row.mem_limit_bytes)}"
        table.add_row(
            f"{row.cpu_percent:.1f}%",
            mem,
            f"{row.mem_percent:.1f}%",
            row.display_name,
            row.id,
        )
    rprint(table)


def _print_image_table(rows: list[ImageRow], *, title: str) -> None:
    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("SIZE", justify="right")
    table.add_column("IMAGE")
    table.add_column("ID")
    for row in rows:
        table.add_row(format_bytes(row.size), row.name, row.id)
    rprint(table)


def _container_preview(rows: list[ContainerRow], *, limit: int = 5) -> list[str]:
    lines: list[str] = []
    for row in rows[:limit]:
        lines.append(f"  - {row.display_name} ({row.status})")
    if len(rows) > limit:
        lines.append(f"  ... ({len(rows) - limit} more)")
    return lines


@docker_app.command("ps")
def ps_cmd(
    top: int = typer.Option(20, "--top", "-n", help="Max rows to show."),
) -> None:
    """Running containers sorted by writable layer size."""
    _require_docker()
    rows = list_containers(running_only=True)[:top]
    if not rows:
        rprint("[dim]no running containers[/dim]")
        return
    _print_container_table(rows, title="Running containers (by storage)")


@docker_app.command("stats")
def stats_cmd(
    by: StatsDomain = typer.Option(
        "all",
        "--by",
        "-b",
        help="cpu | memory | storage | all",
    ),
    top: int = typer.Option(10, "--top", "-n", help="Max rows per section."),
) -> None:
    """Top resource consumers by CPU, memory, or container storage."""
    _require_docker()
    if by in {"cpu", "memory", "all"}:
        live = list_container_stats()
        if not live:
            rprint("[dim]no running containers[/dim]")
        elif by in {"cpu", "all"}:
            cpu_rows = sorted(live, key=lambda row: row.cpu_percent, reverse=True)[:top]
            _print_stats_table(cpu_rows, title=f"Top {len(cpu_rows)} by CPU")
        if by in {"memory", "all"} and live:
            if by == "all":
                rprint()
            mem_rows = sorted(live, key=lambda row: row.mem_used_bytes, reverse=True)[:top]
            _print_stats_table(mem_rows, title=f"Top {len(mem_rows)} by memory")
    if by in {"storage", "all"}:
        storage_rows = list_containers(running_only=True)[:top]
        if not storage_rows:
            if by == "storage":
                rprint("[dim]no running containers[/dim]")
        else:
            if by == "all":
                rprint()
            _print_container_table(storage_rows, title=f"Top {len(storage_rows)} by container storage")


@docker_app.command("containers")
def containers_cmd(
    top: int = typer.Option(20, "--top", "-n", help="Max rows to show."),
    running: bool = typer.Option(False, "--running", help="Only running containers."),
) -> None:
    """All containers sorted by on-disk size."""
    _require_docker()
    rows = list_containers(all_containers=not running, running_only=running)[:top]
    if not rows:
        rprint("[dim]no containers[/dim]")
        return
    title = "Running containers (by storage)" if running else "Containers (by storage)"
    _print_container_table(rows, title=title)


@docker_app.command("images")
def images_cmd(
    top: int = typer.Option(20, "--top", "-n", help="Max rows to show."),
) -> None:
    """Images sorted by size."""
    _require_docker()
    rows = list_images()[:top]
    if not rows:
        rprint("[dim]no images[/dim]")
        return
    _print_image_table(rows, title="Images (by storage)")


@docker_app.command("top")
def top_cmd(
    n: int = typer.Option(5, "--top", "-n", help="Rows per domain section."),
) -> None:
    """Dashboard: heaviest CPU, memory, and storage consumers."""
    _require_docker()
    live = list_container_stats()
    if live:
        cpu_rows = sorted(live, key=lambda row: row.cpu_percent, reverse=True)[:n]
        _print_stats_table(cpu_rows, title=f"CPU — top {len(cpu_rows)} running")
        rprint()
        mem_rows = sorted(live, key=lambda row: row.mem_used_bytes, reverse=True)[:n]
        _print_stats_table(mem_rows, title=f"Memory — top {len(mem_rows)} running")
    else:
        rprint("[dim]no running containers (cpu/memory)[/dim]")

    all_containers = list_containers(all_containers=True)[:n]
    images = list_images()[:n]
    if all_containers:
        rprint()
        _print_container_table(all_containers, title=f"Storage — top {len(all_containers)} containers")
    if images:
        rprint()
        _print_image_table(images, title=f"Storage — top {len(images)} images")
    if not live and not all_containers and not images:
        rprint("[dim]docker is empty[/dim]")


@docker_app.command("df")
def df_cmd() -> None:
    """Docker disk usage summary (docker system df)."""
    _require_docker()
    rprint(system_df())


@docker_app.command("stop")
def stop_cmd(
    names: list[str] = typer.Argument(None, help="Container names/ids (default: all running)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm stop."),
) -> None:
    """Stop running containers."""
    _require_docker()
    running = list_containers(running_only=True)
    targets = list(names) if names else [row.display_name for row in running]
    if not targets:
        rprint("[yellow]no running containers[/yellow]")
        return
    extra = [f"containers_to_stop: {len(targets)}", *[f"  - {name}" for name in targets[:10]]]
    if len(targets) > 10:
        extra.append(f"  ... ({len(targets) - 10} more)")
    require_write_gate(
        "docker-stop",
        summary_lines=["intent: docker stop"],
        question=f"Stop {len(targets)} container(s)?",
        yes=yes,
        extra_lines=extra,
    )
    stopped = stop_containers(names=names)
    rprint(f"[green]stopped[/green] {len(stopped)} container(s)")


@docker_app.command("container-delete")
def container_delete_cmd(
    names: list[str] = typer.Argument(None, help="Container names/ids (default: all)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm delete."),
) -> None:
    """Remove containers (stopped and running)."""
    _require_docker()
    if names:
        preview = [row for row in list_containers(all_containers=True) if row.display_name in names or row.id in names]
        if not preview:
            preview = [
                ContainerRow(name=f"/{name}", id=name[:12], status="unknown", size_rw=0, size_rootfs=0)
                for name in names
            ]
        target_count = len(names)
        question = f"Delete {target_count} container(s)?"
    else:
        preview = list_containers(all_containers=True)
        target_count = len(preview)
        question = f"Delete all {target_count} container(s)?"
    extra = [f"containers_to_delete: {target_count}", *_container_preview(preview)]
    require_write_gate(
        "docker-container-delete",
        summary_lines=["intent: docker rm -f"],
        question=question,
        yes=yes,
        extra_lines=extra,
    )
    removed = remove_containers(names=names)
    rprint(f"[green]deleted[/green] {len(removed)} container(s)")


@docker_app.command("image-delete")
def image_delete_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm image prune."),
    all_images: bool = typer.Option(
        False,
        "--all-images",
        help="Prune all unused images (not only dangling).",
    ),
) -> None:
    """Prune unused images."""
    _require_docker()
    images = list_images()
    extra = [
        f"images_present: {len(images)}",
        f"prune_mode: {'all unused' if all_images else 'dangling only'}",
    ]
    require_write_gate(
        "docker-image-delete",
        summary_lines=["intent: docker image prune"],
        question="Prune unused images?",
        yes=yes,
        extra_lines=extra,
    )
    out = prune_images(all_unused=all_images)
    if out:
        rprint(out)
    rprint("[green]image prune[/green] complete")


@docker_app.command("reset")
def reset_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm full docker reset."),
    all_images: bool = typer.Option(
        True,
        "--all-images/--dangling-only",
        help="Prune all unused images (default) or dangling only.",
    ),
) -> None:
    """Stop all containers, remove them, and prune images + build cache."""
    _require_docker()
    running = list_containers(running_only=True)
    all_rows = list_containers(all_containers=True)
    extra = [
        "intent: stop all → rm all containers → image prune → build cache prune",
        f"running_containers: {len(running)}",
        f"total_containers: {len(all_rows)}",
        f"image_prune: {'all unused' if all_images else 'dangling only'}",
        "build_cache: prune",
    ]
    extra.extend(_container_preview(all_rows))
    require_write_gate(
        "docker-reset",
        summary_lines=["intent: docker reset"],
        question="Reset docker (stop, delete containers, prune images and cache)?",
        yes=yes,
        extra_lines=extra,
    )
    summary = reset_docker(all_images=all_images)
    rprint(f"[green]stopped[/green] {len(summary.stopped)} container(s)")
    rprint(f"[green]deleted[/green] {len(summary.removed_containers)} container(s)")
    if summary.image_prune_output:
        rprint(summary.image_prune_output)
    rprint("[green]image prune[/green] complete")
    if summary.cache_prune_output:
        rprint(summary.cache_prune_output)
    rprint("[green]build cache prune[/green] complete")


@docker_app.command("clean")
def clean_cmd(
    target: str = typer.Argument(
        "containers",
        help="containers | images | cache | all",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm destructive cleanup."),
    all_images: bool = typer.Option(
        False,
        "--all-images",
        help="With images: prune all unused images (not only dangling).",
    ),
) -> None:
    """Targeted cleanup (containers, images, cache). Prefer `reset` for full wipe."""
    _require_docker()

    target = target.lower()
    if target not in {"containers", "images", "cache", "all"}:
        raise typer.BadParameter("target must be containers, images, cache, or all")

    preview_containers = list_containers(all_containers=True) if target in {"containers", "all"} else []

    extra: list[str] = [f"target: {target}"]
    if preview_containers:
        extra.append(f"containers_to_remove: {len(preview_containers)}")
        extra.extend(_container_preview(preview_containers))
    if target in {"images", "all"}:
        extra.append(f"image_prune: {'all unused' if all_images else 'dangling only'}")
    if target in {"cache", "all"}:
        extra.append("build_cache: prune")

    require_write_gate(
        "docker-clean",
        summary_lines=["intent: docker cleanup"],
        question=f"Run docker clean {target}?",
        yes=yes,
        extra_lines=extra,
    )

    if target in {"containers", "all"}:
        removed = remove_containers()
        rprint(f"[green]removed[/green] {len(removed)} container(s)")
    if target in {"images", "all"}:
        out = prune_images(all_unused=all_images)
        if out:
            rprint(out)
        rprint("[green]image prune[/green] complete")
    if target in {"cache", "all"}:
        out = prune_build_cache()
        if out:
            rprint(out)
        rprint("[green]build cache prune[/green] complete")
