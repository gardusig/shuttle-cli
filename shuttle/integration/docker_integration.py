"""Integration checks for shuttle docker CLI commands."""

from __future__ import annotations

import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.integration.docker_mocks import patch_docker_cli

_CLI_RUNNER = CliRunner()
REFUSE_NEEDLE = "non-interactive"

DOCKER_SUBCOMMANDS = (
    "ps",
    "containers",
    "images",
    "top",
    "df",
    "clean",
)

CheckKind = Literal["ok", "refuse"]


@dataclass(frozen=True)
class DockerCheck:
    label: str
    args: tuple[str, ...]
    kind: CheckKind = "ok"
    needle: str | None = None


def docker_checks() -> list[DockerCheck]:
    refuse = REFUSE_NEEDLE
    return [
        DockerCheck("docker --help", ("docker", "--help"), needle="clean"),
        DockerCheck("docker ps", ("docker", "ps"), needle="shuttle-mock-running"),
        DockerCheck("docker containers", ("docker", "containers"), needle="shuttle-mock-stopped"),
        DockerCheck("docker images", ("docker", "images"), needle="shuttle/mock"),
        DockerCheck("docker top", ("docker", "top", "-n", "2"), needle="running containers"),
        DockerCheck("docker df", ("docker", "df"), needle="Images"),
        DockerCheck("docker clean refuse", ("docker", "clean", "containers"), kind="refuse", needle=refuse),
        DockerCheck(
            "docker clean containers yes",
            ("docker", "clean", "containers", "--yes"),
            needle="removed",
        ),
        DockerCheck(
            "docker clean images yes",
            ("docker", "clean", "images", "--yes"),
            needle="image prune",
        ),
    ]


def registered_docker_subcommands() -> set[str]:
    for group in app.registered_groups:
        if group.name == "docker":
            return {cmd.name or "" for cmd in group.typer_instance.registered_commands} - {""}
    return set()


def assert_docker_registry_covers_commands() -> None:
    registered = registered_docker_subcommands()
    expected = set(DOCKER_SUBCOMMANDS)
    missing = expected - registered
    extra = registered - expected
    if missing or extra:
        raise AssertionError(f"docker registry drift: missing={sorted(missing)} extra={sorted(extra)}")


def docker_subcommands_with_ok_check() -> set[str]:
    ok: set[str] = set()
    for check in docker_checks():
        if check.kind != "ok":
            continue
        if len(check.args) >= 2 and check.args[0] == "docker" and not check.args[1].startswith("-"):
            ok.add(check.args[1])
    return ok


def assert_docker_registry_complete() -> None:
    for sub in DOCKER_SUBCOMMANDS:
        if not any(c.args and len(c.args) >= 2 and c.args[1] == sub for c in docker_checks()):
            raise AssertionError(f"missing docker integration check for: {sub}")


def assert_every_docker_subcommand_has_ok_check() -> None:
    missing = set(DOCKER_SUBCOMMANDS) - docker_subcommands_with_ok_check()
    if missing:
        raise AssertionError(f"docker subcommands without ok integration check: {sorted(missing)}")


def run_docker_check(check: DockerCheck, *, repo_root: Path) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.pop("SHUTTLE_GIT_ROOT", None)
    prev = os.getcwd()
    try:
        os.chdir(repo_root)
        result = _CLI_RUNNER.invoke(app, list(check.args), env=env)
    finally:
        os.chdir(prev)
    return result.exit_code, result.stdout + (result.stderr or "")


def run_all_docker_checks(repo_root: Path) -> list[str]:
    assert_docker_registry_complete()
    errors: list[str] = []
    with patch_docker_cli():
        for check in docker_checks():
            code, output = run_docker_check(check, repo_root=repo_root)
            if check.kind == "ok":
                if code != 0:
                    errors.append(f"{check.label}: exit {code}\n{output}")
                    continue
            else:
                if code == 0:
                    errors.append(f"{check.label}: expected refusal, got exit 0\n{output}")
                    continue
            if check.needle and check.needle not in output:
                errors.append(f"{check.label}: missing needle {check.needle!r}\n{output}")
    return errors


_LIVE_CONTAINER = "shuttle-cli-integration-live"


def run_live_docker_checks(repo_root: Path) -> list[str]:
    """Exercise shuttle docker against the host daemon (ubuntu CI / local with Docker)."""
    errors: list[str] = []
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        return ["live docker: docker daemon not available"]

    tag = f"shuttle-cli-live:{uuid.uuid4().hex[:8]}"
    subprocess.run(["docker", "rm", "-f", _LIVE_CONTAINER], capture_output=True)
    subprocess.run(
        ["docker", "run", "-d", "--name", _LIVE_CONTAINER, "alpine", "sleep", "120"],
        check=True,
        capture_output=True,
    )
    subprocess.run(["docker", "pull", "-q", "alpine"], capture_output=True)
    try:
        live_checks = [
            DockerCheck("live docker ps", ("docker", "ps"), needle=_LIVE_CONTAINER),
            DockerCheck("live docker containers", ("docker", "containers", "--top", "5"), needle=_LIVE_CONTAINER),
            DockerCheck("live docker images", ("docker", "images", "--top", "5"), needle="alpine"),
            DockerCheck("live docker top", ("docker", "top", "-n", "3"), needle="running containers"),
            DockerCheck("live docker df", ("docker", "df"), needle="Images"),
            DockerCheck(
                "live docker clean refuse",
                ("docker", "clean", "containers"),
                kind="refuse",
                needle=REFUSE_NEEDLE,
            ),
        ]
        for check in live_checks:
            code, output = run_docker_check(check, repo_root=repo_root)
            if check.kind == "ok":
                if code != 0:
                    errors.append(f"{check.label}: exit {code}\n{output}")
                    continue
            else:
                if code == 0:
                    errors.append(f"{check.label}: expected refusal\n{output}")
                    continue
            if check.needle and check.needle not in output:
                errors.append(f"{check.label}: missing {check.needle!r}\n{output}")

        code, output = run_docker_check(
            DockerCheck("live docker clean containers", ("docker", "clean", "containers", "--yes"), needle="removed"),
            repo_root=repo_root,
        )
        if code != 0:
            errors.append(f"live docker clean: exit {code}\n{output}")
        elif _LIVE_CONTAINER in subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        ).stdout:
            errors.append("live docker clean: container still present after clean")
    finally:
        subprocess.run(["docker", "rm", "-f", _LIVE_CONTAINER], capture_output=True)
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)
    return errors
