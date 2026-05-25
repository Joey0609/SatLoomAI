from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_wiki_manager
from app.core.logging import log_info, log_error, log_ok
from app.schemas.common import OkResponse
from app.schemas.pages import (
    PageContent,
    PageCreateRequest,
    PageDeleteRequest,
    PageUpdateRequest,
)
from app.services.pages import create_page, delete_page, get_page_content, update_page
from app.wiki.client import WikiClientManager

router = APIRouter(prefix="/v1/pages", tags=["pages"])


@router.get("/{title}", response_model=PageContent)
def read_page(title: str, wiki: WikiClientManager = Depends(get_wiki_manager)):
    log_info("PAGE", f"读取页面", f"title=\"{title}\"")
    try:
        result = get_page_content(wiki, title)
        exists_info = "存在" if result.exists else "不存在"
        text_len = len(result.text) if result.text else 0
        log_ok("PAGE", f"读取页面完成", f"title=\"{title}\" {exists_info} text_len={text_len}")
        return result
    except Exception as exc:
        log_error("PAGE", f"读取页面失败", f"title=\"{title}\" error={exc}")
        raise


@router.post("", response_model=OkResponse)
def create(req: PageCreateRequest, wiki: WikiClientManager = Depends(get_wiki_manager)):
    log_info("PAGE", f"创建页面", f"title=\"{req.title}\" summary=\"{req.summary}\" minor={req.minor} bot={req.bot}")
    try:
        create_page(
            wiki,
            title=req.title,
            text=req.text,
            summary=req.summary,
            minor=req.minor,
            bot=req.bot,
        )
        log_ok("PAGE", f"创建页面成功", f"title=\"{req.title}\"")
        return OkResponse()
    except Exception as exc:
        log_error("PAGE", f"创建页面失败", f"title=\"{req.title}\" error={exc}")
        raise


@router.put("/{title}", response_model=OkResponse)
def update(title: str, req: PageUpdateRequest, wiki: WikiClientManager = Depends(get_wiki_manager)):
    log_info("PAGE", f"修改页面", f"title=\"{title}\" summary=\"{req.summary}\" minor={req.minor} bot={req.bot}")
    try:
        update_page(
            wiki,
            title=title,
            text=req.text,
            summary=req.summary,
            minor=req.minor,
            bot=req.bot,
        )
        log_ok("PAGE", f"修改页面成功", f"title=\"{title}\"")
        return OkResponse()
    except Exception as exc:
        log_error("PAGE", f"修改页面失败", f"title=\"{title}\" error={exc}")
        raise


@router.delete("/{title}", response_model=OkResponse)
def delete(title: str, req: PageDeleteRequest, wiki: WikiClientManager = Depends(get_wiki_manager)):
    log_info("PAGE", f"删除页面", f"title=\"{title}\" reason=\"{req.reason}\"")
    try:
        delete_page(wiki, title=title, reason=req.reason)
        log_ok("PAGE", f"删除页面成功", f"title=\"{title}\"")
        return OkResponse()
    except Exception as exc:
        log_error("PAGE", f"删除页面失败", f"title=\"{title}\" error={exc}")
        raise
