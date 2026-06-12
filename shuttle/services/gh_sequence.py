"""Parse and sort issue title sequence prefixes (N / N.M)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_SEQ_RE = re.compile(
    r"^(?P<major>\d+)\s*(?:[.—\-]\s*(?P<minor>\d+))?\s*[—\-]\s*(?P<rest>.+)$"
)
_SEQ_LOOSE_RE = re.compile(r"^(?P<major>\d+)(?:\.(?P<minor>\d+))?\s")


@dataclass(frozen=True, order=True)
class SequenceKey:
    major: int
    minor: int | None

    @classmethod
    def from_title(cls, title: str) -> SequenceKey | None:
        m = _SEQ_RE.match(title.strip())
        if m:
            minor = int(m.group("minor")) if m.group("minor") else None
            return cls(int(m.group("major")), minor)
        m2 = _SEQ_LOOSE_RE.match(title.strip())
        if m2:
            minor = int(m2.group("minor")) if m2.group("minor") else None
            return cls(int(m2.group("major")), minor)
        return None

    def prefix(self) -> str:
        if self.minor is None:
            return f"{self.major} —"
        return f"{self.major}.{self.minor} —"


def sort_issues_by_sequence(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(issue: dict[str, Any]) -> tuple[int, int, str]:
        title = str(issue.get("title", ""))
        seq = SequenceKey.from_title(title)
        if seq is None:
            return (999_999, 999_999, title.lower())
        minor = seq.minor if seq.minor is not None else -1
        return (seq.major, minor, title.lower())

    return sorted(issues, key=key)


def next_child_issue(issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Lowest open issue-type:child by sequence."""
    children = [
        i
        for i in issues
        if any(str(lb).startswith("issue-type:child") for lb in i.get("labels", []))
    ]
    if not children:
        children = [
            i
            for i in issues
            if SequenceKey.from_title(str(i.get("title", ""))) is not None
            and (SequenceKey.from_title(str(i.get("title", ""))) or SequenceKey(0, 0)).minor
            is not None
        ]
    ordered = sort_issues_by_sequence(children)
    return ordered[0] if ordered else None
