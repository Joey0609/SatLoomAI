from __future__ import annotations

from pydantic import BaseModel


class FileInfo(BaseModel):
    name: str
    url: str | None = None
    descriptionurl: str | None = None
    size: int | None = None
    width: int | None = None
    height: int | None = None
    mime: str | None = None
    sha1: str | None = None
    timestamp: str | None = None
    user: str | None = None
    comment: str | None = None


class FileUsageItem(BaseModel):
    title: str
    pageid: int | None = None
    ns: int | None = None


class FileUsageResponse(BaseModel):
    items: list[FileUsageItem]
    continue_token: str | None = None


class FileUploadResponse(BaseModel):
    filename: str
    result: str
    url: str | None = None
    details: dict | None = None
