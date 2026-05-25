from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_wiki_manager
from app.core.logging import log_info, log_error, log_ok
from app.wiki.client import WikiClientManager

router = APIRouter(prefix="/v1/site", tags=["site"])


@router.get("/info")
def site_info(wiki: WikiClientManager = Depends(get_wiki_manager)):
    log_info("SITE", "获取站点信息")
    try:
        result = wiki.api(
            "query",
            meta="siteinfo",
            siprop="general|namespaces|namespacealiases|statistics",
        )
        general = result.get("query", {}).get("general", {})
        sitename = general.get("sitename", "?")
        lang = general.get("lang", "?")
        stats = general.get("statistics", {})
        pages_count = stats.get("pages", "?")
        log_ok("SITE", "获取站点信息完成", f"sitename=\"{sitename}\" lang={lang} pages={pages_count}")
        return result
    except Exception as exc:
        log_error("SITE", "获取站点信息失败", f"error={exc}")
        raise
