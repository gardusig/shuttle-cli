from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DriveConfig(BaseModel):
    google: bool = False
    proton: bool = False
    icloud: bool = False
    onedrive: bool = False


class NotionConfig(BaseModel):
    database_id: str = ""


class ChromeConfig(BaseModel):
    profile: str = "Default"


class ShuttleConfig(BaseModel):
    repositories: list[str] = Field(default_factory=list)
    drives: DriveConfig = Field(default_factory=DriveConfig)
    notion: NotionConfig = Field(default_factory=NotionConfig)
    chrome: ChromeConfig = Field(default_factory=ChromeConfig)


class ShuttleSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHUTTLE_", extra="ignore")

    config_dir: Path = Path.home() / ".config" / "shuttle-cli"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_config_dir() -> Path:
    env = os.environ.get("SHUTTLE_CONFIG_DIR")
    if env:
        return Path(env).expanduser()
    bundled = project_root() / "config"
    if bundled.exists():
        return bundled
    return Path.home() / ".config" / "shuttle-cli"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_config(config_dir: Path | None = None) -> ShuttleConfig:
    base = config_dir or default_config_dir()
    main_path = base / "config.yaml"
    repos_path = base / "repositories.yaml"
    drives_path = base / "drives.yaml"

    merged: dict = {}
    merged.update(load_yaml(main_path))
    repos_data = load_yaml(repos_path)
    if "repositories" in repos_data:
        merged["repositories"] = repos_data["repositories"]
    drives_data = load_yaml(drives_path)
    if "drives" in drives_data:
        merged["drives"] = drives_data["drives"]

    return ShuttleConfig.model_validate(merged)
