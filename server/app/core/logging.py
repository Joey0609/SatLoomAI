from __future__ import annotations

import logging
import sys
from datetime import datetime


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


# ── print 日志辅助 ──────────────────────────────────────────
# 用户要求所有日志用 print 输出，这里提供统一格式化函数。


def log_info(tag: str, message: str, detail: str = "") -> None:
    """输出一条规范的操作日志（print 到 stdout）。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if detail:
        print(f"[{ts}] [{tag:<8}] {message}  | {detail}")
    else:
        print(f"[{ts}] [{tag:<8}] {message}")


def log_error(tag: str, message: str, detail: str = "") -> None:
    """输出一条错误日志（print 到 stderr）。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if detail:
        print(f"[{ts}] [{tag:<8}] [ERR] {message}  | {detail}", file=sys.stderr)
    else:
        print(f"[{ts}] [{tag:<8}] [ERR] {message}", file=sys.stderr)


def log_ok(tag: str, message: str, detail: str = "") -> None:
    """输出一条成功结果日志（print 到 stdout）。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if detail:
        print(f"[{ts}] [{tag:<8}] [OK] {message}  | {detail}")
    else:
        print(f"[{ts}] [{tag:<8}] [OK] {message}")
