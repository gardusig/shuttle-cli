"""Multi-step workflow integration checks (start, push, reset)."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.integration.git_mocks import patch_remote_git
from shuttle.integration.public_endpoints import (
    FEATURE_BRANCH,
    _push_cwd,
    dirty_integration_git,
    prepare_git_repo,
    reset_integration_git,
    setup_feature_branch,
)

_CLI_RUNNER = CliRunner()


def _git(git_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(git_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def invoke_workflow(
    repo_root: Path,
    git_root: Path,
    cli_args: tuple[str, ...],
) -> tuple[int, str]:
    """Run shuttle CLI against disposable git_root with remote git mocked."""
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env["SHUTTLE_GIT_ROOT"] = str(git_root)
    with patch_remote_git(), _push_cwd(repo_root):
        result = _CLI_RUNNER.invoke(app, list(cli_args), env=env)
    return result.exit_code, result.stdout + (result.stderr or "")


def _current_branch(git_root: Path) -> str:
    return _git(git_root, "branch", "--show-current").stdout.strip()


def _is_dirty(git_root: Path) -> bool:
    return bool(_git(git_root, "status", "--short").stdout.strip())


def _local_branches(git_root: Path) -> set[str]:
    out = _git(git_root, "branch", "--format=%(refname:short)").stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def _main_matches_origin(git_root: Path) -> bool:
    local = _git(git_root, "rev-parse", "main").stdout.strip()
    remote = _git(git_root, "rev-parse", "origin/main").stdout.strip()
    return local == remote


def setup_nested_merged_branches(git_root: Path) -> tuple[str, str]:
    """Branch chain main → feature-a → feature-b (both merged), plus unmerged feature-c.

    Returns (merged_leaf, unmerged_tip) branch names.
    """
    merged_a = "feature-a"
    merged_b = "feature-b"
    unmerged = "feature-c"
    _git(git_root, "checkout", "main")
    _git(git_root, "checkout", "-b", merged_a)
    _git(git_root, "commit", "--allow-empty", "-m", "feature a")
    _git(git_root, "checkout", "-b", merged_b)
    _git(git_root, "commit", "--allow-empty", "-m", "feature b")
    _git(git_root, "checkout", "main")
    _git(git_root, "merge", merged_a, "--no-edit")
    _git(git_root, "merge", merged_b, "--no-edit")
    _git(git_root, "checkout", "-b", unmerged, merged_b)
    _git(git_root, "commit", "--allow-empty", "-m", "feature c")
    _git(git_root, "push", "origin", "main")
    return merged_b, unmerged


def _commit_on_branch(git_root: Path, branch: str, *, filename: str, message: str) -> None:
    _git(git_root, "checkout", "-b", branch)
    path = git_root / filename
    path.write_text(f"{message}\n", encoding="utf-8")
    _git(git_root, "add", filename)
    _git(git_root, "commit", "-m", message)


def _invoke_reset(
    repo_root: Path,
    git_root: Path,
    errors: list[str],
    *,
    prefix: str,
    cli_args: tuple[str, ...],
) -> bool:
    """Run reset; append errors and return False on failure."""
    code, output = invoke_workflow(repo_root, git_root, cli_args)
    if code != 0:
        errors.append(f"{prefix}: exit {code}\n{output}")
        return False
    if "reset" not in output:
        errors.append(f"{prefix}: missing success message\n{output}")
        return False
    return True


def _assert_on_synced_main(git_root: Path, errors: list[str], *, prefix: str) -> None:
    if _current_branch(git_root) != "main":
        errors.append(f"{prefix}: expected main, got {_current_branch(git_root)!r}")
    if _is_dirty(git_root):
        errors.append(f"{prefix}: expected clean tree after reset")
    if not _main_matches_origin(git_root):
        errors.append(f"{prefix}: expected main to match origin/main")


def _assert_branches(
    git_root: Path,
    errors: list[str],
    *,
    prefix: str,
    gone: set[str] | None = None,
    kept: set[str] | None = None,
    only_main: bool = False,
) -> None:
    branches = _local_branches(git_root)
    if only_main and branches != {"main"}:
        errors.append(f"{prefix}: expected only main, got {sorted(branches)!r}")
    for name in gone or set():
        if name in branches:
            errors.append(f"{prefix}: expected branch {name!r} deleted")
    for name in kept or set():
        if name not in branches:
            errors.append(f"{prefix}: expected branch {name!r} to remain")


def check_reset_from_clean_main(git_root: Path, repo_root: Path) -> list[str]:
    """On clean main → reset --main-only --yes → synced main, branches unchanged."""
    errors: list[str] = []
    reset_integration_git(git_root)
    before = _local_branches(git_root)
    if _current_branch(git_root) != "main" or _is_dirty(git_root):
        return ["reset from main setup: expected clean main"]

    if not _invoke_reset(
        repo_root,
        git_root,
        errors,
        prefix="reset from clean main",
        cli_args=("git", "reset", "--yes", "--main-only"),
    ):
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset from clean main")
    if _local_branches(git_root) != before:
        errors.append("reset from clean main: expected local branches unchanged")
    return errors


def check_reset_from_dirty_main(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty main → reset --main-only --yes → synced main, dirty work discarded."""
    errors: list[str] = []
    reset_integration_git(git_root)
    dirty_integration_git(git_root)
    if not _is_dirty(git_root):
        return ["reset from dirty main setup: expected dirty tree"]

    if not _invoke_reset(
        repo_root,
        git_root,
        errors,
        prefix="reset from dirty main",
        cli_args=("git", "reset", "--yes", "--main-only"),
    ):
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset from dirty main")
    return errors


def check_reset_from_clean_merged_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On clean merged branch → reset --yes → synced main, merged branch pruned."""
    errors: list[str] = []
    reset_integration_git(git_root)
    setup_feature_branch(git_root, "merged")
    _git(git_root, "push", "origin", "main")
    _git(git_root, "checkout", FEATURE_BRANCH)
    if _is_dirty(git_root):
        return ["reset from merged setup: expected clean tree"]

    if not _invoke_reset(
        repo_root,
        git_root,
        errors,
        prefix="reset from clean merged branch",
        cli_args=("git", "reset", "--yes"),
    ):
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset from clean merged branch")
    _assert_branches(
        git_root,
        errors,
        prefix="reset from clean merged branch",
        gone={FEATURE_BRANCH},
    )
    return errors


def check_reset_from_dirty_merged_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty merged branch → reset --yes --discard → synced main, branch pruned."""
    errors: list[str] = []
    reset_integration_git(git_root)
    setup_feature_branch(git_root, "merged")
    _git(git_root, "push", "origin", "main")
    _git(git_root, "checkout", FEATURE_BRANCH)
    dirty_integration_git(git_root)
    if not _is_dirty(git_root):
        return ["reset from dirty merged setup: expected dirty tree"]

    if not _invoke_reset(
        repo_root,
        git_root,
        errors,
        prefix="reset from dirty merged branch",
        cli_args=("git", "reset", "--yes", "--discard"),
    ):
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset from dirty merged branch")
    _assert_branches(
        git_root,
        errors,
        prefix="reset from dirty merged branch",
        gone={FEATURE_BRANCH},
    )
    return errors


def check_reset_from_committed_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On committed alternate branch → reset --main-only --yes → synced main, branch kept."""
    errors: list[str] = []
    branch = "stale-feature"
    message = "work on stale branch"
    reset_integration_git(git_root)
    _commit_on_branch(git_root, branch, filename="stale-work.txt", message=message)
    if _current_branch(git_root) != branch:
        return ["reset from committed branch setup: expected alternate branch"]

    if not _invoke_reset(
        repo_root,
        git_root,
        errors,
        prefix="reset from committed branch",
        cli_args=("git", "reset", "--yes", "--main-only"),
    ):
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset from committed branch")
    _assert_branches(git_root, errors, prefix="reset from committed branch", kept={branch})
    log = _git(git_root, "log", branch, "-1", "--format=%s").stdout.strip()
    if log != message:
        errors.append(
            f"reset from committed branch: expected commit {message!r}, got {log!r}"
        )
    return errors


def check_reset_from_dirty_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty alternate branch → reset --main-only --yes → commit on branch, synced main."""
    errors: list[str] = []
    branch = "wip-dirty-reset"
    reset_integration_git(git_root)
    _git(git_root, "checkout", "-b", branch)
    dirty_integration_git(git_root)
    if not _is_dirty(git_root):
        return ["reset from dirty branch setup: expected dirty tree"]

    if not _invoke_reset(
        repo_root,
        git_root,
        errors,
        prefix="reset from dirty branch",
        cli_args=("git", "reset", "--yes", "--main-only"),
    ):
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset from dirty branch")
    _assert_branches(git_root, errors, prefix="reset from dirty branch", kept={branch})
    log = _git(git_root, "log", branch, "-1", "--format=%s").stdout.strip()
    if log != ".":
        errors.append(f"reset from dirty branch: expected commit '.', got {log!r}")
    return errors


def check_reset_from_nested_branches(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty nested tip → reset --yes → synced main, merged chain pruned, tip kept."""
    errors: list[str] = []
    reset_integration_git(git_root)
    merged_b, unmerged = setup_nested_merged_branches(git_root)
    _git(git_root, "checkout", unmerged)
    dirty_integration_git(git_root)
    if not _is_dirty(git_root) or merged_b not in _local_branches(git_root):
        return ["reset from nested setup: expected dirty tree on nested tip"]

    if not _invoke_reset(
        repo_root,
        git_root,
        errors,
        prefix="reset from nested branches",
        cli_args=("git", "reset", "--yes"),
    ):
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset from nested branches")
    _assert_branches(
        git_root,
        errors,
        prefix="reset from nested branches",
        gone={"feature-a", merged_b},
        kept={unmerged},
    )
    return errors


def check_reset_all_local_from_nested(git_root: Path, repo_root: Path) -> list[str]:
    """On nested tip → reset --all-local --yes → synced main, every branch except main gone."""
    errors: list[str] = []
    reset_integration_git(git_root)
    _merged_b, unmerged = setup_nested_merged_branches(git_root)
    _git(git_root, "checkout", unmerged)

    if not _invoke_reset(
        repo_root,
        git_root,
        errors,
        prefix="reset all-local from nested",
        cli_args=("git", "reset", "--yes", "--all-local"),
    ):
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset all-local from nested")
    _assert_branches(git_root, errors, prefix="reset all-local from nested", only_main=True)
    return errors


def _invoke_start(
    repo_root: Path,
    git_root: Path,
    errors: list[str],
    *,
    prefix: str,
    branch: str,
) -> bool:
    code, output = invoke_workflow(repo_root, git_root, ("git", "start", branch, "--yes"))
    if code != 0:
        errors.append(f"{prefix}: exit {code}\n{output}")
        return False
    if "started" not in output:
        errors.append(f"{prefix}: missing success message\n{output}")
        return False
    return True


def _assert_started_on_main_tip(
    git_root: Path,
    errors: list[str],
    *,
    prefix: str,
    branch: str,
    prior_branches: set[str] | None = None,
    prior_commit: tuple[str, str] | None = None,
    absent_paths: tuple[str, ...] = (),
) -> None:
    if _current_branch(git_root) != branch:
        errors.append(f"{prefix}: expected {branch!r}, got {_current_branch(git_root)!r}")
    if _is_dirty(git_root):
        errors.append(f"{prefix}: expected clean tree after start")
    if not _main_matches_origin(git_root):
        errors.append(f"{prefix}: expected main to match origin/main")
    main_sha = _git(git_root, "rev-parse", "main").stdout.strip()
    branch_sha = _git(git_root, "rev-parse", branch).stdout.strip()
    if main_sha != branch_sha:
        errors.append(f"{prefix}: expected new branch tip to match main")
    if prior_branches is not None:
        for name in prior_branches:
            if name not in _local_branches(git_root):
                errors.append(f"{prefix}: expected prior branch {name!r} to remain")
    if prior_commit is not None:
        prior_branch, message = prior_commit
        log = _git(git_root, "log", prior_branch, "-1", "--format=%s").stdout.strip()
        if log != message:
            errors.append(f"{prefix}: expected {prior_branch!r} commit {message!r}, got {log!r}")
    for rel in absent_paths:
        if (git_root / rel).exists():
            errors.append(f"{prefix}: expected {rel!r} absent on new branch")


def check_start_from_clean_main(git_root: Path, repo_root: Path) -> list[str]:
    """On clean main → start issue branch --yes → new branch from aligned main."""
    errors: list[str] = []
    branch = "issue-9-from-main"
    reset_integration_git(git_root)
    if _current_branch(git_root) != "main" or _is_dirty(git_root):
        return ["start from clean main setup: expected clean main"]

    if not _invoke_start(
        repo_root, git_root, errors, prefix="start from clean main", branch=branch
    ):
        return errors
    _assert_started_on_main_tip(git_root, errors, prefix="start from clean main", branch=branch)
    return errors


def check_start_from_dirty_main(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty main → start issue branch --yes → prep syncs main, new branch from main."""
    errors: list[str] = []
    branch = "issue-9-from-dirty-main"
    reset_integration_git(git_root)
    dirty_integration_git(git_root)
    if _current_branch(git_root) != "main" or not _is_dirty(git_root):
        return ["start from dirty main setup: expected dirty main"]

    if not _invoke_start(
        repo_root, git_root, errors, prefix="start from dirty main", branch=branch
    ):
        return errors
    _assert_started_on_main_tip(git_root, errors, prefix="start from dirty main", branch=branch)
    return errors


def check_start_from_committed_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On committed feature branch → start --yes → new branch from main, prior branch kept."""
    errors: list[str] = []
    prior_branch = "stale-feature"
    prior_message = "work on stale branch"
    branch = "issue-10-from-branch"
    reset_integration_git(git_root)
    _commit_on_branch(
        git_root,
        prior_branch,
        filename="stale-work.txt",
        message=prior_message,
    )
    if _current_branch(git_root) != prior_branch:
        return ["start from committed branch setup: expected feature branch"]

    if not _invoke_start(
        repo_root, git_root, errors, prefix="start from committed branch", branch=branch
    ):
        return errors
    _assert_started_on_main_tip(
        git_root,
        errors,
        prefix="start from committed branch",
        branch=branch,
        prior_branches={prior_branch},
        prior_commit=(prior_branch, prior_message),
        absent_paths=("stale-work.txt",),
    )
    return errors


def check_start_from_dirty_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty feature branch → start --yes → prep aligns main, new branch from main."""
    errors: list[str] = []
    prior_branch = "wip-dirty-start"
    branch = "issue-11-from-dirty-branch"
    reset_integration_git(git_root)
    _git(git_root, "checkout", "-b", prior_branch)
    dirty_integration_git(git_root)
    if _current_branch(git_root) != prior_branch or not _is_dirty(git_root):
        return ["start from dirty branch setup: expected dirty feature branch"]

    if not _invoke_start(
        repo_root, git_root, errors, prefix="start from dirty branch", branch=branch
    ):
        return errors
    _assert_started_on_main_tip(
        git_root,
        errors,
        prefix="start from dirty branch",
        branch=branch,
        prior_branches={prior_branch},
    )
    return errors


def check_start_from_nested_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On nested branch tip → start --yes → new branch from main, nested chain kept."""
    errors: list[str] = []
    branch = "issue-12-from-nested"
    reset_integration_git(git_root)
    _merged_b, unmerged = setup_nested_merged_branches(git_root)
    _git(git_root, "checkout", unmerged)
    dirty_integration_git(git_root)
    if _current_branch(git_root) != unmerged:
        return ["start from nested setup: expected nested tip branch"]

    if not _invoke_start(
        repo_root, git_root, errors, prefix="start from nested branch", branch=branch
    ):
        return errors
    _assert_started_on_main_tip(
        git_root,
        errors,
        prefix="start from nested branch",
        branch=branch,
        prior_branches={"feature-a", _merged_b, unmerged},
    )
    return errors


def _assert_push_gate(
    output: str,
    errors: list[str],
    *,
    prefix: str,
    from_main: bool,
    branch: str | None = None,
) -> None:
    """Write gate must describe start-first on main vs push on current branch."""
    if from_main:
        for needle in (
            "from_branch: main",
            "target_branch: wip-",
            "intent: start 'wip-",
        ):
            if needle not in output:
                errors.append(f"{prefix}: gate missing {needle!r}\n{output}")
        if "Push changes from 'main'" in output:
            errors.append(f"{prefix}: gate must not offer direct push from main\n{output}")
        return

    if "from_branch: main" in output or "target_branch: wip-" in output:
        errors.append(f"{prefix}: gate must not start a branch when already on feature branch\n{output}")
    if "intent: git add -A → commit → push origin HEAD" not in output:
        errors.append(f"{prefix}: gate missing branch push intent\n{output}")
    if branch is not None and f"branch: {branch}" not in output:
        errors.append(f"{prefix}: gate missing branch {branch!r}\n{output}")


def _invoke_push(
    repo_root: Path,
    git_root: Path,
    errors: list[str],
    *,
    prefix: str,
    message: str = ".",
    extra_args: tuple[str, ...] = (),
    from_main: bool | None = None,
    branch: str | None = None,
) -> tuple[bool, str]:
    code, output = invoke_workflow(
        repo_root,
        git_root,
        ("git", "push", "--yes", "-m", message, *extra_args),
    )
    if code != 0:
        errors.append(f"{prefix}: exit {code}\n{output}")
        return False, output
    if "pushed" not in output:
        errors.append(f"{prefix}: missing success message\n{output}")
        return False, output
    if from_main is not None:
        _assert_push_gate(output, errors, prefix=prefix, from_main=from_main, branch=branch)
    return True, output


def _assert_pushed(
    git_root: Path,
    errors: list[str],
    *,
    prefix: str,
    branch: str | None,
    message: str | None = None,
    leave_main: bool = False,
) -> None:
    current = _current_branch(git_root)
    if leave_main:
        if current == "main":
            errors.append(f"{prefix}: expected to leave main, still on main")
        if not current.startswith("wip-"):
            errors.append(f"{prefix}: expected auto wip- branch, got {current!r}")
    elif branch is not None and current != branch:
        errors.append(f"{prefix}: expected {branch!r}, got {current!r}")
    if _is_dirty(git_root):
        errors.append(f"{prefix}: expected clean tree after push")
    if message is not None:
        log = _git(git_root, "log", "-1", "--format=%s").stdout.strip()
        if log != message:
            errors.append(f"{prefix}: expected commit {message!r}, got {log!r}")


def check_push_from_dirty_main(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty main → push --yes → auto branch, commit, push."""
    errors: list[str] = []
    message = "push from main"
    reset_integration_git(git_root)
    dirty_integration_git(git_root)
    if _current_branch(git_root) != "main" or not _is_dirty(git_root):
        return ["push from dirty main setup: expected dirty main"]

    ok, _output = _invoke_push(
        repo_root,
        git_root,
        errors,
        prefix="push from dirty main",
        message=message,
        from_main=True,
    )
    if not ok:
        return errors
    _assert_pushed(
        git_root,
        errors,
        prefix="push from dirty main",
        branch=None,
        message=message,
        leave_main=True,
    )
    return errors


def check_push_from_dirty_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty feature branch → push --yes → commit and push on same branch."""
    errors: list[str] = []
    branch = "wip-push-branch"
    message = "push from branch"
    reset_integration_git(git_root)
    _git(git_root, "checkout", "-b", branch)
    dirty_integration_git(git_root)
    if not _is_dirty(git_root):
        return ["push from dirty branch setup: expected dirty tree"]

    ok, _output = _invoke_push(
        repo_root,
        git_root,
        errors,
        prefix="push from dirty branch",
        message=message,
        from_main=False,
        branch=branch,
    )
    if not ok:
        return errors
    _assert_pushed(
        git_root,
        errors,
        prefix="push from dirty branch",
        branch=branch,
        message=message,
    )
    return errors


def check_push_from_nested_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On dirty nested tip → push --yes → commit and push on nested branch."""
    errors: list[str] = []
    message = "push from nested"
    reset_integration_git(git_root)
    _merged_b, unmerged = setup_nested_merged_branches(git_root)
    _git(git_root, "checkout", unmerged)
    dirty_integration_git(git_root)
    if _current_branch(git_root) != unmerged or not _is_dirty(git_root):
        return ["push from nested setup: expected dirty nested tip"]

    ok, _output = _invoke_push(
        repo_root,
        git_root,
        errors,
        prefix="push from nested branch",
        message=message,
        from_main=False,
        branch=unmerged,
    )
    if not ok:
        return errors
    _assert_pushed(
        git_root,
        errors,
        prefix="push from nested branch",
        branch=unmerged,
        message=message,
    )
    for name in ("feature-a", _merged_b, unmerged):
        if name not in _local_branches(git_root):
            errors.append(f"push from nested branch: expected branch {name!r} to remain")
    return errors


def check_push_from_clean_branch(git_root: Path, repo_root: Path) -> list[str]:
    """On clean committed branch → push --yes → push existing commit, no new commit."""
    errors: list[str] = []
    branch = "feat-push-clean"
    commit_message = "existing work"
    reset_integration_git(git_root)
    _commit_on_branch(
        git_root,
        branch,
        filename="push-clean.txt",
        message=commit_message,
    )
    if _is_dirty(git_root):
        return ["push from clean branch setup: expected clean tree"]

    ok, _output = _invoke_push(
        repo_root,
        git_root,
        errors,
        prefix="push from clean branch",
        message=".",
        from_main=False,
        branch=branch,
    )
    if not ok:
        return errors
    _assert_pushed(
        git_root,
        errors,
        prefix="push from clean branch",
        branch=branch,
        message=commit_message,
    )
    return errors


def check_push_from_clean_main(git_root: Path, repo_root: Path) -> list[str]:
    """On clean main → push --yes → new wip branch, no extra commit, push HEAD."""
    errors: list[str] = []
    reset_integration_git(git_root)
    if _current_branch(git_root) != "main" or _is_dirty(git_root):
        return ["push from clean main setup: expected clean main"]

    ok, _output = _invoke_push(
        repo_root,
        git_root,
        errors,
        prefix="push from clean main",
        message=".",
        from_main=True,
    )
    if not ok:
        return errors
    _assert_pushed(
        git_root,
        errors,
        prefix="push from clean main",
        branch=None,
        message=None,
        leave_main=True,
    )
    return errors


RESET_WORKFLOW_CHECKS: tuple[tuple[str, Callable[[Path, Path], list[str]]], ...] = (
    ("reset from clean main", check_reset_from_clean_main),
    ("reset from dirty main", check_reset_from_dirty_main),
    ("reset from clean merged branch", check_reset_from_clean_merged_branch),
    ("reset from dirty merged branch", check_reset_from_dirty_merged_branch),
    ("reset from committed branch", check_reset_from_committed_branch),
    ("reset from dirty branch", check_reset_from_dirty_branch),
    ("reset from nested branches", check_reset_from_nested_branches),
    ("reset all-local from nested", check_reset_all_local_from_nested),
)

START_WORKFLOW_CHECKS: tuple[tuple[str, Callable[[Path, Path], list[str]]], ...] = (
    ("start from clean main", check_start_from_clean_main),
    ("start from dirty main", check_start_from_dirty_main),
    ("start from committed branch", check_start_from_committed_branch),
    ("start from dirty branch", check_start_from_dirty_branch),
    ("start from nested branch", check_start_from_nested_branch),
)

PUSH_WORKFLOW_CHECKS: tuple[tuple[str, Callable[[Path, Path], list[str]]], ...] = (
    ("push from dirty main", check_push_from_dirty_main),
    ("push from clean main", check_push_from_clean_main),
    ("push from dirty branch", check_push_from_dirty_branch),
    ("push from nested branch", check_push_from_nested_branch),
    ("push from clean branch", check_push_from_clean_branch),
)

WORKFLOW_CHECKS: tuple[tuple[str, Callable[[Path, Path], list[str]]], ...] = (
    *RESET_WORKFLOW_CHECKS,
    *START_WORKFLOW_CHECKS,
    *PUSH_WORKFLOW_CHECKS,
)


def run_all_workflow_checks(repo_root: Path, git_root: Path) -> list[str]:
    """Run every workflow scenario; return error messages (empty if all passed)."""
    errors: list[str] = []
    for label, check in WORKFLOW_CHECKS:
        scenario_errors = check(git_root, repo_root)
        for msg in scenario_errors:
            errors.append(f"{label}: {msg}")
        reset_integration_git(git_root)
    return errors


def prepare_workflow_git(path: Path) -> None:
    """Disposable repo for workflow integration (local origin remote)."""
    prepare_git_repo(path)
