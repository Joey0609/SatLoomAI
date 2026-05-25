from __future__ import annotations

from pathlib import Path

from fastapi import Request

from app.core.config import AppConfig, Credentials, load_app_config, load_credentials
from app.wiki.client import WikiClientManager, WikiRequestContext


def get_server_dir() -> Path:
    # server/app/api/deps.py -> server/
    return Path(__file__).resolve().parents[2]


def get_config(request: Request) -> AppConfig:
    cfg: AppConfig | None = getattr(request.app.state, "config", None)
    if cfg is not None:
        return cfg

    server_dir = get_server_dir()
    cfg = load_app_config(server_dir)
    request.app.state.config = cfg
    return cfg


def get_credentials(request: Request) -> Credentials:
    creds: Credentials | None = getattr(request.app.state, "creds", None)
    if creds is not None:
        return creds

    server_dir = get_server_dir()
    creds = load_credentials(server_dir)
    request.app.state.creds = creds
    return creds


def get_wiki_manager(request: Request) -> WikiClientManager:
    mgr: WikiClientManager | None = getattr(request.app.state, "wiki", None)
    if mgr is not None:
        return mgr

    cfg = get_config(request)
    creds = get_credentials(request)

    mgr = WikiClientManager(cfg.site, creds, WikiRequestContext())
    request.app.state.wiki = mgr
    return mgr
