"""Bookmark models (placeholder per issue #3)."""

from pydantic import BaseModel, Field


class BookmarkEntry(BaseModel):
    title: str = ""
    url: str = ""
    folder: str = ""


class BookmarkExport(BaseModel):
    profile: str = "Default"
    entries: list[BookmarkEntry] = Field(default_factory=list)
