"""Retry helpers (placeholder per issue #3)."""

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    last: Exception | None = None
    for _ in range(attempts):
        try:
            return fn()
        except exceptions as exc:
            last = exc
            time.sleep(delay)
    raise last  # type: ignore[misc]
