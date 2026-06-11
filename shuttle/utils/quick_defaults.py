"""Smart defaults — suggest names/messages instead of prompting."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime

DEFAULT_COMMIT_MESSAGE = "."
DEFAULT_STASH_MESSAGE = "."


def default_commit_message() -> str:
    return DEFAULT_COMMIT_MESSAGE


def default_stash_message() -> str:
    return DEFAULT_STASH_MESSAGE


def default_tag_name() -> str:
    return date.today().isoformat()


def suggest_branch_name(existing_branches: Iterable[str] | None = None) -> str:
    """Unique wip branch: wip-YYMMDD-NNN (daily sequence, no prompt)."""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"wip-{today}-"
    taken = {name.strip() for name in (existing_branches or ()) if name.strip()}
    seq = 1
    for name in taken:
        if not name.startswith(prefix):
            continue
        tail = name[len(prefix) :]
        if tail.isdigit():
            seq = max(seq, int(tail) + 1)
    while True:
        candidate = f"{prefix}{seq:03d}"
        if candidate not in taken:
            return candidate
        seq += 1
