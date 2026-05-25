from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import ConfigError


@dataclass(frozen=True)
class SiteConfig:
    base_url: str
    host: str
    scheme: str
    path: str


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int
    log_level: str


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


@dataclass(frozen=True)
class AppConfig:
    site: SiteConfig
    server: ServerConfig


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(
            code="config_not_found",
            message=f"缺少配置文件: {path}",
            status_code=500,
        )

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(
            code="config_invalid_json",
            message=f"配置文件 JSON 解析失败: {path}",
            status_code=500,
            details={"error": str(exc)},
        ) from exc


def load_app_config(server_dir: Path) -> AppConfig:
    raw = _read_json(server_dir / "config.json")

    try:
        site_raw = raw["site"]
        server_raw = raw["server"]

        site = SiteConfig(
            base_url=str(site_raw["base_url"]),
            host=str(site_raw["host"]),
            scheme=str(site_raw.get("scheme", "https")),
            path=str(site_raw.get("path", "/")),
        )

        server = ServerConfig(
            host=str(server_raw.get("host", "127.0.0.1")),
            port=int(server_raw.get("port", 6280)),
            log_level=str(server_raw.get("log_level", "info")),
        )

        return AppConfig(site=site, server=server)
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(
            code="config_missing_fields",
            message="config.json 缺少必要字段 (site/server)",
            status_code=500,
            details={"error": str(exc)},
        ) from exc


def load_credentials(server_dir: Path) -> Credentials:
    raw = _read_json(server_dir / "credentials.json")

    try:
        return Credentials(username=str(raw["username"]), password=str(raw["password"]))
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(
            code="credentials_missing_fields",
            message="credentials.json 缺少 username/password",
            status_code=500,
            details={"error": str(exc)},
        ) from exc
