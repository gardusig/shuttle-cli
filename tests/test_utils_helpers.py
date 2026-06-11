"""Unit tests for shuttle.utils helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from shuttle.utils import fs, hashing, retry, zip as zip_util
from shuttle.utils.confirm import require_confirmation
from shuttle.utils.config import default_config_dir, load_config, load_yaml, project_root
from shuttle.utils.process import GitCommandError, run_git
from shuttle.utils.yaml import dump_yaml, load_yaml as utils_load_yaml


def test_project_root_points_at_repo() -> None:
    root = project_root()
    assert (root / "pyproject.toml").is_file()


def test_default_config_dir_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHUTTLE_CONFIG_DIR", str(tmp_path))
    assert default_config_dir() == tmp_path


def test_load_yaml_missing_returns_empty(tmp_path: Path) -> None:
    assert load_yaml(tmp_path / "missing.yaml") == {}


def test_load_yaml_invalid_mapping_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("- not-a-map\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_yaml(path)


def test_load_config_merges_files(tmp_path: Path) -> None:
    (tmp_path / "config.yaml").write_text("chrome:\n  profile: Work\n", encoding="utf-8")
    (tmp_path / "repositories.yaml").write_text(
        "repositories:\n  - /path/a\n", encoding="utf-8"
    )
    (tmp_path / "drives.yaml").write_text("drives:\n  google: true\n", encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.chrome.profile == "Work"
    assert cfg.repositories == ["/path/a"]
    assert cfg.drives.google is True


def test_utils_yaml_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "cfg.yaml"
    dump_yaml(path, {"a": 1})
    assert utils_load_yaml(path) == {"a": 1}
    assert utils_load_yaml(tmp_path / "none.yaml") == {}


def test_utils_yaml_invalid_raises(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("[1, 2]\n", encoding="utf-8")
    with pytest.raises(ValueError):
        utils_load_yaml(path)


def test_fs_helpers(tmp_path: Path) -> None:
    dest = tmp_path / "out" / "file.txt"
    src = tmp_path / "src.txt"
    src.write_text("data", encoding="utf-8")
    fs.atomic_replace(src, dest)
    assert dest.read_text(encoding="utf-8") == "data"
    assert fs.ensure_dir(tmp_path / "a" / "b") == tmp_path / "a" / "b"


def test_sha256_file(tmp_path: Path) -> None:
    path = tmp_path / "f.bin"
    path.write_bytes(b"hello")
    digest = hashing.sha256_file(path)
    assert len(digest) == 64


def test_zip_create_and_extract(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.txt").write_text("one", encoding="utf-8")
    archive = tmp_path / "out.zip"
    zip_util.create_zip(source, archive)
    extract = tmp_path / "extracted"
    zip_util.extract_zip(archive, extract)
    assert (extract / "a.txt").read_text(encoding="utf-8") == "one"


def test_retry_succeeds_after_failure() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError("nope")
        return "ok"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(retry.time, "sleep", lambda _: None)
        assert retry.retry(flaky, attempts=3, delay=0) == "ok"


def test_retry_raises_last_error() -> None:
    def always_fail() -> None:
        raise RuntimeError("fail")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(retry.time, "sleep", lambda _: None)
        with pytest.raises(RuntimeError, match="fail"):
            retry.retry(always_fail, attempts=2, delay=0)


def test_run_git_raises_on_failure(tmp_path: Path) -> None:
    with pytest.raises(GitCommandError):
        run_git(["status"], cwd=str(tmp_path), check=True)


def test_git_command_error_message() -> None:
    err = GitCommandError(["git", "x"], 1, "boom")
    assert "boom" in str(err)
    assert err.returncode == 1


def test_require_confirmation_with_yes() -> None:
    require_confirmation("go?", yes=True)
