from __future__ import annotations

from app.schemas.pages import PageContent
from app.wiki.client import WikiClientManager


def get_page_content(wiki: WikiClientManager, title: str) -> PageContent:
    exists, text = wiki.page_text(title)
    return PageContent(title=title, text=text, exists=exists)


def create_page(
    wiki: WikiClientManager,
    title: str,
    text: str,
    summary: str,
    minor: bool,
    bot: bool,
) -> None:
    wiki.page_save(title=title, text=text, summary=summary, minor=minor, bot=bot)


def update_page(
    wiki: WikiClientManager,
    title: str,
    text: str,
    summary: str,
    minor: bool,
    bot: bool,
) -> None:
    wiki.page_save(title=title, text=text, summary=summary, minor=minor, bot=bot)


def delete_page(wiki: WikiClientManager, title: str, reason: str) -> None:
    wiki.page_delete(title=title, reason=reason)
