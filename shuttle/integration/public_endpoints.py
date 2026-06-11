"""Canonical registry of every public shuttle CLI endpoint for integration checks."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

FeatureBranchMode = Literal["none", "exists", "checked_out", "merged"]

from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.integration.git_mocks import patch_remote_git

_CLI_RUNNER = CliRunner()

CheckKind = Literal["ok", "refuse"]
REFUSE_NEEDLE = "non-interactive"
FEATURE_BRANCH = "integration-feature"


@dataclass(frozen=True)
class EndpointCheck:
    """One invocable public CLI surface."""

    label: str
    args: tuple[str, ...]
    kind: CheckKind = "ok"
    needle: str | None = None
    needs_git: bool = False
    reset_git: bool = False
    dirty_git: bool = False
    ensure_stash: bool = False
    feature_branch: FeatureBranchMode = "none"
    ensure_second_commit: bool = False
    accept_exit_codes: tuple[int, ...] = (0,)
    extra_env: dict[str, str] = field(default_factory=dict)


# Top-level groups (excluding hidden `g` alias — covered separately).
TOP_LEVEL_COMMANDS = (
    "links",
    "git",
    "backup",
    "restore",
    "drives",
    "notion",
    "bookmarks",
)

# Every `shuttle git <name>` subcommand from git_app.
GIT_SUBCOMMANDS = (
    "main",
    "pull",
    "commit",
    "push",
    "ship",
    "prep",
    "kickoff",
    "land",
    "start",
    "stash",
    "branch",
    "branch-delete",
    "branch-delete-all",
    "branch-clear",
    "post-merge-cleanup",
    "rebase",
    "reset",
    "revert",
    "cherry-pick",
    "tag",
    "zip",
    "review",
    "docs",
    "large-files",
)


def endpoint_checks() -> list[EndpointCheck]:
    """All integration checks in stable order."""
    refuse = REFUSE_NEEDLE
    checks: list[EndpointCheck] = [
        EndpointCheck("root --help", ("--help",), needle="git"),
        EndpointCheck("root --version", ("--version",), needle="0.1.0"),
        EndpointCheck("backup", ("backup",), needle="not implemented yet"),
        EndpointCheck("restore", ("restore",), needle="not implemented yet"),
        EndpointCheck("drives", ("drives",), needle="not implemented yet"),
        EndpointCheck("notion", ("notion",), needle="not implemented yet"),
        EndpointCheck("bookmarks", ("bookmarks",), needle="export-bookmarks.sh"),
        EndpointCheck("links", ("links",), needle="Quick defaults"),
        EndpointCheck(
            "git group help",
            ("git",),
            needle="start",
            accept_exit_codes=(0, 2),
        ),
        EndpointCheck("git --help", ("git", "--help"), needle="branch-clear"),
        EndpointCheck("hidden alias g commit", ("g", "commit"), needle="nothing to commit", needs_git=True, reset_git=True),
        EndpointCheck("git docs", ("git", "docs"), needle="Documentation"),
        EndpointCheck("git large-files", ("git", "large-files", "-n", "1"), needle="shuttle/"),
        EndpointCheck(
            "git review quick",
            ("git", "review", "--no-install", "--quick"),
            needle="review passed",
        ),
        EndpointCheck(
            "git commit",
            ("git", "commit"),
            needle="nothing to commit",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git branch list",
            ("git", "branch", "list"),
            needle="main",
            needs_git=True,
        ),
        EndpointCheck(
            "git stash list",
            ("git", "stash", "list"),
            needle="empty",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git stash push",
            ("git", "stash", "push"),
            needle="stashed",
            needs_git=True,
            reset_git=True,
            dirty_git=True,
        ),
        EndpointCheck(
            "git stash apply",
            ("git", "stash", "apply"),
            needle="stash applied",
            needs_git=True,
            ensure_stash=True,
        ),
        EndpointCheck(
            "git stash pop",
            ("git", "stash", "pop"),
            needle="stash popped",
            needs_git=True,
            ensure_stash=True,
        ),
        EndpointCheck(
            "git pull",
            ("git", "pull"),
            needle="pull complete",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git branch prune",
            ("git", "branch", "prune"),
            needle="pruned",
            needs_git=True,
        ),
        EndpointCheck(
            "git branch delete refuse",
            ("git", "branch", "delete", "integration-feature"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git start explicit",
            ("git", "start", "integration-feature"),
            needle="integration-feature",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git start auto",
            ("git", "start"),
            needle="on branch",
            needs_git=True,
        ),
        EndpointCheck(
            "git tag local",
            ("git", "tag", "integration-tag"),
            needle="integration-tag",
            needs_git=True,
        ),
        EndpointCheck(
            "git zip",
            ("git", "zip", "integration-tag"),
            needle=".zip",
            needs_git=True,
        ),
        # Write gates — must refuse without --yes in non-interactive mode.
        EndpointCheck("git push", ("git", "push"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck("git ship", ("git", "ship"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck("git prep", ("git", "prep"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck("git kickoff", ("git", "kickoff"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck("git land", ("git", "land"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck("git main", ("git", "main"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck("git reset", ("git", "reset"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck(
            "git branch-delete",
            ("git", "branch-delete", "integration-feature"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git branch-delete-all",
            ("git", "branch-delete-all"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git branch-clear",
            ("git", "branch-clear"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git post-merge-cleanup",
            ("git", "post-merge-cleanup"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git stash drop",
            ("git", "stash", "drop"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git stash clear",
            ("git", "stash", "clear"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck("git rebase", ("git", "rebase"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck(
            "git revert",
            ("git", "revert", "HEAD"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git cherry-pick",
            ("git", "cherry-pick", "HEAD"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git tag push refuse",
            ("git", "tag", "--push"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        # Gated writes with --yes (remote fetch/push/ls-remote mocked in run_all_endpoint_checks).
        EndpointCheck(
            "git push yes",
            ("git", "push", "--yes"),
            needle="pushed",
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
        ),
        EndpointCheck(
            "git ship yes",
            ("git", "ship", "--yes"),
            needle="shipped",
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
            dirty_git=True,
        ),
        EndpointCheck(
            "git prep yes",
            ("git", "prep", "--yes"),
            needle="prep complete",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git kickoff yes",
            ("git", "kickoff", "integration-kickoff", "--yes"),
            needle="kickoff",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git land yes",
            ("git", "land", "--yes"),
            needle="landed",
            needs_git=True,
            reset_git=True,
            feature_branch="merged",
        ),
        EndpointCheck(
            "git main yes",
            ("git", "main", "--yes"),
            needle="main aligned",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git reset yes",
            ("git", "reset", "--yes"),
            needle="reset complete",
            needs_git=True,
            reset_git=True,
            dirty_git=True,
        ),
        EndpointCheck(
            "git branch-delete yes",
            ("git", "branch-delete", "integration-feature", "--yes", "--no-remote"),
            needle="deleted",
            needs_git=True,
            reset_git=True,
            feature_branch="exists",
        ),
        EndpointCheck(
            "git branch delete yes",
            ("git", "branch", "delete", "integration-feature", "--yes", "--no-remote"),
            needle="deleted",
            needs_git=True,
            reset_git=True,
            feature_branch="exists",
        ),
        EndpointCheck(
            "git branch rename",
            ("git", "branch", "rename", "--rename", "integration-renamed"),
            needle="renamed",
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
        ),
        EndpointCheck(
            "git stash drop yes",
            ("git", "stash", "drop", "--yes"),
            needle="stash dropped",
            needs_git=True,
            ensure_stash=True,
        ),
        EndpointCheck(
            "git stash clear yes",
            ("git", "stash", "clear", "--yes"),
            needle="stash cleared",
            needs_git=True,
            ensure_stash=True,
        ),
        EndpointCheck(
            "git rebase yes",
            ("git", "rebase", "--yes"),
            needle="rebase step complete",
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
        ),
        EndpointCheck(
            "git revert yes",
            ("git", "revert", "HEAD", "--yes"),
            needle="revert step complete",
            needs_git=True,
            reset_git=True,
            ensure_second_commit=True,
        ),
        EndpointCheck(
            "git cherry-pick yes",
            ("git", "cherry-pick", FEATURE_BRANCH, "--yes"),
            needle="cherry-pick step complete",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git tag push yes",
            ("git", "tag", "integration-remote-tag", "--push", "--yes"),
            needle="integration-remote-tag",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git branch-delete-all yes",
            ("git", "branch-delete-all", "--yes"),
            needle="deleted",
            needs_git=True,
            reset_git=True,
            feature_branch="merged",
        ),
        EndpointCheck(
            "git branch-clear yes",
            ("git", "branch-clear", "--yes"),
            needle="cleared",
            needs_git=True,
            reset_git=True,
            feature_branch="exists",
        ),
        EndpointCheck(
            "git post-merge-cleanup yes",
            ("git", "post-merge-cleanup", "--yes"),
            needle="cleanup done",
            needs_git=True,
            reset_git=True,
            feature_branch="merged",
        ),
        EndpointCheck(
            "git start push yes",
            ("git", "start", "integration-push-branch", "--push", "--yes"),
            needle="integration-push-branch",
            needs_git=True,
            reset_git=True,
        ),
    ]
    return checks


def registered_git_subcommands() -> set[str]:
    names: set[str] = set()
    for cmd in app.registered_groups:
        if cmd.name in {"git", "g"}:
            for sub in cmd.typer_instance.registered_commands:
                names.add(sub.name or "")
    return {n for n in names if n}


def assert_registry_covers_git_commands() -> None:
    registered = registered_git_subcommands()
    expected = set(GIT_SUBCOMMANDS)
    missing = expected - registered
    extra = registered - expected
    if missing or extra:
        raise AssertionError(f"git registry drift: missing={sorted(missing)} extra={sorted(extra)}")


def _git_env() -> dict[str, str]:
    """Subprocess env without inherited GIT_DIR / GIT_WORK_TREE bleed."""
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def ensure_project_git(repo_root: Path) -> None:
    """Init repo_root when copied without .git (Docker integration workspace)."""
    if (repo_root / ".git").exists():
        return
    env = _git_env()
    git = ["git", "-C", str(repo_root)]
    subprocess.run(
        ["git", "config", "--global", "--add", "safe.directory", str(repo_root.resolve())],
        check=True,
        env=env,
    )
    subprocess.run([*git, "init", "-b", "main"], check=True, capture_output=True, env=env)
    subprocess.run([*git, "config", "user.email", "shuttle@example.test"], check=True, env=env)
    subprocess.run([*git, "config", "user.name", "Shuttle Test"], check=True, env=env)
    subprocess.run([*git, "add", "-A"], check=True, capture_output=True, env=env)
    subprocess.run(
        [*git, "commit", "-m", "integration snapshot"],
        check=True,
        capture_output=True,
        env=env,
    )


def prepare_git_repo(path: Path) -> None:
    """Disposable repo with local origin remote for SHUTTLE_GIT_ROOT checks."""
    path.mkdir(parents=True, exist_ok=True)
    bare = path.parent / f"{path.name}-origin.git"
    if bare.exists():
        shutil.rmtree(bare)
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "shuttle@example.test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Shuttle Integration"],
        check=True,
    )
    readme = path / "README.md"
    readme.write_text("integration\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-m", "initial"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "remote", "add", "origin", str(bare)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "push", "-u", "origin", "main"],
        check=True,
        capture_output=True,
    )


def dirty_integration_git(git_root: Path) -> None:
    """Uncommitted change so stash push creates an entry."""
    readme = git_root / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\n", encoding="utf-8")


def setup_feature_branch(git_root: Path, mode: FeatureBranchMode) -> None:
    """Prepare integration-feature branch for destructive CLI checks."""
    if mode == "none":
        return
    git = ["git", "-C", str(git_root)]
    subprocess.run([*git, "checkout", "-b", FEATURE_BRANCH], check=True, capture_output=True)
    if mode == "merged":
        subprocess.run([*git, "commit", "--allow-empty", "-m", "feature"], check=True, capture_output=True)
        subprocess.run([*git, "checkout", "main"], check=True, capture_output=True)
        subprocess.run([*git, "merge", FEATURE_BRANCH, "--no-edit"], check=True, capture_output=True)
    elif mode == "exists":
        subprocess.run([*git, "checkout", "main"], check=True, capture_output=True)
    # checked_out: stay on FEATURE_BRANCH


def add_second_commit(git_root: Path, *, on_feature: bool = False) -> None:
    """Add a commit on main (or current branch) for revert/cherry-pick checks."""
    git = ["git", "-C", str(git_root)]
    if not on_feature:
        subprocess.run([*git, "checkout", "main"], check=False, capture_output=True)
    marker = git_root / ("feature-marker.txt" if on_feature else "second-commit.txt")
    marker.write_text("marker\n", encoding="utf-8")
    subprocess.run([*git, "add", marker.name], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-m", "second"], check=True, capture_output=True)


def setup_cherry_pick(git_root: Path) -> None:
    """Feature branch with unique commit, then checkout main for cherry-pick."""
    setup_feature_branch(git_root, "checked_out")
    add_second_commit(git_root, on_feature=True)
    subprocess.run(
        ["git", "-C", str(git_root), "checkout", "main"],
        check=True,
        capture_output=True,
    )


def reset_integration_git(git_root: Path) -> None:
    """Return disposable repo to main with no extra branches or stashes."""
    subprocess.run(["git", "-C", str(git_root), "checkout", "main"], check=False, capture_output=True)
    subprocess.run(["git", "-C", str(git_root), "reset", "--hard"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(git_root), "clean", "-fd"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(git_root), "stash", "clear"], check=False, capture_output=True)
    result = subprocess.run(
        ["git", "-C", str(git_root), "branch", "--format=%(refname:short)"],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        name = line.strip()
        if name and name != "main":
            subprocess.run(
                ["git", "-C", str(git_root), "branch", "-D", name],
                check=False,
                capture_output=True,
            )


def git_subcommands_covered_by_checks() -> set[str]:
    covered: set[str] = set()
    for check in endpoint_checks():
        if not check.args or check.args[0] not in {"git", "g"}:
            continue
        if check.args[0] == "g":
            continue
        if len(check.args) == 1:
            continue
        sub = check.args[1]
        if sub.startswith("-"):
            continue
        covered.add(sub)
    return covered


def assert_every_git_subcommand_checked() -> None:
    missing = set(GIT_SUBCOMMANDS) - git_subcommands_covered_by_checks()
    if missing:
        raise AssertionError(f"integration checks missing git subcommands: {sorted(missing)}")


def git_subcommands_with_ok_check() -> set[str]:
    ok: set[str] = set()
    for check in endpoint_checks():
        if check.kind != "ok":
            continue
        if not check.args or check.args[0] != "git" or len(check.args) < 2:
            continue
        sub = check.args[1]
        if not sub.startswith("-"):
            ok.add(sub)
    return ok


def assert_every_git_subcommand_has_ok_check() -> None:
    """Every public git subcommand must have at least one successful integration path."""
    missing = set(GIT_SUBCOMMANDS) - git_subcommands_with_ok_check()
    if missing:
        raise AssertionError(f"git subcommands without ok integration check: {sorted(missing)}")


def assert_every_top_level_command_checked() -> None:
    for name in TOP_LEVEL_COMMANDS:
        if name == "git":
            if not any(c.label == "git group help" for c in endpoint_checks()):
                raise AssertionError("missing integration check for git group help")
            continue
        if not any(c.args and c.args[0] == name for c in endpoint_checks()):
            raise AssertionError(f"missing integration check for top-level command: {name}")


def ensure_stash_entry(repo_root: Path, git_root: Path) -> tuple[int, str]:
    """Reset, dirty tree, and stash push so apply/pop have an entry."""
    reset_integration_git(git_root)
    dirty_integration_git(git_root)
    return run_endpoint_check(
        EndpointCheck("stash setup", ("git", "stash", "push"), needs_git=True),
        repo_root=repo_root,
        git_root=git_root,
    )


def run_endpoint_check(
    check: EndpointCheck,
    *,
    repo_root: Path,
    git_root: Path | None,
) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    if check.needs_git and git_root is not None:
        env["SHUTTLE_GIT_ROOT"] = str(git_root)
    else:
        # Block SHUTTLE_GIT_ROOT bleed from Docker CI (whole-pytest env var).
        env.pop("SHUTTLE_GIT_ROOT", None)
        env["SHUTTLE_GIT_ROOT"] = ""
    env.update(check.extra_env)
    with _push_cwd(repo_root):
        result = _CLI_RUNNER.invoke(app, list(check.args), env=env)
    output = result.stdout + (result.stderr or "")
    return result.exit_code, output


class _push_cwd:
    """Temporarily chdir for git commands that resolve repo root from cwd."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous = Path.cwd()

    def __enter__(self) -> None:
        os.chdir(self.path)

    def __exit__(self, *args: object) -> None:
        os.chdir(self.previous)


def run_all_endpoint_checks(repo_root: Path, git_root: Path | None = None) -> list[str]:
    """Run every check; return error messages (empty if all passed)."""
    ensure_project_git(repo_root)
    assert_registry_covers_git_commands()
    assert_every_git_subcommand_checked()
    assert_every_git_subcommand_has_ok_check()
    assert_every_top_level_command_checked()
    errors: list[str] = []
    with patch_remote_git():
        for check in endpoint_checks():
            if check.reset_git and git_root is not None:
                reset_integration_git(git_root)
            if check.label == "git cherry-pick yes" and git_root is not None:
                setup_cherry_pick(git_root)
            elif git_root is not None and check.feature_branch != "none":
                setup_feature_branch(git_root, check.feature_branch)
            elif check.ensure_second_commit and git_root is not None:
                add_second_commit(git_root, on_feature=False)
            if check.dirty_git and git_root is not None:
                dirty_integration_git(git_root)
            if check.ensure_stash and git_root is not None:
                setup_code, setup_out = ensure_stash_entry(repo_root, git_root)
                if setup_code != 0:
                    errors.append(
                        f"{check.label} setup: stash push failed ({setup_code})\n{setup_out}"
                    )
                    continue
            code, output = run_endpoint_check(check, repo_root=repo_root, git_root=git_root)
            if check.kind == "ok":
                if code not in check.accept_exit_codes:
                    errors.append(
                        f"{check.label}: expected exit {check.accept_exit_codes}, got {code}\n{output}"
                    )
                    continue
            else:
                if code == 0:
                    errors.append(f"{check.label}: expected refusal, got exit 0\n{output}")
                    continue
            if check.needle and check.needle not in output:
                errors.append(f"{check.label}: missing needle {check.needle!r}\n{output}")
    return errors
