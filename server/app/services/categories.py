from __future__ import annotations

from app.schemas.categories import (
    CategoryItem,
    CategoryListResponse,
    CategoryMember,
    CategoryMembersResponse,
)
from app.wiki.client import WikiClientManager


def list_categories(
    wiki: WikiClientManager,
    limit: int,
    continue_token: str | None,
) -> CategoryListResponse:
    data = wiki.list_categories(limit=limit, continue_token=continue_token)

    items_raw = data.get("query", {}).get("allcategories", [])
    items = [CategoryItem(name=str(x.get("*", ""))) for x in items_raw]

    next_token = data.get("continue", {}).get("accontinue")
    return CategoryListResponse(items=items, continue_token=next_token)


def list_category_members(
    wiki: WikiClientManager,
    category_name: str,
    limit: int,
    continue_token: str | None,
) -> CategoryMembersResponse:
    data = wiki.category_members(
        category_name=category_name,
        limit=limit,
        continue_token=continue_token,
    )

    items_raw = data.get("query", {}).get("categorymembers", [])
    items = [
        CategoryMember(
            title=str(x.get("title", "")),
            pageid=x.get("pageid"),
            ns=x.get("ns"),
        )
        for x in items_raw
    ]

    next_token = data.get("continue", {}).get("cmcontinue")
    return CategoryMembersResponse(items=items, continue_token=next_token)
