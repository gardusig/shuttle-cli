from __future__ import annotations

import typer
from rich import print as rprint

from shuttle.internal.read.git import git_worktree_snapshot
from shuttle.internal.write.gate import require_write_gate
from shuttle.services.git_review import run_review
from shuttle.services.git_shortcuts import GitShortcuts
from shuttle.utils.config import project_root

git_app = typer.Typer(help="Git shortcuts (commit message defaults to '.').", no_args_is_help=True)


def _svc() -> GitShortcuts:
    return GitShortcuts()


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
    name: str | None = typer.Argument(None, help="Tag name (default yyyy-mm-dd)."),
    push: bool = typer.Option(False, "--push", help="Push tag to origin."),
    replace_local: bool = typer.Option(False, "--replace-local"),
    force_push: bool = typer.Option(False, "--force-push"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Create annotated tag on synced main."""
    if force_push:
        _write_gate("tag-force-push", yes=yes, question="Force-push tag to remote?")
    elif push:
        _write_gate("tag-push", yes=yes, question="Push tag to remote?")
    elif replace_local:
        _write_gate("tag-replace", yes=yes, question="Replace existing local tag?")
    tag_name = _svc().tag(
        name,
        push=push,
        replace_local=replace_local,
        force_push=force_push,
        yes=yes,
    )
    rprint(f"[green]tag[/green] {tag_name}")


@git_app.command("review")
def review_cmd(
    no_install: bool = typer.Option(False, "--no-install", help="Skip bootstrap if venv missing."),
) -> None:
    """Workspace health: bootstrap, shell syntax checks, pytest (@git-review)."""
    code = run_review(install=not no_install)
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
