"""Source intake endpoints."""
from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.source_inbox import append_sources

router = APIRouter(prefix="/topics/{slug}/sources", tags=["sources"])


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except ValueError:
        return ""


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("", response_model=list[schemas.SourceOut])
async def list_sources(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)
    result = await db.execute(select(models.SourceDoc).where(models.SourceDoc.topic_id == topic.id))
    return result.scalars().all()


@router.post("", response_model=list[schemas.SourceOut])
async def add_sources(
    slug: str,
    payload: schemas.SourceCreate,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)

    urls = [url.strip() for url in payload.urls if url.strip()]
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    append_sources(slug, urls, source=payload.source)

    created = []
    for url in urls:
        doc = models.SourceDoc(
            topic_id=topic.id,
            url=url,
            domain=_domain(url),
            status="pending",
        )
        db.add(doc)
        created.append(doc)

    await db.commit()
    for doc in created:
        await db.refresh(doc)

    return created
