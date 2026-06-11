"""Repository models (placeholder per issue #3)."""

from pydantic import BaseModel, Field


class Repository(BaseModel):
    path: str
    name: str = ""
    tags: list[str] = Field(default_factory=list)
