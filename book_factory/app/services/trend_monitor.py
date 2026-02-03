"""RSS-based trend monitor to avoid scraping/captcha."""
from __future__ import annotations

from datetime import datetime

import feedparser
from urllib.parse import quote_plus

from app.services.storage import slugify

from app.config import settings
from app.models import TrendCandidate


class TrendMonitor:
    """Fetch trend candidates from configured RSS feeds."""

    def __init__(self) -> None:
        self.feeds = settings.trend_rss_feeds

    def fetch(self) -> list[TrendCandidate]:
        candidates: list[TrendCandidate] = []
        for feed_url in self.feeds:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:20]:
                title = getattr(entry, "title", "").strip()
                if not title:
                    continue
                description = getattr(entry, "summary", None)
                candidates.append(
                    TrendCandidate(
                        source="rss",
                        topic_name=title,
                        description=description,
                        discovered_at=datetime.utcnow(),
                        status="new",
                    )
                )
        return candidates


def topic_based_feeds(topic_name: str) -> list[str]:
    """Generate RSS feeds based on a topic name."""
    query = quote_plus(topic_name)
    tag = slugify(topic_name)

    feeds = [
        f"https://www.reddit.com/search.rss?q={query}&sort=hot",
        f"https://medium.com/feed/tag/{tag}",
    ]
    return feeds
