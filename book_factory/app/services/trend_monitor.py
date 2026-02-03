"""RSS-based trend monitor to avoid scraping/captcha."""
from __future__ import annotations

from datetime import datetime

import feedparser

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
