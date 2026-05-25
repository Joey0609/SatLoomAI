from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import admin, categories, files, pages, site, tools
from app.core.config import load_app_config, load_credentials
from app.core.errors import AppError
from app.core.logging import log_info, setup_logging, log_error
from app.wiki.client import WikiClientManager, WikiRequestContext

logger = logging.getLogger(__name__)


def create_app(server_dir: Path) -> FastAPI:
    cfg = load_app_config(server_dir)
    setup_logging(cfg.server.log_level)
    creds = load_credentials(server_dir)

    app = FastAPI(
        title="SatLoomAI Wiki Local Server",
        version="1.0.0",
        description="本地暴露 sat.huijiwiki.com 的常用 Wiki 操作接口",
    )

    # 存在前端调用可能性，这里放宽到本地开发（需要更严格可自行收敛）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.config = cfg

    # 启动时输出关键信息
    log_info("SRV", f"服务器启动配置：host={cfg.server.host} port={cfg.server.port}")
    log_info("SRV", f"目标站点：{cfg.site.base_url}")
    log_info("SRV", f"Wiki 账号：{creds.username}")
    log_info("SRV", f"日志级别：{cfg.server.log_level}")

    # 预建 Wiki 连接
    mgr = WikiClientManager(cfg.site, creds, WikiRequestContext())
    app.state.wiki = mgr

    # 启动时校验连接
    try:
        mgr.ensure_login()
        log_info("WIKI", "启动时 Wiki 连接校验通过")
    except Exception as exc:
        log_error("WIKI", f"启动时 Wiki 连接校验失败：{exc}")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.exception_handler(AppError)
    def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(Exception)
    def unhandled_error_handler(_: Request, exc: Exception):
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": "服务器内部错误", "details": {"error": str(exc)}},
        )

    app.include_router(pages.router)
    app.include_router(categories.router)
    app.include_router(files.router)
    app.include_router(site.router)
    app.include_router(admin.router)
    app.include_router(tools.router)

    return app
