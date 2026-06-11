"""Read-only git worktree inventory."""

from __future__ import annotations

from dataclasses import dataclass

from shuttle.services.git_shortcuts import GitShortcuts


@dataclass(frozen=True)
class GitWorktreeSnapshot:
    repo_root: str
    branch: str
    dirty: bool
    status_short: str
    has_upstream: bool
    canonical_main: str
    has_origin: bool

    def summary_lines(self) -> list[str]:
        lines = [
            f"repo: {self.repo_root}",
            f"branch: {self.branch}",
            f"dirty: {self.dirty}",
            f"upstream: {'yes' if self.has_upstream else 'no'}",
            f"canonical_main: {self.canonical_main}",
        ]
        if self.status_short.strip():
            lines.append("status:")
            for line in self.status_short.strip().splitlines()[:12]:
                lines.append(f"  {line}")
            remaining = len(self.status_short.strip().splitlines()) - 12
            if remaining > 0:
                lines.append(f"  ... ({remaining} more lines)")
        return lines


def git_worktree_snapshot(svc: GitShortcuts) -> GitWorktreeSnapshot:
    return GitWorktreeSnapshot(
        repo_root=svc.top,
        branch=svc.current_branch(),
        dirty=svc.is_dirty(),
        status_short=svc.status_short(),
        has_upstream=svc.has_upstream(),
        canonical_main=svc.canonical_main_ref(),
        has_origin=svc.remote_exists("origin"),
    )
