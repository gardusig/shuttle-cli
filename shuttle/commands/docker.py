"""Docker container and image shortcuts."""

from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from shuttle.internal.write.gate import require_write_gate
from shuttle.services.docker_runtime import (
    ContainerRow,
    ImageRow,
    docker_available,
    format_bytes,
    list_containers,
    list_images,
    prune_build_cache,
    prune_images,
    remove_all_containers,
    system_df,
)

docker_app = typer.Typer(
    help="Docker containers and images (list, top, clean).",
    no_args_is_help=True,
)


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


def _print_image_table(rows: list[ImageRow], *, title: str) -> None:
    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("SIZE", justify="right")
    table.add_column("IMAGE")
    table.add_column("ID")
    for row in rows:
        table.add_row(format_bytes(row.size), row.name, row.id)
    rprint(table)


@docker_app.command("ps")
def ps_cmd(
    top: int = typer.Option(20, "--top", "-n", help="Max rows to show."),
) -> None:
    """Running containers sorted by writable layer size."""
    if not docker_available():
        raise typer.Exit("docker is not installed or not on PATH")
    rows = list_containers(running_only=True)[:top]
    if not rows:
        rprint("[dim]no running containers[/dim]")
        return
    _print_container_table(rows, title="Running containers (by size)")


@docker_app.command("containers")
def containers_cmd(
    top: int = typer.Option(20, "--top", "-n", help="Max rows to show."),
    running: bool = typer.Option(False, "--running", help="Only running containers."),
) -> None:
    """All containers sorted by size (running and stopped)."""
    if not docker_available():
        raise typer.Exit("docker is not installed or not on PATH")
    rows = list_containers(all_containers=not running, running_only=running)[:top]
    if not rows:
        rprint("[dim]no containers[/dim]")
        return
    title = "Running containers (by size)" if running else "Containers (by size)"
    _print_container_table(rows, title=title)


@docker_app.command("images")
def images_cmd(
    top: int = typer.Option(20, "--top", "-n", help="Max rows to show."),
) -> None:
    """Images sorted by size."""
    if not docker_available():
        raise typer.Exit("docker is not installed or not on PATH")
    rows = list_images()[:top]
    if not rows:
        rprint("[dim]no images[/dim]")
        return
    _print_image_table(rows, title="Images (by size)")


@docker_app.command("top")
def top_cmd(
    n: int = typer.Option(10, "--top", "-n", help="Rows per section."),
) -> None:
    """Heaviest running containers, all containers, and images."""
    if not docker_available():
        raise typer.Exit("docker is not installed or not on PATH")
    running = list_containers(running_only=True)[:n]
    all_rows = list_containers(all_containers=True)[:n]
    images = list_images()[:n]
    if running:
        _print_container_table(running, title=f"Top {len(running)} running containers")
    else:
        rprint("[dim]no running containers[/dim]")
    if all_rows:
        rprint()
        _print_container_table(all_rows, title=f"Top {len(all_rows)} containers (all)")
    if images:
        rprint()
        _print_image_table(images, title=f"Top {len(images)} images")
    elif not running and not all_rows:
        rprint("[dim]no images[/dim]")


@docker_app.command("df")
def df_cmd() -> None:
    """Docker disk usage summary (docker system df)."""
    if not docker_available():
        raise typer.Exit("docker is not installed or not on PATH")
    rprint(system_df())


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
    """Remove containers and/or prune images and build cache."""
    if not docker_available():
        raise typer.Exit("docker is not installed or not on PATH")

    target = target.lower()
    if target not in {"containers", "images", "cache", "all"}:
        raise typer.BadParameter("target must be containers, images, cache, or all")

    preview_containers = list_containers(all_containers=True) if target in {"containers", "all"} else []
    preview_images = list_images() if target in {"images", "all"} else []

    extra: list[str] = [f"target: {target}"]
    if preview_containers:
        extra.append(f"containers_to_remove: {len(preview_containers)}")
        for row in preview_containers[:5]:
            extra.append(f"  - {row.display_name} ({row.status})")
        if len(preview_containers) > 5:
            extra.append(f"  ... ({len(preview_containers) - 5} more)")
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
        removed = remove_all_containers()
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
