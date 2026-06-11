"""Hashing helpers (placeholder per issue #3)."""

import hashlib
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
