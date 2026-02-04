"""Source discovery helpers (GitHub, Reddit RSS, Substack via RSSHub)."""
from __future__ import annotations

from urllib.parse import quote_plus

import httpx

from app.config import settings
from app.services.storage import slugify


def reddit_search_feed(topic: str) -> str:
    query = quote_plus(topic)
    return f"https://www.reddit.com/search.rss?q={query}&sort=hot"


def medium_tag_feed(topic: str) -> str:
    return f"https://medium.com/feed/tag/{slugify(topic)}"


def substack_search_feed(topic: str) -> str | None:
    if not settings.rsshub_base_url:
        return None
    query = quote_plus(topic)
    base = settings.rsshub_base_url.rstrip("/")
    return f"{base}/substack/search/{query}"


def github_search_url(topic: str) -> str:
    return f"https://github.com/search?q={quote_plus(topic)}&type=repositories"


async def github_search_repos(topic: str, limit: int = 10) -> list[str]:
    """Return top GitHub repo URLs for a topic."""
    query = quote_plus(topic)
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={limit}"
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items", [])
    return [item.get("html_url") for item in items if item.get("html_url")]
