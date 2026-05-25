from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_wiki_manager
from app.core.logging import log_info, log_error, log_ok
from app.schemas.common import OkResponse
from app.schemas.pages import PageCreateRequest, PageDeleteRequest, PageUpdateRequest
from app.services.categories import list_categories, list_category_members
from app.services.files import get_file_info, get_file_usage
from app.services.pages import create_page, delete_page, get_page_content, update_page
from app.wiki.client import WikiClientManager

router = APIRouter(prefix="/v1/tools", tags=["tools"])


# 轻量 MCP 风格：提供 tool 列表与统一调用入口（不替代 REST 路由，只是聚合层）
TOOLS: dict[str, dict[str, Any]] = {
    "page.get": {"description": "获取词条内容", "args": {"title": "str"}},
    "page.create": {"description": "创建词条", "args_schema": PageCreateRequest.model_json_schema()},
    "page.update": {
        "description": "修改词条",
        "args": {"title": "str"},
        "args_schema": PageUpdateRequest.model_json_schema(),
    },
    "page.delete": {
        "description": "删除词条",
        "args": {"title": "str"},
        "args_schema": PageDeleteRequest.model_json_schema(),
    },
    "category.list": {"description": "列出分类", "args": {"limit": "int", "continue": "str?"}},
    "category.members": {"description": "列出分类成员", "args": {"name": "str", "limit": "int", "continue": "str?"}},
    "file.info": {"description": "获取文件信息", "args": {"filename": "str"}},
    "file.usage": {"description": "获取文件使用情况", "args": {"filename": "str", "limit": "int", "continue": "str?"}},
}


@router.get("", summary="列出所有工具")
def list_tools():
    log_info("TOOL", "列出所有工具")
    items = [{"name": k, **v} for k, v in TOOLS.items()]
    log_ok("TOOL", f"列出工具完成", f"count={len(items)}")
    return {"items": items}


@router.post("/call", summary="统一工具调用")
def call_tool(payload: dict, wiki: WikiClientManager = Depends(get_wiki_manager)):
    name = payload.get("name")
    args = payload.get("args") or {}

    if name not in TOOLS:
        raise RuntimeError(f"未知工具: {name}")

    log_info("TOOL", f"调用工具", f"name=\"{name}\" args={args}")

    try:
        if name == "page.get":
            result = get_page_content(wiki, title=str(args.get("title", ""))).model_dump()
            log_ok("TOOL", f"工具执行成功", f"name=\"{name}\"")
            return result

        if name == "page.create":
            req = PageCreateRequest(**args)
            create_page(wiki, title=req.title, text=req.text, summary=req.summary, minor=req.minor, bot=req.bot)
            log_ok("TOOL", f"工具执行成功", f"name=\"{name}\" title=\"{req.title}\"")
            return OkResponse().model_dump()

        if name == "page.update":
            title = str(args.get("title", ""))
            req = PageUpdateRequest(**{k: v for k, v in args.items() if k != "title"})
            update_page(wiki, title=title, text=req.text, summary=req.summary, minor=req.minor, bot=req.bot)
            log_ok("TOOL", f"工具执行成功", f"name=\"{name}\" title=\"{title}\"")
            return OkResponse().model_dump()

        if name == "page.delete":
            title = str(args.get("title", ""))
            req = PageDeleteRequest(**{k: v for k, v in args.items() if k != "title"})
            delete_page(wiki, title=title, reason=req.reason)
            log_ok("TOOL", f"工具执行成功", f"name=\"{name}\" title=\"{title}\"")
            return OkResponse().model_dump()

        if name == "category.list":
            limit = int(args.get("limit", 50))
            cont = args.get("continue")
            result = list_categories(wiki, limit=limit, continue_token=str(cont) if cont else None).model_dump()
            log_ok("TOOL", f"工具执行成功", f"name=\"{name}\" limit={limit}")
            return result

        if name == "category.members":
            cat = str(args.get("name", ""))
            limit = int(args.get("limit", 50))
            cont = args.get("continue")
            result = list_category_members(wiki, category_name=cat, limit=limit, continue_token=str(cont) if cont else None).model_dump()
            log_ok("TOOL", f"工具执行成功", f"name=\"{name}\" category=\"{cat}\" limit={limit}")
            return result

        if name == "file.info":
            result = get_file_info(wiki, filename=str(args.get("filename", ""))).model_dump()
            log_ok("TOOL", f"工具执行成功", f"name=\"{name}\"")
            return result

        if name == "file.usage":
            filename = str(args.get("filename", ""))
            limit = int(args.get("limit", 50))
            cont = args.get("continue")
            result = get_file_usage(wiki, filename=filename, limit=limit, continue_token=str(cont) if cont else None).model_dump()
            log_ok("TOOL", f"工具执行成功", f"name=\"{name}\" filename=\"{filename}\" limit={limit}")
            return result

        raise RuntimeError(f"未实现工具: {name}")

    except Exception as exc:
        log_error("TOOL", f"工具执行失败", f"name=\"{name}\" error={exc}")
        raise
