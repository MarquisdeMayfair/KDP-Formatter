"""X trend digest helpers."""
from __future__ import annotations

from collections import Counter
from typing import Any

from app.services.x_client import search_recent_tweets
from app.services.topic_utils import build_or_query, normalize_terms
from app.services.openai_compat_client import OpenAICompatClient
from app.config import settings


def _score(metrics: dict | None) -> int:
    if not metrics:
        return 0
    return (
        int(metrics.get("like_count", 0))
        + 2 * int(metrics.get("retweet_count", 0))
        + int(metrics.get("reply_count", 0))
        + int(metrics.get("quote_count", 0))
    )


def build_trend_digest(
    topic_name: str,
    keywords: list[str] | None = None,
    max_results: int = 30,
    top_authors: int = 8,
    top_urls: int = 10,
) -> dict[str, Any]:
    query = build_or_query(normalize_terms(topic_name, keywords)) or topic_name
    tweets = search_recent_tweets(query, max_results=max_results)

    by_author: dict[str, dict[str, Any]] = {}
    url_counts: Counter[str] = Counter()

    for tweet in tweets:
        for url in tweet.get("urls", []) or []:
            url_counts[url] += 1

        author_id = tweet.get("author_id") or "unknown"
        score = _score(tweet.get("public_metrics"))
        current = by_author.get(author_id)
        if current is None or score > current.get("score", 0):
            by_author[author_id] = {
                "author_id": author_id,
                "username": tweet.get("username"),
                "name": tweet.get("name"),
                "score": score,
                "tweet": tweet.get("text"),
                "urls": tweet.get("urls", []),
            }

    top_authors_list = sorted(by_author.values(), key=lambda item: item.get("score", 0), reverse=True)[:top_authors]
    top_urls_list = [{"url": url, "mentions": count} for url, count in url_counts.most_common(top_urls)]

    return {
        "query": query,
        "tweets": tweets,
        "top_authors": top_authors_list,
        "top_urls": top_urls_list,
    }


async def summarize_trends(digest: dict[str, Any]) -> str:
    if not settings.grok_api_key:
        return ""
    client = OpenAICompatClient(
        settings.grok_api_key,
        settings.grok_base_url,
        settings.grok_model,
        settings.openai_compat_path,
    )
    system_prompt = (
        "You summarize current X discourse for a tech book. "
        "Focus on what is trending, who is influential, and notable claims."
    )
    user_prompt = (
        "Provide a concise summary (200-300 words) and bullet list of key claims. "
        "Use only the provided data; do not invent.\n\n"
        f"Top authors: {digest.get('top_authors', [])}\n"
        f"Top URLs: {digest.get('top_urls', [])}\n"
        f"Sample tweets: {digest.get('tweets', [])[:10]}"
    )
    return await client.generate(system_prompt, user_prompt, max_tokens=600)
