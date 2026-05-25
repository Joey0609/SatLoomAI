from __future__ import annotations

from pydantic import BaseModel, Field


class PageContent(BaseModel):
    title: str
    text: str
    exists: bool


class PageCreateRequest(BaseModel):
    title: str = Field(..., description="页面标题（不含命名空间前缀也可）")
    text: str
    summary: str = "create via SatLoomAI"
    minor: bool = False
    bot: bool = True


class PageUpdateRequest(BaseModel):
    text: str
    summary: str = "update via SatLoomAI"
    minor: bool = False
    bot: bool = True


class PageDeleteRequest(BaseModel):
    reason: str = "delete via SatLoomAI"
