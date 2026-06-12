"""Read-only safety policy: which operations need a write gate."""

from __future__ import annotations

from enum import Enum


class OperationKind(Enum):
    READ = "read"
    WRITE_SAFE = "write_safe"
    WRITE_GATED = "write_gated"


# Read-only or low-risk local writes (no gate).
READ_OPERATIONS = frozenset(
    {
        "status",
        "branch-list",
        "stash-list",
        "large-files",
        "zip",
        "review",
        "docs",
        "pull",
    }
)

WRITE_SAFE_OPERATIONS = frozenset(
    {
        "commit",
        "stash-push",
        "stash-apply",
        "stash-pop",
        "branch-rename",
        "branch-prune",
        "rebase-continue",
        "rebase-abort",
        "revert-continue",
        "revert-abort",
        "cherry-pick-continue",
        "cherry-pick-abort",
    }
)

# Destructive or remote-publishing — require write gate + confirmation.
WRITE_GATED_OPERATIONS = frozenset(
    {
        "push",
        "start",
        "main",
        "reset",
        "branch-delete",
        "branch-delete-all",
        "branch-delete-action",
        "branch-clear",
        "branch-clear-remote",
        "post-merge-cleanup",
        "stash-drop",
        "stash-clear",
        "tag-push",
        "tag-replace",
        "tag-force-push",
        "start-push",
        "rebase",
        "revert",
        "cherry-pick",
        "docker-clean",
        "docker-stop",
        "docker-container-delete",
        "docker-image-delete",
        "docker-reset",
    }
)


def classify_operation(operation: str) -> OperationKind:
    if operation in READ_OPERATIONS:
        return OperationKind.READ
    if operation in WRITE_SAFE_OPERATIONS:
        return OperationKind.WRITE_SAFE
    if operation in WRITE_GATED_OPERATIONS:
        return OperationKind.WRITE_GATED
    return OperationKind.WRITE_GATED
