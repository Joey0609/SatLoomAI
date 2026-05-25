from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.logging import log_info
from app.schemas.common import OkResponse

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.post("/shutdown", response_model=OkResponse)
def shutdown(request: Request):
    log_info("ADMIN", "收到关闭请求，正在停止服务器")
    # run.py 会把 uvicorn.Server 放在 app.state.uvicorn_server
    server = getattr(request.app.state, "uvicorn_server", None)
    if server is not None:
        server.should_exit = True
        log_info("ADMIN", "已设置 should_exit，服务器将在当前请求处理完毕后退出")
    return OkResponse()
