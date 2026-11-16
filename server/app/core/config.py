from __future__ import annotations

import json
from dataclasses import dataclass, field
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
    password: str = field(repr=False)


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


def load_accounts(server_dir: Path) -> list[Credentials]:
    raw = _read_json(server_dir / "credentials.json")

    if not isinstance(raw, dict):
        raise ConfigError(
            code="credentials_invalid_format",
            message="credentials.json 必须是单账户对象或包含 accounts 列表的对象",
            status_code=500,
        )

    # 兼容原来的 {"username": "...", "password": "..."} 格式。
    accounts = raw.get("accounts") if "accounts" in raw else [raw]
    if not isinstance(accounts, list) or not accounts:
        raise ConfigError(
            code="credentials_invalid_accounts",
            message="credentials.json 的 accounts 必须是非空列表",
            status_code=500,
        )

    result = []
    for index, account in enumerate(accounts, start=1):
        if (
            not isinstance(account, dict)
            or not isinstance(account.get("username"), str)
            or not account["username"].strip()
            or not isinstance(account.get("password"), str)
            or not account["password"]
        ):
            raise ConfigError(
                code="credentials_missing_fields",
                message=f"credentials.json 第 {index} 个账户缺少有效的 username/password",
                status_code=500,
            )
        result.append(Credentials(username=account["username"], password=account["password"]))
    return result


def load_credentials(server_dir: Path, *, interactive: bool = False) -> Credentials:
    accounts = load_accounts(server_dir)
    if len(accounts) == 1:
        return accounts[0]

    if not interactive:
        raise ConfigError(
            code="credentials_selection_required",
            message="credentials.json 包含多个账户，请在终端启动服务器并选择登录账户",
            status_code=500,
        )

    print("请选择 Wiki 登录账户：")
    for index, account in enumerate(accounts, start=1):
        print(f"  {index}. {account.username}")

    while True:
        try:
            choice = input(f"账户序号 [1-{len(accounts)}]：").strip()
        except (EOFError, OSError) as exc:
            raise ConfigError(
                code="credentials_selection_required",
                message="无法读取账户选择，请在交互式终端启动服务器",
                status_code=500,
            ) from exc
        try:
            index = int(choice)
        except ValueError:
            index = 0
        if 1 <= index <= len(accounts):
            return accounts[index - 1]
        print(f"无效的账户序号，请输入 1 到 {len(accounts)}。")
