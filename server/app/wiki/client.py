from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

import cloudscraper
from mwclient import Site, client as mwclient_client
from requests.exceptions import HTTPError

from app.core.config import Credentials, SiteConfig
from app.core.errors import WikiApiError, WikiAuthError
from app.core.logging import log_info, log_error, log_ok

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WikiRequestContext:
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    accept: str = (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    )
    accept_language: str = "zh-CN,zh;q=0.9,en;q=0.8"


class WikiClientManager:
    """线程安全的 mwclient Site 管理器。

    - 懒加载连接
    - 自动登录（失败抛 WikiAuthError）
    - 统一封装 token 与 API 调用异常
    """

    def __init__(self, site_cfg: SiteConfig, creds: Credentials, ctx: WikiRequestContext):
        self._site_cfg = site_cfg
        self._creds = creds
        self._ctx = ctx
        self._lock = threading.RLock()
        self._site: Site | None = None
        self._is_logged_in: bool = False

    def _build_site(self) -> Site:
        log_info("WIKI", "建立站点连接", f"host={self._site_cfg.host} scheme={self._site_cfg.scheme}")
        scraper = cloudscraper.create_scraper()
        # 组装 User-Agent（保持与 mwclient 默认拼接方式一致）
        ua = self._ctx.user_agent + " " + mwclient_client.USER_AGENT
        scraper.headers["User-Agent"] = ua
        scraper.headers["Accept"] = self._ctx.accept
        scraper.headers["Accept-Language"] = self._ctx.accept_language

        # 通过 pool 参数传入 cloudscraper session，
        # 使得 Site.__init__ 内部 site_init() 的首次 API 调用就使用 cloudscraper，
        # 从而自动处理 Cloudflare JS Challenge。
        site = Site(
            self._site_cfg.host,
            scheme=self._site_cfg.scheme,
            path=self._site_cfg.path,
            pool=scraper,
        )
        log_ok("WIKI", "站点连接建立成功")
        return site

    def _ensure_site(self) -> Site:
        with self._lock:
            if self._site is None:
                try:
                    log_info("WIKI", "初始化 Wiki 连接 ...")
                    self._site = self._build_site()
                    log_ok("WIKI", "Wiki 连接初始化完成")
                except HTTPError as exc:
                    # 常见：Cloudflare/WAF 直接拦截 api.php，返回 403 + "Just a moment..."
                    resp = getattr(exc, "response", None)
                    status = getattr(resp, "status_code", None)
                    snippet = None
                    try:
                        if resp is not None and resp.text:
                            snippet = resp.text[:300]
                    except Exception:  # noqa: BLE001
                        snippet = None

                    log_error("WIKI", "Wiki 连接被拦截（可能是 Cloudflare/WAF）", f"status={status}")
                    raise WikiApiError(
                        code="wiki_http_error",
                        message=(
                            "访问 Wiki API 被拦截（可能是 Cloudflare/WAF 需要浏览器校验）。"
                            "请在站点侧放行本机 IP 或放行 /api.php 才能使用。"
                        ),
                        status_code=int(status) if status else 502,
                        details={"status": status, "body_snippet": snippet},
                    ) from exc
                except Exception as exc:  # noqa: BLE001
                    log_error("WIKI", "初始化 Wiki 连接失败", f"error={exc}")
                    raise WikiApiError(
                        code="wiki_site_init_failed",
                        message="初始化 Wiki 站点连接失败",
                        status_code=502,
                        details={"error": str(exc)},
                    ) from exc
            return self._site

    def ensure_login(self) -> Site:
        with self._lock:
            site = self._ensure_site()
            if self._is_logged_in:
                return site

            log_info("WIKI", "登录 Wiki", f"user={self._creds.username}")
            try:
                site.login(self._creds.username, self._creds.password)
                self._is_logged_in = True
                log_ok("WIKI", "Wiki 登录成功", f"user={self._creds.username}")
                return site
            except Exception as exc:  # noqa: BLE001
                # 登录失败时清空登录态，便于下次重试
                self._is_logged_in = False
                log_error("WIKI", "Wiki 登录失败", f"user={self._creds.username} error={exc}")
                raise WikiAuthError(
                    code="wiki_login_failed",
                    message="Wiki 登录失败（请检查 credentials.json 与账号权限）",
                    status_code=401,
                    details={"error": str(exc)},
                ) from exc

    def api(self, action: str, **params):
        site = self.ensure_login()
        log_info("WIKI", f"调用 Wiki API", f"action={action} params={params}")
        try:
            result = site.api(action, **params)
            log_ok("WIKI", f"Wiki API 调用成功", f"action={action}")
            return result
        except Exception as exc:  # noqa: BLE001
            log_error("WIKI", f"Wiki API 调用失败", f"action={action} error={exc}")
            raise WikiApiError(
                code="wiki_api_error",
                message=f"Wiki API 调用失败: action={action}",
                status_code=502,
                details={"error": str(exc)},
            ) from exc

    def get_csrf_token(self) -> str:
        log_info("WIKI", "获取 CSRF token")
        data = self.api("query", meta="tokens")
        try:
            token = str(data["query"]["tokens"]["csrftoken"])
            log_ok("WIKI", "CSRF token 获取成功")
            return token
        except Exception as exc:  # noqa: BLE001
            log_error("WIKI", "获取 CSRF token 失败")
            raise WikiApiError(
                code="wiki_token_error",
                message="获取 CSRF token 失败",
                status_code=502,
                details={"raw": data},
            ) from exc

    # ── Page ─────────────────────────────────────────────────

    def page_text(self, title: str) -> tuple[bool, str]:
        site = self.ensure_login()
        page = site.pages[title]
        try:
            exists = bool(page.exists)
            text = page.text() if exists else ""
            exists_label = "存在" if exists else "不存在"
            log_ok("WIKI", f"读取页面内容", f"title=\"{title}\" {exists_label} text_len={len(text)}")
            return exists, text
        except Exception as exc:  # noqa: BLE001
            log_error("WIKI", f"读取页面内容失败", f"title=\"{title}\" error={exc}")
            raise WikiApiError(
                code="wiki_page_read_failed",
                message="读取页面失败",
                status_code=502,
                details={"title": title, "error": str(exc)},
            ) from exc

    def page_save(self, title: str, text: str, summary: str, minor: bool, bot: bool) -> None:
        site = self.ensure_login()
        page = site.pages[title]
        try:
            log_info("WIKI", f"保存页面", f"title=\"{title}\" summary=\"{summary}\" minor={minor} bot={bot} text_len={len(text)}")
            page.save(text, summary=summary, minor=minor, bot=bot)
            log_ok("WIKI", f"保存页面成功", f"title=\"{title}\"")
        except Exception as exc:  # noqa: BLE001
            log_error("WIKI", f"保存页面失败", f"title=\"{title}\" error={exc}")
            raise WikiApiError(
                code="wiki_page_save_failed",
                message="保存页面失败",
                status_code=502,
                details={"title": title, "error": str(exc)},
            ) from exc

    def page_delete(self, title: str, reason: str) -> None:
        log_info("WIKI", f"删除页面", f"title=\"{title}\" reason=\"{reason}\"")
        token = self.get_csrf_token()
        try:
            self.api("delete", title=title, reason=reason, token=token)
            log_ok("WIKI", f"删除页面成功", f"title=\"{title}\"")
        except Exception as exc:
            log_error("WIKI", f"删除页面失败", f"title=\"{title}\" error={exc}")
            raise

    # ── Categories ────────────────────────────────────────────

    def list_categories(self, limit: int, continue_token: str | None) -> dict:
        params: dict = {"list": "allcategories", "aclimit": limit}
        if continue_token:
            params["accontinue"] = continue_token
        log_info("WIKI", "列出分类", f"limit={limit} continue={continue_token!r}")
        return self.api("query", **params)

    def category_members(self, category_name: str, limit: int, continue_token: str | None) -> dict:
        # MediaWiki 需要 Category: 前缀
        cat_title = category_name
        if not cat_title.lower().startswith("category:") and not cat_title.startswith("分类:"):
            cat_title = f"Category:{category_name}"

        params: dict = {
            "list": "categorymembers",
            "cmtitle": cat_title,
            "cmlimit": limit,
        }
        if continue_token:
            params["cmcontinue"] = continue_token
        log_info("WIKI", "获取分类成员", f"category=\"{cat_title}\" limit={limit} continue={continue_token!r}")
        return self.api("query", **params)

    # ── Files ─────────────────────────────────────────────────

    def file_info(self, filename: str) -> dict:
        title = filename
        if not title.lower().startswith("file:") and not title.startswith("文件:"):
            title = f"File:{filename}"

        log_info("WIKI", "查询文件信息", f"filename=\"{filename}\" title=\"{title}\"")
        return self.api(
            "query",
            titles=title,
            prop="imageinfo",
            iiprop="url|size|mime|sha1|timestamp|user|comment|extmetadata",
        )

    def file_usage(self, filename: str, limit: int, continue_token: str | None) -> dict:
        title = filename
        if not title.lower().startswith("file:") and not title.startswith("文件:"):
            title = f"File:{filename}"

        params: dict = {
            "titles": title,
            "prop": "imageusage",
            "iulimit": limit,
        }
        if continue_token:
            params["iucontinue"] = continue_token

        log_info("WIKI", "查询文件使用情况", f"filename=\"{filename}\" title=\"{title}\" limit={limit} continue={continue_token!r}")
        return self.api("query", **params)

    def upload_file(self, fileobj, filename: str, comment: str, ignore_warnings: bool) -> dict:
        site = self.ensure_login()
        log_info("WIKI", f"上传文件", f"filename=\"{filename}\" comment=\"{comment}\" ignore_warnings={ignore_warnings}")
        try:
            result = site.upload(
                file=fileobj,
                filename=filename,
                description=comment,
                ignore=ignore_warnings,
            )
            # mwclient 的返回可能不是 dict，这里统一转
            if isinstance(result, dict):
                log_ok("WIKI", f"上传文件成功", f"filename=\"{filename}\" result={result.get('upload', {}).get('result', '?')}")
                return result
            log_ok("WIKI", f"上传文件成功", f"filename=\"{filename}\" result={result}")
            return {"result": str(result)}
        except Exception as exc:  # noqa: BLE001
            log_error("WIKI", f"上传文件失败", f"filename=\"{filename}\" error={exc}")
            raise WikiApiError(
                code="wiki_upload_failed",
                message="上传文件失败",
                status_code=502,
                details={"filename": filename, "error": str(exc)},
            ) from exc
