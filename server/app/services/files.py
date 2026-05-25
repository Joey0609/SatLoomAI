from __future__ import annotations

from app.schemas.files import (
    FileInfo,
    FileUploadResponse,
    FileUsageItem,
    FileUsageResponse,
)
from app.wiki.client import WikiClientManager


def _extract_first_page(data: dict) -> dict | None:
    pages = data.get("query", {}).get("pages", {})
    if not isinstance(pages, dict):
        return None
    for _, v in pages.items():
        if isinstance(v, dict):
            return v
    return None


def get_file_info(wiki: WikiClientManager, filename: str) -> FileInfo:
    data = wiki.file_info(filename)
    page = _extract_first_page(data) or {}

    imageinfo = (page.get("imageinfo") or [])
    ii0 = imageinfo[0] if isinstance(imageinfo, list) and len(imageinfo) > 0 else {}

    return FileInfo(
        name=str(page.get("title") or filename),
        url=ii0.get("url"),
        descriptionurl=ii0.get("descriptionurl"),
        size=ii0.get("size"),
        width=ii0.get("width"),
        height=ii0.get("height"),
        mime=ii0.get("mime"),
        sha1=ii0.get("sha1"),
        timestamp=ii0.get("timestamp"),
        user=ii0.get("user"),
        comment=ii0.get("comment"),
    )


def get_file_usage(
    wiki: WikiClientManager,
    filename: str,
    limit: int,
    continue_token: str | None,
) -> FileUsageResponse:
    data = wiki.file_usage(filename=filename, limit=limit, continue_token=continue_token)
    page = _extract_first_page(data) or {}

    usage_raw = page.get("imageusage") or []
    items = [
        FileUsageItem(
            title=str(x.get("title", "")),
            pageid=x.get("pageid"),
            ns=x.get("ns"),
        )
        for x in usage_raw
        if isinstance(x, dict)
    ]

    next_token = data.get("continue", {}).get("iucontinue")
    return FileUsageResponse(items=items, continue_token=next_token)


def upload_file(
    wiki: WikiClientManager,
    fileobj,
    filename: str,
    comment: str,
    ignore_warnings: bool,
) -> FileUploadResponse:
    data = wiki.upload_file(
        fileobj=fileobj,
        filename=filename,
        comment=comment,
        ignore_warnings=ignore_warnings,
    )

    # mwclient 返回可能是 {'upload': {...}} 或类似结构
    upload = data.get("upload") if isinstance(data, dict) else None
    if isinstance(upload, dict):
        return FileUploadResponse(
            filename=str(upload.get("filename", filename)),
            result=str(upload.get("result", "unknown")),
            url=upload.get("imageinfo", {}).get("url") if isinstance(upload.get("imageinfo"), dict) else None,
            details=upload,
        )

    return FileUploadResponse(filename=filename, result="unknown", details=data if isinstance(data, dict) else {"raw": str(data)})
