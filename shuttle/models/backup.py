"""Backup snapshot models (placeholder per issue #3)."""

from pydantic import BaseModel, Field


class BackupSnapshot(BaseModel):
    id: str = ""
    created_at: str = ""
    repositories: list[str] = Field(default_factory=list)
    drives: list[str] = Field(default_factory=list)
