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
    cse_discover,
)
from app.services.topic_utils import build_or_query, normalize_terms
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

    terms = normalize_terms(topic.name, topic.keywords)
    query = build_or_query(terms) or topic.name
    primary_term = terms[0] if terms else topic.name
    feeds = {
        "reddit": reddit_search_feed(query),
        "medium": medium_tag_feed(primary_term),
        "substack": substack_search_feed(query),
        "github_search": github_search_url(topic.name, keywords=topic.keywords),
    }

    repos = await github_search_repos(topic.name, keywords=topic.keywords, limit=8)

    return {
        "topic": topic.name,
        "feeds": feeds,
        "seed_urls": topic.seed_urls or [],
        "github_repos": repos,
    }


@router.post("/queue")
async def queue_discovered_sources(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)

    pending_result = await db.execute(
        select(models.SourceDoc).where(
            models.SourceDoc.topic_id == topic.id,
            models.SourceDoc.status == "pending",
        )
    )
    pending_count = len(pending_result.scalars().all())

    per_feed = None if pending_count < 50 else 8
    seeded = await queue_sources(db, topic.id, topic.slug, topic.seed_urls or [], source_label="seed")
    feed_urls = collect_discovery_urls(topic.name, per_feed=per_feed, keywords=topic.keywords)
    repos = await github_search_repos(topic.name, keywords=topic.keywords, limit=8)
    cse_sources = cse_discover(topic.name, keywords=topic.keywords)
    candidates = list(dict.fromkeys(feed_urls + repos))

    queued = await queue_sources(db, topic.id, topic.slug, candidates, source_label="discovery")
    queued += await queue_sources(db, topic.id, topic.slug, cse_sources, source_label="cse")

    return {
        "topic": topic.name,
        "queued": queued,
        "seeded": seeded,
        "candidates": len(candidates),
        "cse_candidates": len(cse_sources),
        "pending_before": pending_count,
    }
