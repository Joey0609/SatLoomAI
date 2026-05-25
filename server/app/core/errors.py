from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


class ConfigError(AppError):
    pass


class WikiAuthError(AppError):
    pass


class WikiApiError(AppError):
    pass
