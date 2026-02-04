"""Discovery endpoints to seed sources for a topic."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.database import get_db
from app.services.discovery import (
    github_search_repos,
    github_search_url,
    medium_tag_feed,
    reddit_search_feed,
    substack_search_feed,
    collect_discovery_urls,
)
from app.services.source_queue import queue_sources

router = APIRouter(prefix="/topics/{slug}/discover", tags=["discover"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("")
async def discover_sources(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)

    feeds = {
        "reddit": reddit_search_feed(topic.name),
        "medium": medium_tag_feed(topic.name),
        "substack": substack_search_feed(topic.name),
        "github_search": github_search_url(topic.name),
    }

    repos = await github_search_repos(topic.name, limit=8)

    return {
        "topic": topic.name,
        "feeds": feeds,
        "github_repos": repos,
    }


@router.post("/queue")
async def queue_discovered_sources(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)

    feed_urls = collect_discovery_urls(topic.name, per_feed=8)
    repos = await github_search_repos(topic.name, limit=8)
    candidates = list(dict.fromkeys(feed_urls + repos))

    queued = await queue_sources(db, topic.id, topic.slug, candidates, source_label="discovery")

    return {
        "topic": topic.name,
        "queued": queued,
        "candidates": len(candidates),
    }
