from __future__ import annotations

import asyncio
from pathlib import Path

import uvicorn

from app.main import create_app


def _server_dir() -> Path:
    # server/run.py -> server/
    return Path(__file__).resolve().parent


async def serve() -> None:
    app = create_app(_server_dir())

    # 用程序化 Server，便于 /v1/admin/shutdown 设置 should_exit
    config = uvicorn.Config(
        app,
        host=app.state.config.server.host,
        port=app.state.config.server.port,
        log_level=app.state.config.server.log_level,
    )
    server = uvicorn.Server(config)
    app.state.uvicorn_server = server

    await server.serve()


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
