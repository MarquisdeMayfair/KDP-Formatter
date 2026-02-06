"""X trend digest endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.database import get_db
from app.services.x_trends import build_trend_digest, summarize_trends

router = APIRouter(prefix="/topics/{slug}/x", tags=["x"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("/trends")
async def x_trends(
    slug: str,
    max_results: int = 30,
    top_authors: int = 8,
    summarize: bool = False,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    digest = build_trend_digest(
        topic.name,
        topic.keywords or [],
        max_results=max_results,
        top_authors=top_authors,
        top_urls=10,
    )
    summary = ""
    if summarize:
        summary = await summarize_trends(digest)
    return {**digest, "summary": summary}
