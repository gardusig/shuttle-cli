"""GitHub (`gh`) subcommands — JSON-first, write gates."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from shuttle.internal.write.gate import require_write_gate
from shuttle.services.gh_service import GhService

gh_app = typer.Typer(help="GitHub via gh — issues, labels, PRs, backlog.", no_args_is_help=True)
issue_app = typer.Typer(help="Issue read/write.", no_args_is_help=True)
label_app = typer.Typer(help="Label read/write.", no_args_is_help=True)
pr_app = typer.Typer(help="Pull request read/write.", no_args_is_help=True)
backlog_app = typer.Typer(help="Backlog tree, next, resequence.", no_args_is_help=True)

gh_app.add_typer(issue_app, name="issue")
gh_app.add_typer(label_app, name="label")
gh_app.add_typer(pr_app, name="pr")
repo_app = typer.Typer(help="Repository metadata.", no_args_is_help=True)
gh_app.add_typer(repo_app, name="repo")
gh_app.add_typer(backlog_app, name="backlog")


def _svc(repo: str | None) -> GhService:
    return GhService(repo=repo)


def _emit(data: object, fmt: str) -> None:
    if fmt == "json":
        typer.echo(json.dumps(data, indent=2))
    else:
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    typer.echo(f"#{row.get('number', '?')} {row.get('title', row)}")
                else:
                    typer.echo(str(row))
        elif isinstance(data, dict):
            for k, v in data.items():
                typer.echo(f"{k}: {v}")
        else:
            typer.echo(str(data))


def _write_gate(
    operation: str,
    svc: GhService,
    *,
    yes: bool,
    question: str | None = None,
    extra_lines: list[str] | None = None,
) -> None:
    require_write_gate(
        operation,
        svc.snapshot_summary(),
        question=question,
        yes=yes,
        extra_lines=extra_lines,
    )


@gh_app.callback()
def gh_root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo", help="owner/name (default: gh context)"),
    format: str = typer.Option("json", "--format", help="json or table"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
    ctx.obj["format"] = format


def _ctx_repo(ctx: typer.Context) -> str | None:
    return (ctx.obj or {}).get("repo")


def _ctx_format(ctx: typer.Context) -> str:
    return (ctx.obj or {}).get("format") or "json"


# --- Issue read ---


@issue_app.command("list")
def issue_list_cmd(
    ctx: typer.Context,
    state: str = typer.Option("open", "--state"),
    label: list[str] = typer.Option(None, "--label"),
    limit: int = typer.Option(30, "--limit"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    data = svc.issue_list(state=state, label=label, limit=limit)
    _emit(data, _ctx_format(ctx))


@issue_app.command("view")
def issue_view_cmd(
    ctx: typer.Context,
    number: int,
    comments: bool = typer.Option(False, "--comments"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    data = svc.issue_view(number, comments=comments)
    _emit(data, _ctx_format(ctx))


@issue_app.command("search")
def issue_search_cmd(
    ctx: typer.Context,
    query: str,
    limit: int = typer.Option(30, "--limit"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    data = svc.issue_search(query, limit=limit)
    _emit(data, _ctx_format(ctx))


# --- Issue write ---


@issue_app.command("create")
def issue_create_cmd(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title"),
    body_file: Path | None = typer.Option(None, "--body-file"),
    body: str | None = typer.Option(None, "--body"),
    label: list[str] = typer.Option(None, "--label"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate(
        "gh-issue-create",
        svc,
        yes=yes,
        question=f"Create issue {title!r}?",
        extra_lines=[f"title: {title}", f"labels: {label or []}"],
    )
    data = svc.issue_create(title=title, body_file=body_file, body=body, labels=label)
    _emit(data, _ctx_format(ctx))


@issue_app.command("edit")
def issue_edit_cmd(
    ctx: typer.Context,
    number: int,
    title: str | None = typer.Option(None, "--title"),
    body_file: Path | None = typer.Option(None, "--body-file"),
    add_label: list[str] = typer.Option(None, "--add-label"),
    remove_label: list[str] = typer.Option(None, "--remove-label"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate(
        "gh-issue-edit",
        svc,
        yes=yes,
        question=f"Edit issue #{number}?",
        extra_lines=[f"number: {number}", f"title: {title}"],
    )
    svc.issue_edit(
        number,
        title=title,
        body_file=body_file,
        add_labels=add_label,
        remove_labels=remove_label,
    )
    _emit({"number": number, "action": "edit"}, _ctx_format(ctx))


@issue_app.command("close")
def issue_close_cmd(
    ctx: typer.Context,
    number: int,
    comment: str | None = typer.Option(None, "--comment"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-issue-close", svc, yes=yes, question=f"Close issue #{number}?")
    svc.issue_close(number, comment=comment)
    _emit({"number": number, "action": "close"}, _ctx_format(ctx))


@issue_app.command("delete")
def issue_delete_cmd(
    ctx: typer.Context,
    number: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-issue-delete", svc, yes=yes, question=f"Delete issue #{number}?")
    svc.issue_delete(number)
    _emit({"number": number, "action": "delete"}, _ctx_format(ctx))


@issue_app.command("comment")
def issue_comment_cmd(
    ctx: typer.Context,
    number: int,
    body: str = typer.Option(..., "--body"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-issue-comment", svc, yes=yes, question=f"Comment on issue #{number}?")
    svc.issue_comment(number, body=body)
    _emit({"number": number, "action": "comment"}, _ctx_format(ctx))


@issue_app.command("batch")
def issue_batch_cmd(
    ctx: typer.Context,
    file: Path = typer.Option(..., "--file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate(
        "gh-issue-batch",
        svc,
        yes=yes,
        question=f"Run issue batch from {file}?",
        extra_lines=[f"batch_file: {file}"],
    )
    data = svc.issue_batch(file)
    _emit(data, _ctx_format(ctx))


# --- Label ---


@label_app.command("list")
def label_list_cmd(ctx: typer.Context) -> None:
    svc = _svc(_ctx_repo(ctx))
    _emit(svc.label_list(), _ctx_format(ctx))


@label_app.command("create")
def label_create_cmd(
    ctx: typer.Context,
    name: str,
    color: str = typer.Option("ededed", "--color"),
    description: str = typer.Option("", "--description"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-label-create", svc, yes=yes, question=f"Create label {name!r}?")
    svc.label_create(name, color=color, description=description)
    _emit({"name": name, "action": "create"}, _ctx_format(ctx))


@label_app.command("delete")
def label_delete_cmd(
    ctx: typer.Context,
    name: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-label-delete", svc, yes=yes, question=f"Delete label {name!r}?")
    svc.label_delete(name)
    _emit({"name": name, "action": "delete"}, _ctx_format(ctx))


@label_app.command("sync")
def label_sync_cmd(
    ctx: typer.Context,
    manifest: Path = typer.Option(..., "--manifest"),
    prune_orphans: bool = typer.Option(False, "--prune-orphans"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate(
        "gh-label-sync",
        svc,
        yes=yes,
        question=f"Sync labels from {manifest}?",
        extra_lines=[f"prune_orphans: {prune_orphans}"],
    )
    data = svc.label_sync(manifest, prune_orphans=prune_orphans)
    _emit(data, _ctx_format(ctx))


# --- PR ---


@pr_app.command("list")
def pr_list_cmd(
    ctx: typer.Context,
    state: str = typer.Option("open", "--state"),
    limit: int = typer.Option(30, "--limit"),
    head: str | None = typer.Option(None, "--head"),
    base: str | None = typer.Option(None, "--base"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _emit(svc.pr_list(state=state, limit=limit, head=head, base=base), _ctx_format(ctx))


@pr_app.command("view")
def pr_view_cmd(ctx: typer.Context, number: int) -> None:
    svc = _svc(_ctx_repo(ctx))
    _emit(svc.pr_view(number), _ctx_format(ctx))


@pr_app.command("diff")
def pr_diff_cmd(ctx: typer.Context, number: int) -> None:
    svc = _svc(_ctx_repo(ctx))
    text = svc.pr_diff_stat(number)
    if _ctx_format(ctx) == "json":
        _emit({"number": number, "stat": text}, "json")
    else:
        typer.echo(text)


@pr_app.command("create")
def pr_create_cmd(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title"),
    body_file: Path | None = typer.Option(None, "--body-file"),
    body: str | None = typer.Option(None, "--body"),
    base: str | None = typer.Option(None, "--base"),
    head: str | None = typer.Option(None, "--head"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-pr-create", svc, yes=yes, question=f"Create PR {title!r}?")
    data = svc.pr_create(title=title, body_file=body_file, body=body, base=base, head=head)
    _emit(data, _ctx_format(ctx))


@pr_app.command("edit")
def pr_edit_cmd(
    ctx: typer.Context,
    number: int,
    title: str | None = typer.Option(None, "--title"),
    body_file: Path | None = typer.Option(None, "--body-file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-pr-edit", svc, yes=yes, question=f"Edit PR #{number}?")
    svc.pr_edit(number, title=title, body_file=body_file)
    _emit({"number": number, "action": "edit"}, _ctx_format(ctx))


@pr_app.command("close")
def pr_close_cmd(
    ctx: typer.Context,
    number: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-pr-close", svc, yes=yes, question=f"Close PR #{number}?")
    svc.pr_close(number)
    _emit({"number": number, "action": "close"}, _ctx_format(ctx))


@pr_app.command("merge")
def pr_merge_cmd(
    ctx: typer.Context,
    number: int,
    merge_method: str = typer.Option("merge", "--merge-method"),
    delete_branch: bool = typer.Option(False, "--delete-branch"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate("gh-pr-merge", svc, yes=yes, question=f"Merge PR #{number}?")
    svc.pr_merge(number, merge_method=merge_method, delete_branch=delete_branch)
    _emit({"number": number, "action": "merge"}, _ctx_format(ctx))


# --- Backlog ---


@backlog_app.command("tree")
def backlog_tree_cmd(ctx: typer.Context) -> None:
    svc = _svc(_ctx_repo(ctx))
    _emit(svc.backlog_tree(), _ctx_format(ctx))


@backlog_app.command("next")
def backlog_next_cmd(ctx: typer.Context) -> None:
    svc = _svc(_ctx_repo(ctx))
    data = svc.backlog_next()
    if data is None:
        if _ctx_format(ctx) == "json":
            _emit({"next": None}, "json")
        else:
            typer.echo("No open child issue found.")
        raise typer.Exit(0)
    _emit(data, _ctx_format(ctx))


@backlog_app.command("resequence")
def backlog_resequence_cmd(
    ctx: typer.Context,
    file: Path = typer.Option(..., "--file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _write_gate(
        "gh-backlog-resequence",
        svc,
        yes=yes,
        question=f"Resequence titles from {file}?",
    )
    data = svc.backlog_resequence(file)
    _emit(data, _ctx_format(ctx))


@repo_app.command("view")
def repo_view_cmd(
    ctx: typer.Context,
    fields: str = typer.Option(
        "nameWithOwner,owner,issueTemplates,pullRequestTemplates",
        "--json-fields",
        help="Comma-separated gh repo view --json fields",
    ),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _emit(svc.repo_view(fields=fields), _ctx_format(ctx))
