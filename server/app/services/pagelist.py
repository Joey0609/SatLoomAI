from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from app.core.errors import WikiApiError
from app.core.logging import log_error, log_info, log_ok
from app.utils.ahocorasick import AhoCorasick
from app.wiki.client import WikiClientManager

# ── 常量 ──────────────────────────────────────────────────

CACHE_VALID_SECONDS = 86400  # 1 天
PAGE_LIST_LIMIT = 5000  # 每次 API 请求条数
CACHE_DIR = Path(__file__).resolve().parents[1] / "cache"
CSV_PATH = CACHE_DIR / "pagelist.csv"
META_PATH = CACHE_DIR / "pagelist_meta.json"


# ══════════════════════════════════════════════════════════
#  PageListService
# ══════════════════════════════════════════════════════════


class PageListService:
    """全量词条列表服务。

    - 从 MediaWiki `allpages` API 分页拉取命名空间 0 的所有页面。
    - 缓存到本地 CSV，有效期 1 天。
    - 构建 Aho-Corasick 自动机用于高效词条匹配。
    - 提供词条列表查询和文字中词条名称匹配功能。
    """

    def __init__(self, wiki: WikiClientManager) -> None:
        self._wiki = wiki
        self._page_titles: list[str] = []
        self._automaton: AhoCorasick | None = None
        self._cached_at: datetime | None = None
        self._cache_complete: bool = False

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._init_from_cache()

    # ── 公开接口 ────────────────────────────────────────────

    @property
    def page_titles(self) -> list[str]:
        return list(self._page_titles)

    @property
    def cache_valid(self) -> bool:
        if not self._cached_at or not self._cache_complete:
            return False
        return (datetime.now() - self._cached_at).total_seconds() < CACHE_VALID_SECONDS

    @property
    def cached_at(self) -> str | None:
        return self._cached_at.isoformat() if self._cached_at else None

    def ensure_fresh(self) -> None:
        """检查缓存是否有效，失效则重新拉取。"""
        if not self.cache_valid:
            log_info("CACHE", "缓存失效或不存在，开始重新拉取页面列表")
            self._fetch_and_cache()
        else:
            log_info("CACHE", "缓存有效，跳过拉取")

    def get_pagelist(self) -> list[str]:
        self.ensure_fresh()
        return self.page_titles

    def check_pagename(self, text: str) -> list[str]:
        """返回文本中出现的词条名称（按首次出现位置排序、去重）。"""
        self.ensure_fresh()
        if not self._automaton:
            self._build_automaton()
        return self._automaton.find_matched(text) if self._automaton else []

    # ── 缓存管理 ────────────────────────────────────────────

    def _init_from_cache(self) -> None:
        """启动时尝试加载缓存，如果有效则直接使用。"""
        if META_PATH.exists() and CSV_PATH.exists():
            try:
                meta = json.loads(META_PATH.read_text(encoding="utf-8"))
                last_fetch = datetime.fromisoformat(meta["last_fetch"])
                complete = bool(meta.get("complete", False))

                if complete and (datetime.now() - last_fetch).total_seconds() < CACHE_VALID_SECONDS:
                    self._cached_at = last_fetch
                    self._cache_complete = True
                    self._load_csv()
                    log_ok("CACHE", f"加载本地缓存 ({len(self._page_titles)} 条，{self._cached_at})")
                    # 加载完立刻构建自动机
                    self._build_automaton()
                    return
                else:
                    log_info("CACHE", "缓存过期或不完整，启动时将重新拉取")
            except Exception as exc:
                log_error("CACHE", f"读取缓存元数据失败: {exc}")
        else:
            log_info("CACHE", "无本地缓存，启动时将拉取页面列表")

    def _load_csv(self) -> None:
        """从 CSV 加载页面标题列表。"""
        titles: list[str] = []
        with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            try:
                for row in reader:
                    if row:
                        titles.append(row[0])
            except Exception:
                pass
        self._page_titles = titles

    def _save_cache(self, titles: list[str], complete: bool) -> None:
        """保存页面标题到 CSV，并写入元数据。"""
        # 写 CSV
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for title in titles:
                writer.writerow([title])

        # 写元数据
        meta = {
            "last_fetch": datetime.now().isoformat(),
            "complete": complete,
            "count": len(titles),
        }
        META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        self._page_titles = titles
        self._cached_at = datetime.now()
        self._cache_complete = complete
        # 缓存变更后重建自动机
        self._build_automaton()

    # ── 自动机构建 ──────────────────────────────────────────

    def _build_automaton(self) -> None:
        if not self._page_titles:
            self._automaton = None
            return
        log_info("AUTO", f"构建 Aho-Corasick 自动机 ({len(self._page_titles)} 个模式串)")
        self._automaton = AhoCorasick(self._page_titles)

    # ── API 拉取 ────────────────────────────────────────────

    def _fetch_and_cache(self) -> None:
        """分页拉取所有页面标题并写入缓存。"""
        all_titles: list[str] = []
        apcontinue: str | None = None
        complete = True
        pages_fetched = 0

        log_info("FETCH", "开始拉取全量页面列表")

        while True:
            params: dict = {
                "list": "allpages",
                "aplimit": PAGE_LIST_LIMIT,
                "apnamespace": 0,
            }
            if apcontinue:
                params["apcontinue"] = apcontinue

            try:
                data = self._wiki.api("query", **params)
            except WikiApiError as exc:
                log_error("FETCH", f"API 调用失败", str(exc))
                complete = False
                break
            except Exception as exc:
                log_error("FETCH", f"拉取出错", str(exc))
                complete = False
                break

            # 提取页面标题
            pages = data.get("query", {}).get("allpages", [])
            for p in pages:
                title = p.get("title", "")
                if title:
                    all_titles.append(title)
                    pages_fetched += 1

            log_info("FETCH", f"已拉取 {pages_fetched} 条...")

            # 检查是否还有下一页
            cont = data.get("continue", {})
            apcontinue = cont.get("apcontinue") if cont else None
            if not apcontinue:
                break

        # 写缓存
        self._save_cache(all_titles, complete)

        if complete:
            log_ok("CACHE", f"全量拉取完成，共 {len(all_titles)} 条")
        else:
            log_error("CACHE", f"拉取未完成，已缓存 {len(all_titles)} 条（有效期=0）")
