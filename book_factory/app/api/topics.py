"""Topic endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import models, schemas
from app.services.storage import ensure_topic_structure, SILO_TITLES, silo_paths, slugify
from app.services.templates import DEFAULT_SILO_TEMPLATES
from app.services.trend_monitor import topic_based_feeds

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("", response_model=schemas.TopicDetail, status_code=201)
async def create_topic(
    payload: schemas.TopicCreate,
    db: AsyncSession = Depends(get_db),
):
    slug = slugify(payload.name)
    existing = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Topic slug already exists")

    topic = models.Topic(
        slug=slug,
        name=payload.name,
        series_name=payload.series_name,
        book_title=payload.book_title or payload.name,
        subtitle=payload.subtitle,
        author_voice_preset=payload.author_voice_preset,
        target_audience=payload.target_audience,
        stance=payload.stance,
        taboo_list=payload.taboo_list,
        draft_target_words=payload.draft_target_words,
        final_target_words=payload.final_target_words,
        rrp_usd=payload.rrp_usd,
        expected_units=payload.expected_units,
        max_cost_usd=payload.max_cost_usd,
        status="research",
    )
    db.add(topic)
    await db.flush()

    ensure_topic_structure(slug)
    for silo_number, title in SILO_TITLES.items():
        draft_path, final_path, audio_path = silo_paths(slug, silo_number)
        silo = models.Silo(
            topic_id=topic.id,
            silo_number=silo_number,
            name_template=title,
            draft_md_path=str(draft_path),
            final_txt_path=str(final_path),
            review_audio_path=str(audio_path),
            status="drafting" if silo_number == 0 else "empty",
        )
        db.add(silo)

        template = DEFAULT_SILO_TEMPLATES.get(silo_number, {})
        db.add(
            models.SiloSetting(
                topic_id=topic.id,
                silo_number=silo_number,
                target_words=2000,
                min_sources=5,
                min_nuggets=12,
                template_json=template,
            )
        )

    await db.commit()
    await db.refresh(topic)
    return topic


@router.get("", response_model=List[schemas.TopicSummary])
async def list_topics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Topic).order_by(models.Topic.created_at.desc()))
    return result.scalars().all()


@router.get("/{slug}", response_model=schemas.TopicDetail)
async def get_topic(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("/{slug}/suggest-feeds")
async def suggest_feeds(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"topic": topic.name, "feeds": topic_based_feeds(topic.name)}
