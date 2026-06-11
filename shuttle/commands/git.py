from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich import print as rprint

from shuttle.internal.read.git import git_worktree_snapshot
from shuttle.internal.write.gate import WRITE_GATE_DELIMITER, require_write_gate
from shuttle.services.git_review import run_review
from shuttle.services.git_shortcuts import GitShortcuts
from shuttle.utils.config import project_root
from shuttle.utils.quick_defaults import default_tag_name, suggest_branch_name

git_app = typer.Typer(help="Git shortcuts (commit message defaults to '.').", no_args_is_help=True)


def _svc() -> GitShortcuts:
    return GitShortcuts()


def _branch_preview_lines(
    label: str,
    branches: list[str],
    *,
    prefix: str = "",
    limit: int = 20,
) -> list[str]:
    lines = [f"{label}: {len(branches)}"]
    for name in branches[:limit]:
        lines.append(f"  - {prefix}{name}")
    if len(branches) > limit:
        lines.append(f"  ... ({len(branches) - limit} more)")
    return lines


def _write_gate(
    operation: str,
    *,
    yes: bool = False,
    question: str | None = None,
    extra_lines: list[str] | None = None,
) -> None:
    """Read worktree snapshot, show delimiter, then Q&A before write."""
    snapshot = git_worktree_snapshot(_svc())
    require_write_gate(
        operation,
        snapshot.summary_lines(),
        question=question,
        yes=yes,
        extra_lines=extra_lines,
    )


@git_app.command("main")
def main_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Discard dirty tree and align."),
    keep_ignored: bool = typer.Option(False, "--keep-ignored", help="Use git clean -fd instead of -fdx."),
) -> None:
    """Align local main to canonical remote main."""
    _write_gate("main", yes=yes, question="Reset main to remote and clean working tree?")
    _svc().align_main(yes=True, keep_ignored=keep_ignored)
    rprint("[green]main aligned[/green]")


@git_app.command("pull")
def pull_cmd(
    merge_branch: str | None = typer.Option(None, "--merge", help="Named branch/ref to merge into current."),
) -> None:
    """Fetch and merge upstream + canonical main."""
    _svc().pull(merge_branch=merge_branch)
    rprint("[green]pull complete[/green]")


@git_app.command("commit")
def commit_cmd(
    message: str = typer.Option(".", "-m", "--message", help="Commit subject."),
    path: list[str] = typer.Option(None, "--path", help="Stage only these paths (repeatable)."),
) -> None:
    """Stage and commit (no-op if clean)."""
    created = _svc().commit(message, paths=path)
    if created:
        rprint(f"[green]committed[/green] ({message!r})")
    else:
        rprint("[yellow]nothing to commit[/yellow]")


@git_app.command("push")
def push_cmd(
    allow_main: bool = typer.Option(False, "--allow-main", help="Allow pushing from main."),
    message: str = typer.Option(".", "-m", "--message", help="Commit message if tree is dirty."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm push to remote."),
) -> None:
    """Commit if dirty, then push to origin."""
    _write_gate("push", yes=yes, question="Push current branch to remote?")
    _svc().push(allow_main=allow_main, message=message, yes=True)
    rprint("[green]pushed[/green]")


def _ship_intent_lines(svc: GitShortcuts, message: str, *, allow_main: bool) -> list[str]:
    branch = svc.current_branch()
    lines = [
        "intent: git add -A → commit → push origin HEAD",
        f"branch: {branch}",
        f"commit_message: {message!r}",
        f"dirty: {svc.is_dirty()}",
        f"remote: {'origin' if svc.remote_exists('origin') else '(none)'}",
    ]
    if branch == "main" and not allow_main:
        lines.append("warning: refusing main without --allow-main")
    return lines


@git_app.command("ship")
def ship_cmd(
    allow_main: bool = typer.Option(False, "--allow-main", help="Allow shipping from main."),
    message: str = typer.Option(".", "-m", "--message", help="Commit message for staged changes."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm ship (stage, commit, push)."),
) -> None:
    """Stage all, commit, and push — with branch summary confirmation first."""
    svc = _svc()
    branch = svc.current_branch()
    _write_gate(
        "ship",
        yes=yes,
        question=f"Ship changes from {branch!r} to origin?",
        extra_lines=_ship_intent_lines(svc, message, allow_main=allow_main),
    )
    svc.push(allow_main=allow_main, message=message, yes=True)
    rprint("[green]shipped[/green]")


def _prep_intent_lines(svc: GitShortcuts, *, keep_ignored: bool) -> list[str]:
    clean = "git clean -fd" if keep_ignored else "git clean -fdx"
    return [
        "intent: checkout main → fetch → reset --hard → " + clean,
        f"canonical_main: {svc.canonical_main_ref()}",
        f"dirty: {svc.is_dirty()}",
    ]


@git_app.command("prep")
def prep_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Discard dirty tree and align main."),
    keep_ignored: bool = typer.Option(False, "--keep-ignored", help="Use git clean -fd instead of -fdx."),
) -> None:
    """Before work: fresh local main (fetch, reset, clean)."""
    svc = _svc()
    _write_gate(
        "prep",
        yes=yes,
        question="Reset main to remote and clean working tree?",
        extra_lines=_prep_intent_lines(svc, keep_ignored=keep_ignored),
    )
    svc.prep(yes=True, keep_ignored=keep_ignored)
    rprint("[green]prep complete[/green] — on main, synced with remote")


@git_app.command("kick")
def kick_cmd(
    branch: str | None = typer.Argument(
        None,
        help="Branch name (default wip-YYMMDD-NNN; use issue slug e.g. issue-9-docker).",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm align main + new branch."),
    keep_ignored: bool = typer.Option(False, "--keep-ignored", help="Use git clean -fd instead of -fdx."),
) -> None:
    """Start issue work: align main, then create feature branch."""
    svc = _svc()
    branch_name = branch or suggest_branch_name(svc.local_branch_names(exclude_main=False))
    extra = [
        "intent: prep (align main) → git checkout -b",
        f"branch_to_create: {branch_name}",
        *_prep_intent_lines(svc, keep_ignored=keep_ignored),
    ]
    _write_gate(
        "kick",
        yes=yes,
        question=f"Prep main and start branch {branch_name!r}?",
        extra_lines=extra,
    )
    name = svc.kick(branch_name, yes=True, keep_ignored=keep_ignored)
    rprint(f"[green]kick[/green] on branch {name}")


def _land_intent_lines(svc: GitShortcuts, *, all_local: bool) -> list[str]:
    if all_local:
        branches = svc.local_branch_names(exclude_main=True)
        label = "local_branches_to_delete"
        mode = "all local branches except main"
    else:
        branches = svc.merged_branch_names(include_current=True)
        label = "merged_branches_to_delete"
        mode = "merged branches only"
    lines = [
        "intent: checkout main → fetch → reset --hard → clean → delete branches",
        f"delete_mode: {mode}",
        f"canonical_main: {svc.canonical_main_ref()}",
    ]
    lines.extend(_branch_preview_lines(label, branches))
    return lines


@git_app.command("land")
def land_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm post-merge cleanup."),
    all_local: bool = typer.Option(
        False,
        "--all-local",
        help="Delete every local branch except main (not only merged).",
    ),
    keep_ignored: bool = typer.Option(False, "--keep-ignored", help="Use git clean -fd instead of -fdx."),
) -> None:
    """After merge: return to main, sync, and remove feature branches."""
    svc = _svc()
    _write_gate(
        "land",
        yes=yes,
        question="Land on main and delete feature branches?",
        extra_lines=_land_intent_lines(svc, all_local=all_local),
    )
    deleted = svc.land(yes=True, all_local=all_local, keep_ignored=keep_ignored)
    rprint(f"[green]landed[/green] on main; removed {len(deleted)} branch(es)")


@git_app.command("start")
def start_cmd(
    branch: str | None = typer.Argument(None, help="Branch name (default wip-<timestamp>)."),
    align_main: bool = typer.Option(False, "--align-main", help="Align main before branching (destructive)."),
    no_push: bool = typer.Option(True, "--no-push/--push", help="Skip push after branch creation."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm destructive align or push."),
) -> None:
    """Create feature branch from current state (no reset/clean by default)."""
    if align_main:
        _write_gate(
            "start-align-main",
            yes=yes,
            question="Align main (reset/clean) before creating branch?",
        )
    if not no_push:
        _write_gate("start-push", yes=yes, question="Push new branch to remote?")
    name = _svc().start(
        branch,
        align_main=align_main,
        yes=yes,
        no_push=no_push,
    )
    rprint(f"[green]on branch[/green] {name}")


@git_app.command("stash")
def stash_cmd(
    action: str = typer.Argument("list", help="push|list|apply|pop|drop|clear"),
    message: str | None = typer.Option(None, "-m", "--message"),
    index: int = typer.Option(0, "--index", help="Stash index for apply/pop/drop."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Stash operations."""
    svc = _svc()
    if action == "push":
        svc.stash_push(message)
        rprint("[green]stashed[/green]")
    elif action == "list":
        rprint(svc.stash_list() or "(empty)")
    elif action == "apply":
        svc.stash_apply(index)
        rprint("[green]stash applied[/green]")
    elif action == "pop":
        svc.stash_pop(index)
        rprint("[green]stash popped[/green]")
    elif action == "drop":
        _write_gate("stash-drop", yes=yes, question="Drop stash entry?")
        svc.stash_drop(index, yes=True)
        rprint("[green]stash dropped[/green]")
    elif action == "clear":
        _write_gate("stash-clear", yes=yes, question="Clear all stashes?")
        svc.stash_clear(yes=True)
        rprint("[green]stash cleared[/green]")
    else:
        raise typer.BadParameter(f"Unknown stash action: {action}")


@git_app.command("branch")
def branch_cmd(
    action: str = typer.Argument("list", help="list|prune|delete|rename"),
    name: str | None = typer.Argument(None),
    new_name: str | None = typer.Option(None, "--rename", help="New name for rename."),
    force: bool = typer.Option(False, "--force", "-D"),
    remote: bool = typer.Option(True, "--remote/--no-remote"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Branch hygiene."""
    svc = _svc()
    if action == "list":
        rprint(svc.branch_list())
    elif action == "prune":
        svc.branch_prune()
        rprint("[green]pruned[/green]")
    elif action == "delete":
        if not name:
            raise typer.BadParameter("branch name required for delete")
        _write_gate(
            "branch-delete-action",
            yes=yes,
            question=f"Delete branch {name}?",
            extra_lines=[f"target_branch: {name}", f"force: {force}", f"remote: {remote}"],
        )
        svc.branch_delete(name, force=force, remote=remote, yes=True)
        rprint(f"[green]deleted[/green] {name}")
    elif action == "rename":
        if not new_name:
            raise typer.BadParameter("--rename NEW required")
        from shuttle.utils.process import run_git
        run_git(["branch", "-m", new_name], cwd=svc.top)
        rprint(f"[green]renamed to[/green] {new_name}")
    else:
        raise typer.BadParameter(f"Unknown branch action: {action}")


@git_app.command("branch-delete")
def branch_delete_cmd(
    name: str = typer.Argument(..., help="Branch to delete."),
    force: bool = typer.Option(False, "--force", "-D"),
    remote: bool = typer.Option(True, "--remote/--no-remote"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Delete one merged branch locally and on origin."""
    _write_gate(
        "branch-delete",
        yes=yes,
        question=f"Delete branch {name}?",
        extra_lines=[f"target_branch: {name}", f"force: {force}", f"remote: {remote}"],
    )
    _svc().branch_delete(name, force=force, remote=remote, yes=True)
    rprint(f"[green]deleted[/green] {name}")


@git_app.command("branch-delete-all")
def branch_delete_all_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Delete all merged local branches (and remotes)."""
    _write_gate("branch-delete-all", yes=yes, question="Delete all merged branches?")
    deleted = _svc().branch_delete_all_merged(yes=True)
    rprint(f"[green]deleted[/green] {len(deleted)} branches")


@git_app.command("branch-clear")
def branch_clear_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    keep_ignored: bool = typer.Option(
        False, "--keep-ignored", help="Use git clean -fd instead of -fdx."
    ),
    delete_remote: bool = typer.Option(
        False,
        "--delete-remote",
        help="Also delete remote branches on origin (non-interactive; requires --yes).",
    ),
) -> None:
    """Reset locally, checkout main, delete all branches except main."""
    svc = _svc()
    local_preview = svc.local_branch_names(exclude_main=True)
    _write_gate(
        "branch-clear",
        yes=yes,
        question=(
            "Reset working tree, checkout main, and delete ALL local branches except main?"
        ),
        extra_lines=[
            "warning: this clears everything locally",
            *_branch_preview_lines("local_branches_to_delete", local_preview),
        ],
    )
    local_deleted = svc.clear_branches_local(yes=True, keep_ignored=keep_ignored)
    rprint(f"[green]cleared[/green] {len(local_deleted)} local branch(es)")

    remote_preview = svc.remote_branch_names()
    if not remote_preview:
        return

    do_remote = False
    if delete_remote:
        if not sys.stdin.isatty() and not yes:
            raise typer.Exit("Pass --yes with --delete-remote in non-interactive mode.")
        if sys.stdin.isatty() and not yes:
            _write_gate(
                "branch-clear-remote",
                yes=False,
                question="Also delete ALL remote branches on origin (except main)?",
                extra_lines=_branch_preview_lines(
                    "remote_branches_to_delete",
                    remote_preview,
                    prefix="origin/",
                ),
            )
            do_remote = True
        else:
            do_remote = True
    elif sys.stdin.isatty():
        snapshot = git_worktree_snapshot(svc)
        typer.echo(WRITE_GATE_DELIMITER)
        typer.echo("operation: branch-clear-remote")
        for line in snapshot.summary_lines():
            typer.echo(line)
        for line in _branch_preview_lines(
            "remote_branches_to_delete",
            remote_preview,
            prefix="origin/",
        ):
            typer.echo(line)
        typer.echo(WRITE_GATE_DELIMITER)
        do_remote = typer.confirm(
            "Also delete ALL remote branches on origin (except main)?",
            default=False,
        )

    if do_remote:
        remote_deleted = svc.delete_remote_branches(yes=True)
        rprint(f"[green]deleted[/green] {len(remote_deleted)} remote branch(es)")


@git_app.command("post-merge-cleanup")
def post_merge_cleanup_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Align main and delete merged branches."""
    _write_gate(
        "post-merge-cleanup",
        yes=yes,
        question="Align main and delete merged branches?",
    )
    deleted = _svc().post_merge_cleanup(yes=True)
    rprint(f"[green]cleanup done[/green]; removed {len(deleted)} branches")


@git_app.command("rebase")
def rebase_cmd(
    onto: str | None = typer.Argument(None, help="Rebase onto ref (default canonical main)."),
    continue_: bool = typer.Option(False, "--continue", help="Continue rebase."),
    abort: bool = typer.Option(False, "--abort", help="Abort rebase."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Rebase current branch."""
    svc = _svc()
    if not (continue_ or abort):
        target = onto or svc.canonical_main_ref()
        _write_gate(
            "rebase",
            yes=yes,
            question=f"Rebase onto {target}?",
            extra_lines=[f"onto: {target}"],
        )
    svc.rebase(onto, continue_=continue_, abort=abort)
    rprint("[green]rebase step complete[/green]")


@git_app.command("reset")
def reset_cmd(
    target: str | None = typer.Argument(None, help="Reset target (default @{u} or canonical main)."),
    yes: bool = typer.Option(False, "--yes", "-y"),
    keep_ignored: bool = typer.Option(False, "--keep-ignored"),
) -> None:
    """Hard reset + clean current branch."""
    _write_gate(
        "reset",
        yes=yes,
        question="Hard reset and clean working tree?",
        extra_lines=[f"target: {target or '@{u} or canonical main'}"],
    )
    _svc().reset(target, yes=True, keep_ignored=keep_ignored)
    rprint("[green]reset complete[/green]")


@git_app.command("revert")
def revert_cmd(
    sha: str | None = typer.Argument(None),
    merge_parent: int | None = typer.Option(None, "-m", help="Merge parent for merge commits."),
    continue_: bool = typer.Option(False, "--continue"),
    abort: bool = typer.Option(False, "--abort"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Revert commit(s)."""
    if not sha and not (continue_ or abort):
        raise typer.BadParameter("sha required unless --continue/--abort")
    if sha and not (continue_ or abort):
        _write_gate(
            "revert",
            yes=yes,
            question=f"Revert commit {sha}?",
            extra_lines=[f"sha: {sha}"],
        )
    _svc().revert(sha or "", merge_parent=merge_parent, continue_=continue_, abort=abort)
    rprint("[green]revert step complete[/green]")


@git_app.command("cherry-pick")
def cherry_pick_cmd(
    sha: str | None = typer.Argument(None),
    continue_: bool = typer.Option(False, "--continue"),
    abort: bool = typer.Option(False, "--abort"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Cherry-pick onto current branch."""
    if not sha and not (continue_ or abort):
        raise typer.BadParameter("sha required unless --continue/--abort")
    if sha and not (continue_ or abort):
        _write_gate(
            "cherry-pick",
            yes=yes,
            question=f"Cherry-pick {sha}?",
            extra_lines=[f"sha: {sha}"],
        )
    _svc().cherry_pick(sha or "", continue_=continue_, abort=abort)
    rprint("[green]cherry-pick step complete[/green]")


@git_app.command("tag")
def tag_cmd(
    name: str | None = typer.Argument(None, help="Tag name (default today YYYY-MM-DD)."),
    push: bool = typer.Option(False, "--push", help="Push to origin (skips push prompt)."),
    no_push: bool = typer.Option(False, "--no-push", help="Never push to origin."),
    replace_local: bool = typer.Option(False, "--replace-local", help="Replace existing local tag."),
    force_push: bool = typer.Option(False, "--force-push", help="Force-push tag on origin."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Create annotated tag on HEAD (default name: today's date)."""
    svc = _svc()
    tag_name = name or default_tag_name()

    if svc.tag_exists_local(tag_name) and not replace_local:
        _write_gate(
            "tag-replace",
            yes=yes,
            question=f"Tag {tag_name} exists locally. Replace it?",
            extra_lines=[f"tag: {tag_name}"],
        )
        replace_local = True

    svc.create_tag(tag_name, replace=replace_local)

    should_push = False
    if not no_push and svc.remote_exists("origin"):
        if push:
            _write_gate(
                "tag-push",
                yes=yes,
                question=f"Push tag {tag_name} to origin?",
                extra_lines=[f"tag: {tag_name}"],
            )
            should_push = True
        elif sys.stdin.isatty() and not yes:
            snapshot = git_worktree_snapshot(svc)
            typer.echo(WRITE_GATE_DELIMITER)
            typer.echo("operation: tag-push")
            for line in snapshot.summary_lines():
                typer.echo(line)
            typer.echo(f"tag: {tag_name}")
            typer.echo(WRITE_GATE_DELIMITER)
            should_push = typer.confirm(f"Push tag {tag_name} to origin?", default=False)

    if should_push:
        use_force = force_push
        if svc.tag_exists_remote(tag_name):
            _write_gate(
                "tag-force-push",
                yes=yes or force_push,
                question=f"Tag {tag_name} exists on origin. Force-push?",
                extra_lines=[f"tag: {tag_name}", "remote: origin"],
            )
            use_force = True
        elif force_push:
            _write_gate(
                "tag-force-push",
                yes=yes,
                question=f"Force-push tag {tag_name} to origin?",
                extra_lines=[f"tag: {tag_name}"],
            )
        svc.push_tag(tag_name, force=use_force)

    rprint(f"[green]tag[/green] {tag_name}")


@git_app.command("zip")
def zip_cmd(
    tag: str | None = typer.Argument(None, help="Tag to archive (default today YYYY-MM-DD)."),
    output: Path | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Output zip path (default data/backups/TAG.zip).",
    ),
) -> None:
    """Create a zip archive of the tree at a git tag."""
    svc = _svc()
    tag_name = tag or default_tag_name()
    if not svc.tag_exists_local(tag_name):
        raise typer.Exit(f"Tag not found: {tag_name}. Run `shuttle git tag` first.")
    root = project_root()
    dest = output or (root / "data" / "backups" / f"{tag_name}.zip")
    archive = svc.zip_tag(tag_name, dest)
    rprint(f"[green]zip[/green] {archive.relative_to(root)}")


@git_app.command("review")
def review_cmd(
    no_install: bool = typer.Option(False, "--no-install", help="Skip bootstrap if venv missing."),
    quick: bool = typer.Option(
        False,
        "--quick",
        help="Shell syntax only; skip pytest (integration smoke).",
    ),
) -> None:
    """Workspace health: bootstrap, shell syntax checks, pytest (@git-review)."""
    code = run_review(install=not no_install, quick=quick)
    if code == 0:
        rprint("[green]review passed[/green]")
        raise typer.Exit()
    rprint("[red]review failed[/red]")
    raise typer.Exit(code=code)


@git_app.command("docs")
def docs_cmd() -> None:
    """List doc paths for sync (@git-docs; AI-driven edits via cursor-skills)."""
    root = project_root()
    docs_dir = root / "docs"
    readme = root / "README.md"
    rprint("[bold]Documentation inventory[/bold] (edit via cursor-skills @git-docs):")
    if readme.exists():
        rprint(f"  {readme.relative_to(root)}")
    if docs_dir.is_dir():
        for path in sorted(docs_dir.rglob("*.md")):
            rprint(f"  {path.relative_to(root)}")
    rprint("[dim]No files modified. Run @git-docs in Cursor for in-place doc updates.[/dim]")


@git_app.command("large-files")
def large_files_cmd(
    top_n: int = typer.Option(20, "-n", "--top"),
    worktree: bool = typer.Option(False, "--worktree", help="Scan worktree instead of tracked files."),
) -> None:
    """List largest files in the repo."""
    rows = _svc().large_files(top_n, worktree=worktree)
    for size, path in rows:
        rprint(f"{size:>12}  {path}")
