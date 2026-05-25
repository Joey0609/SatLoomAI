from __future__ import annotations

from pydantic import BaseModel


class CategoryItem(BaseModel):
    name: str


class CategoryListResponse(BaseModel):
    items: list[CategoryItem]
    continue_token: str | None = None


class CategoryMember(BaseModel):
    title: str
    pageid: int | None = None
    ns: int | None = None


class CategoryMembersResponse(BaseModel):
    items: list[CategoryMember]
    continue_token: str | None = None
