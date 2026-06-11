"""iCloud Drive provider adapter (placeholder per issue #3)."""


def upload(_local_path: str, _remote_path: str) -> None:
    raise NotImplementedError("iCloud Drive upload not implemented yet")


def download(_remote_path: str, _local_path: str) -> None:
    raise NotImplementedError("iCloud Drive download not implemented yet")


def list_files(_prefix: str = "") -> list[str]:
    raise NotImplementedError("iCloud Drive list not implemented yet")


def delete(_remote_path: str) -> None:
    raise NotImplementedError("iCloud Drive delete not implemented yet")
