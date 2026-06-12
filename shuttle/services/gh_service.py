"""GitHub issue/label/PR services via gh provider."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from shuttle.providers.gh import GhProvider
from shuttle.services.gh_sequence import SequenceKey, next_child_issue, sort_issues_by_sequence


class GhService:
    def __init__(self, *, repo: str | None = None) -> None:
        self.provider = GhProvider(repo=repo)

    def repo_display(self) -> str:
        return self.provider.repo or self.provider.default_repo()

    # --- Issue read ---

    def issue_list(
        self,
        *,
        state: str = "open",
        label: list[str] | None = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        args = [
            "issue",
            "list",
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,labels,url",
        ]
        for lb in label or []:
            args.extend(["--label", lb])
        return self.provider.run_json(args)

    def issue_view(self, number: int, *, comments: bool = False) -> dict[str, Any]:
        fields = "number,title,body,state,labels,url,author,createdAt,updatedAt"
        args = ["issue", "view", str(number), "--json", fields]
        if comments:
            args.append("--comments")
        return self.provider.run_json(args)

    def issue_search(self, query: str, *, limit: int = 30) -> list[dict[str, Any]]:
        args = [
            "search",
            "issues",
            query,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,labels,url",
        ]
        return self.provider.run_json(args)

    # --- Issue write ---

    def issue_create(
        self,
        *,
        title: str,
        body_file: Path | None = None,
        body: str | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        args = ["issue", "create", "--title", title]
        if body_file:
            args.extend(["--body-file", str(body_file)])
        elif body:
            args.extend(["--body", body])
        if labels:
            args.extend(["--label", ",".join(labels)])
        url = self.provider.run(args)
        number = int(url.rstrip("/").split("/")[-1])
        return {"url": url, "number": number, "title": title}

    def issue_edit(
        self,
        number: int,
        *,
        title: str | None = None,
        body_file: Path | None = None,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> None:
        args = ["issue", "edit", str(number)]
        if title:
            args.extend(["--title", title])
        if body_file:
            args.extend(["--body-file", str(body_file)])
        for lb in add_labels or []:
            args.extend(["--add-label", lb])
        for lb in remove_labels or []:
            args.extend(["--remove-label", lb])
        self.provider.run(args)

    def issue_close(self, number: int, *, comment: str | None = None) -> None:
        args = ["issue", "close", str(number)]
        if comment:
            args.extend(["--comment", comment])
        self.provider.run(args)

    def issue_delete(self, number: int) -> None:
        self.provider.run(["issue", "delete", str(number), "--yes"])

    def issue_comment(self, number: int, *, body: str) -> None:
        self.provider.run(["issue", "comment", str(number), "--body", body])

    def issue_batch(self, batch_file: Path) -> list[dict[str, Any]]:
        data = yaml.safe_load(batch_file.read_text(encoding="utf-8"))
        ops = data.get("operations") or data.get("issues") or []
        results: list[dict[str, Any]] = []
        for op in ops:
            kind = op.get("action") or op.get("kind") or "create"
            if kind == "create":
                results.append(
                    self.issue_create(
                        title=op["title"],
                        body_file=Path(op["body_file"]) if op.get("body_file") else None,
                        body=op.get("body"),
                        labels=op.get("labels"),
                    )
                )
            elif kind == "edit":
                self.issue_edit(
                    int(op["number"]),
                    title=op.get("title"),
                    body_file=Path(op["body_file"]) if op.get("body_file") else None,
                    add_labels=op.get("add_labels"),
                    remove_labels=op.get("remove_labels"),
                )
                results.append({"number": op["number"], "action": "edit"})
            elif kind == "close":
                self.issue_close(int(op["number"]), comment=op.get("comment"))
                results.append({"number": op["number"], "action": "close"})
            else:
                raise ValueError(f"Unknown batch action: {kind}")
        return results

    # --- Labels ---

    def label_list(self) -> list[dict[str, Any]]:
        return self.provider.run_json(["label", "list", "--json", "name,color,description"])

    def label_create(self, name: str, *, color: str = "ededed", description: str = "") -> None:
        args = ["label", "create", name, "--color", color]
        if description:
            args.extend(["--description", description])
        self.provider.run(args)

    def label_delete(self, name: str) -> None:
        self.provider.run(["label", "delete", name, "--yes"])

    def label_sync(
        self,
        manifest_path: Path,
        *,
        prune_orphans: bool = False,
    ) -> dict[str, Any]:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        desired = {entry["name"]: entry for entry in manifest.get("labels", [])}
        existing = {lb["name"]: lb for lb in self.label_list()}
        created: list[str] = []
        for name, spec in desired.items():
            if name not in existing:
                self.label_create(
                    name,
                    color=spec.get("color", "ededed"),
                    description=spec.get("description", ""),
                )
                created.append(name)
        deleted: list[str] = []
        if prune_orphans:
            protected = set(manifest.get("protected", []))
            for name in existing:
                if name not in desired and name not in protected:
                    self.label_delete(name)
                    deleted.append(name)
        return {"created": created, "deleted": deleted, "manifest": str(manifest_path)}

    # --- PR ---

    def pr_list(
        self,
        *,
        state: str = "open",
        limit: int = 30,
        head: str | None = None,
        base: str | None = None,
    ) -> list[dict[str, Any]]:
        args = [
            "pr",
            "list",
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,url,headRefName,baseRefName,mergedAt",
        ]
        if head:
            args.extend(["--head", head])
        if base:
            args.extend(["--base", base])
        return self.provider.run_json(args)

    def repo_view(
        self,
        *,
        fields: str = "nameWithOwner,owner,issueTemplates,pullRequestTemplates",
    ) -> dict[str, Any]:
        return self.provider.run_json(["repo", "view", "--json", fields])

    def pr_view(self, number: int) -> dict[str, Any]:
        return self.provider.run_json(
            [
                "pr",
                "view",
                str(number),
                "--json",
                "number,title,body,state,url,headRefName,baseRefName,commits,files",
            ]
        )

    def pr_diff_stat(self, number: int) -> str:
        return self.provider.run(["pr", "diff", str(number), "--stat"])

    def pr_create(
        self,
        *,
        title: str,
        body_file: Path | None = None,
        body: str | None = None,
        base: str | None = None,
        head: str | None = None,
    ) -> dict[str, Any]:
        args = ["pr", "create", "--title", title]
        if body_file:
            args.extend(["--body-file", str(body_file)])
        elif body:
            args.extend(["--body", body])
        if base:
            args.extend(["--base", base])
        if head:
            args.extend(["--head", head])
        url = self.provider.run(args)
        number = int(url.rstrip("/").split("/")[-1])
        return {"url": url, "number": number, "title": title}

    def pr_edit(
        self,
        number: int,
        *,
        title: str | None = None,
        body_file: Path | None = None,
    ) -> None:
        args = ["pr", "edit", str(number)]
        if title:
            args.extend(["--title", title])
        if body_file:
            args.extend(["--body-file", str(body_file)])
        self.provider.run(args)

    def pr_close(self, number: int) -> None:
        self.provider.run(["pr", "close", str(number)])

    def pr_merge(
        self,
        number: int,
        *,
        merge_method: str = "merge",
        delete_branch: bool = False,
    ) -> None:
        args = ["pr", "merge", str(number), "--merge-method", merge_method]
        if delete_branch:
            args.append("--delete-branch")
        self.provider.run(args)

    # --- Backlog ---

    def backlog_tree(self) -> dict[str, Any]:
        issues = self.issue_list(state="open", limit=200)
        ordered = sort_issues_by_sequence(issues)
        epics: dict[str, list[dict[str, Any]]] = {}
        roots: list[dict[str, Any]] = []
        for issue in ordered:
            labels = [str(lb.get("name", lb)) if isinstance(lb, dict) else str(lb) for lb in issue.get("labels", [])]
            epic_labels = [lb for lb in labels if lb.startswith("epic:")]
            seq = SequenceKey.from_title(str(issue.get("title", "")))
            node = {
                "number": issue["number"],
                "title": issue["title"],
                "labels": labels,
                "sequence": seq.prefix() if seq else None,
            }
            if "issue-type:epic" in labels or (seq and seq.minor is None):
                roots.append(node)
            elif epic_labels:
                slug = epic_labels[0]
                epics.setdefault(slug, []).append(node)
            elif seq and seq.minor is not None:
                epics.setdefault("_unlabeled", []).append(node)
            else:
                roots.append(node)
        return {"repo": self.repo_display(), "roots": roots, "epics": epics, "issues": ordered}

    def backlog_next(self) -> dict[str, Any] | None:
        issues = self.issue_list(state="open", limit=200)
        for issue in issues:
            labels = issue.get("labels", [])
            issue["labels"] = [
                lb.get("name", lb) if isinstance(lb, dict) else lb for lb in labels
            ]
        candidate = next_child_issue(issues)
        if not candidate:
            return None
        seq = SequenceKey.from_title(str(candidate.get("title", "")))
        return {
            "number": candidate["number"],
            "title": candidate["title"],
            "url": candidate.get("url"),
            "sequence": seq.prefix() if seq else None,
        }

    def backlog_resequence(self, plan_file: Path) -> list[dict[str, Any]]:
        plan = yaml.safe_load(plan_file.read_text(encoding="utf-8"))
        results: list[dict[str, Any]] = []
        for entry in plan.get("renames", []):
            number = int(entry["number"])
            new_title = entry["title"]
            self.issue_edit(number, title=new_title)
            results.append({"number": number, "title": new_title})
        return results

    def snapshot_summary(self) -> list[str]:
        return [f"repo: {self.repo_display()}"]
