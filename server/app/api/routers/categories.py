from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_wiki_manager
from app.core.logging import log_info, log_error, log_ok
from app.schemas.categories import CategoryListResponse, CategoryMembersResponse
from app.services.categories import list_categories, list_category_members
from app.wiki.client import WikiClientManager

router = APIRouter(prefix="/v1/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse)
def categories(
    limit: int = Query(50, ge=1, le=500),
    continue_token: str | None = Query(None, alias="continue"),
    wiki: WikiClientManager = Depends(get_wiki_manager),
):
    log_info("CAT", "列出分类", f"limit={limit} continue={continue_token!r}")
    try:
        result = list_categories(wiki, limit=limit, continue_token=continue_token)
        count = len(result.items)
        log_ok("CAT", f"列出分类完成", f"count={count} continue_next={result.continue_token!r}")
        return result
    except Exception as exc:
        log_error("CAT", "列出分类失败", f"error={exc}")
        raise


@router.get("/{name}/members", response_model=CategoryMembersResponse)
def members(
    name: str,
    limit: int = Query(50, ge=1, le=500),
    continue_token: str | None = Query(None, alias="continue"),
    wiki: WikiClientManager = Depends(get_wiki_manager),
):
    log_info("CAT", f"列出分类成员", f"name=\"{name}\" limit={limit} continue={continue_token!r}")
    try:
        result = list_category_members(wiki, category_name=name, limit=limit, continue_token=continue_token)
        count = len(result.items)
        log_ok("CAT", f"列出分类成员完成", f"name=\"{name}\" count={count} continue_next={result.continue_token!r}")
        return result
    except Exception as exc:
        log_error("CAT", f"列出分类成员失败", f"name=\"{name}\" error={exc}")
        raise
