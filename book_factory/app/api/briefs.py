"""Chapter brief endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.swarm import ensure_briefs
from app.services.templates import DEFAULT_SILO_TEMPLATES
from app.services.storage import SILO_TITLES

router = APIRouter(prefix="/topics/{slug}/briefs", tags=["briefs"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("", response_model=list[schemas.BriefOut])
async def list_briefs(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)
    await ensure_briefs(topic.id, topic.slug)
    result = await db.execute(
        select(models.ChapterBrief).where(models.ChapterBrief.topic_id == topic.id)
    )
    return result.scalars().all()


@router.put("/{silo_number}", response_model=schemas.BriefOut)
async def update_brief(
    slug: str,
    silo_number: int,
    payload: schemas.BriefUpdate,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    await ensure_briefs(topic.id, topic.slug)
    result = await db.execute(
        select(models.ChapterBrief).where(
            models.ChapterBrief.topic_id == topic.id,
            models.ChapterBrief.silo_number == silo_number,
        )
    )
    brief = result.scalar_one_or_none()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")

    if payload.title is not None:
        brief.title = payload.title
    if payload.goal is not None:
        brief.goal = payload.goal
    if payload.outline is not None:
        brief.outline = payload.outline
    if payload.notes is not None:
        brief.notes = payload.notes
    if payload.status is not None:
        brief.status = payload.status

    await db.commit()
    await db.refresh(brief)
    return brief
