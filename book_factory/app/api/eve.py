"""Eve integration endpoints with API key auth."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.services.storage import ensure_topic_structure, SILO_TITLES, silo_paths, slugify
from app.services.source_inbox import append_sources

router = APIRouter(prefix="/eve", tags=["eve"])


def _auth(authorization: str = Header("")) -> None:
    if not settings.eve_api_key:
        raise HTTPException(status_code=500, detail="Eve API key not configured")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != settings.eve_api_key:
        raise HTTPException(status_code=403, detail="Invalid token")


@router.post("/topics", dependencies=[Depends(_auth)], response_model=schemas.TopicDetail)
async def eve_create_topic(payload: schemas.TopicCreate, db: AsyncSession = Depends(get_db)):
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
        status="research",
    )
    db.add(topic)
    await db.flush()

    ensure_topic_structure(slug)
    for silo_number, title in SILO_TITLES.items():
        draft_path, final_path, audio_path = silo_paths(slug, silo_number)
        db.add(
            models.Silo(
                topic_id=topic.id,
                silo_number=silo_number,
                name_template=title,
                draft_md_path=str(draft_path),
                final_txt_path=str(final_path),
                review_audio_path=str(audio_path),
                status="drafting" if silo_number == 0 else "empty",
            )
        )

    await db.commit()
    await db.refresh(topic)
    return topic


@router.post("/topics/{slug}/sources", dependencies=[Depends(_auth)], response_model=list[schemas.SourceOut])
async def eve_add_sources(slug: str, payload: schemas.SourceCreate, db: AsyncSession = Depends(get_db)):
    topic_result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = topic_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    urls = [url.strip() for url in payload.urls if url.strip()]
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    append_sources(slug, urls, source=payload.source)

    created = []
    for url in urls:
        doc = models.SourceDoc(topic_id=topic.id, url=url, status="pending")
        db.add(doc)
        created.append(doc)

    await db.commit()
    for doc in created:
        await db.refresh(doc)

    return created
