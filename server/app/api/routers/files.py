from __future__ import annotations

import mimetypes

import requests
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import get_wiki_manager
from app.core.errors import WikiApiError
from app.core.logging import log_info, log_error, log_ok
from app.schemas.files import FileInfo, FileUploadResponse, FileUsageResponse
from app.services.files import get_file_info, get_file_usage, upload_file
from app.wiki.client import WikiClientManager

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.get("/{filename}/info", response_model=FileInfo)
def info(filename: str, wiki: WikiClientManager = Depends(get_wiki_manager)):
    log_info("FILE", f"获取文件信息", f"filename=\"{filename}\"")
    try:
        result = get_file_info(wiki, filename)
        log_ok("FILE", f"获取文件信息完成", f"filename=\"{filename}\" size={result.size} mime={result.mime}")
        return result
    except Exception as exc:
        log_error("FILE", f"获取文件信息失败", f"filename=\"{filename}\" error={exc}")
        raise


@router.get("/{filename}/usage", response_model=FileUsageResponse)
def usage(
    filename: str,
    limit: int = Query(50, ge=1, le=500),
    continue_token: str | None = Query(None, alias="continue"),
    wiki: WikiClientManager = Depends(get_wiki_manager),
):
    log_info("FILE", f"获取文件使用情况", f"filename=\"{filename}\" limit={limit} continue={continue_token!r}")
    try:
        result = get_file_usage(wiki, filename=filename, limit=limit, continue_token=continue_token)
        count = len(result.items)
        log_ok("FILE", f"获取文件使用情况完成", f"filename=\"{filename}\" count={count} continue_next={result.continue_token!r}")
        return result
    except Exception as exc:
        log_error("FILE", f"获取文件使用情况失败", f"filename=\"{filename}\" error={exc}")
        raise


@router.get("/{filename}/download")
def download(filename: str, wiki: WikiClientManager = Depends(get_wiki_manager)):
    log_info("FILE", f"下载文件", f"filename=\"{filename}\"")
    try:
        fileinfo = get_file_info(wiki, filename)
        if not fileinfo.url:
            raise WikiApiError(
                code="file_no_url",
                message="目标文件无可下载 URL（可能不存在、被删除或权限不足）",
                status_code=404,
                details={"filename": filename, "title": fileinfo.name},
            )

        r = requests.get(fileinfo.url, stream=True, timeout=60)
        r.raise_for_status()

        guessed_type, _ = mimetypes.guess_type(fileinfo.name)
        content_type = fileinfo.mime or guessed_type or "application/octet-stream"

        def iter_bytes():
            yield from r.iter_content(chunk_size=1024 * 256)

        log_ok("FILE", f"下载文件开始", f"filename=\"{filename}\" url={fileinfo.url} type={content_type}")
        return StreamingResponse(iter_bytes(), media_type=content_type)
    except Exception as exc:
        log_error("FILE", f"下载文件失败", f"filename=\"{filename}\" error={exc}")
        raise


@router.post("/upload", response_model=FileUploadResponse)
def upload(
    file: UploadFile = File(...),
    filename: str | None = Query(None, description="目标文件名（不传则用上传文件名）"),
    comment: str = Query("upload via SatLoomAI", description="上传说明"),
    ignore_warnings: bool = Query(False, description="是否忽略警告（覆盖/同名等）"),
    wiki: WikiClientManager = Depends(get_wiki_manager),
):
    target = filename or file.filename
    if not target:
        raise RuntimeError("缺少 filename")

    log_info("FILE", f"上传文件", f"filename=\"{target}\" comment=\"{comment}\" ignore_warnings={ignore_warnings}")
    try:
        result = upload_file(
            wiki,
            fileobj=file.file,
            filename=target,
            comment=comment,
            ignore_warnings=ignore_warnings,
        )
        log_ok("FILE", f"上传文件完成", f"filename=\"{target}\" result=\"{result.result}\" url={result.url}")
        return result
    except Exception as exc:
        log_error("FILE", f"上传文件失败", f"filename=\"{target}\" error={exc}")
        raise
