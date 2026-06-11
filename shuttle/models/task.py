"""Notion task models (placeholder per issue #3)."""

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str = ""
    title: str = ""
    status: str = ""
    properties: dict[str, str] = Field(default_factory=dict)
