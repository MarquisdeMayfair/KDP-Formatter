"""Source discovery helpers (GitHub, Reddit RSS, Substack via RSSHub)."""
from __future__ import annotations

from urllib.parse import quote_plus

import httpx
import feedparser
import requests

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


def extract_feed_entries(feed_url: str, limit: int | None = 8) -> list[str]:
    parsed = feedparser.parse(feed_url)
    urls: list[str] = []
    entries = parsed.entries if limit in (None, 0) else parsed.entries[:limit]
    for entry in entries:
        link = getattr(entry, "link", None) or getattr(entry, "id", None)
        if link:
            urls.append(link)
    return urls


def collect_discovery_urls(topic_name: str, per_feed: int | None = 8) -> list[str]:
    feeds: list[str] = [
        reddit_search_feed(topic_name),
        medium_tag_feed(topic_name),
    ]
    substack = substack_search_feed(topic_name)
    if substack:
        feeds.append(substack)

    urls: list[str] = []
    for feed in feeds:
        urls.extend(extract_feed_entries(feed, limit=per_feed))

    # De-duplicate while preserving order
    deduped = list(dict.fromkeys(urls))
    return deduped


def section_query_templates() -> dict[int, list[str]]:
    return {
        1: ["{topic} trend", "{topic} why now", "{topic} market adoption"],
        2: ["{topic} install guide", "{topic} setup", "{topic} onboarding"],
        3: ["{topic} architecture", "{topic} how it works", "{topic} core concepts"],
        4: ["{topic} step by step", "{topic} workflow", "{topic} build guide"],
        5: ["{topic} use cases", "{topic} case study", "{topic} examples"],
        6: ["{topic} troubleshooting", "{topic} fail states", "{topic} gotchas"],
        7: ["{topic} security risks", "{topic} privacy", "{topic} compliance"],
        8: ["{topic} performance", "{topic} scaling", "{topic} cost"],
        9: ["{topic} checklist", "{topic} templates", "{topic} commands"],
        10: ["{topic} roadmap", "{topic} future", "{topic} what's next"],
    }


def cse_search(query: str, date_restrict: str | None = None, num: int = 3) -> list[str]:
    if not settings.google_cse_api_key:
        return []
    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_cx,
        "q": query,
        "num": num,
    }
    if date_restrict:
        params["dateRestrict"] = date_restrict
    resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return [item.get("link") for item in data.get("items", []) if item.get("link")]


def cse_discover(topic_name: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    domains = settings.cse_primary_domains
    per_query = settings.google_cse_results_per_query
    date_restrict = settings.google_cse_date_restrict
    for silo_num, templates in section_query_templates().items():
        for template in templates:
            base_query = template.format(topic=topic_name)
            for domain in domains:
                query = f"{base_query} site:{domain}"
                try:
                    urls = cse_search(query, date_restrict=date_restrict, num=per_query)
                except Exception:
                    urls = []
                for url in urls:
                    results.append((url, f"cse:silo_{silo_num}"))
    deduped = list(dict.fromkeys(results))
    return deduped
