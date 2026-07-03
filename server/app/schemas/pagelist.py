from __future__ import annotations

from pydantic import BaseModel, Field


class PagelistResponse(BaseModel):
    total: int
    titles: list[str]
    cache_valid: bool
    cached_at: str | None = None


class CheckPagenameRequest(BaseModel):
    text: str = Field(..., min_length=1, description="要检查的文本内容")


class CheckPagenameResponse(BaseModel):
    total: int
    matched_titles: list[str]
