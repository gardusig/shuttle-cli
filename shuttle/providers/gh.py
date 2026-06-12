"""GitHub CLI (`gh`) subprocess provider."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from shuttle.utils.process import run_gh


class GhProvider:
    """Thin wrapper around `gh` with optional --repo injection."""

    def __init__(self, *, repo: str | None = None) -> None:
        self.repo = repo

    def _base_args(self) -> list[str]:
        if self.repo:
            return ["--repo", self.repo]
        return []

    def run(
        self,
        args: Sequence[str],
        *,
        check: bool = True,
    ) -> str:
        result = run_gh([*self._base_args(), *args], check=check)
        return result.stdout.strip()

    def run_json(self, args: Sequence[str]) -> Any:
        text = self.run(args)
        if not text:
            return []
        return json.loads(text)

    def default_repo(self) -> str:
        data = self.run_json(["repo", "view", "--json", "nameWithOwner"])
        return str(data["nameWithOwner"])
