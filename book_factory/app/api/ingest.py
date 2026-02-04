"""Ingestion endpoints for auto pipeline."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.database import get_db
from app.services.ingestion import fetch_and_clean, chunk_text, classify_chunk, extract_nuggets, append_to_silo
from app.services.ollama_client import OllamaClient
from app.services.storage import SILO_TITLES

router = APIRouter(prefix="/topics/{slug}", tags=["ingest"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/ingest")
async def ingest_topic(slug: str, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)
    background.add_task(_run_ingest, topic.id, slug, topic.name)
    return {"message": "Ingestion started"}


async def _run_ingest(topic_id: int, slug: str, topic_name: str) -> None:
    from app.database import AsyncSessionLocal

    ollama = OllamaClient()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(models.SourceDoc).where(
                models.SourceDoc.topic_id == topic_id,
                models.SourceDoc.status == "pending",
            )
        )
        sources = result.scalars().all()

        for source in sources:
            try:
                text = await fetch_and_clean(source.url)
                chunks = chunk_text(text)

                for chunk in chunks:
                    silo_num = await classify_chunk(ollama, chunk.text, topic_name)
                    silo_title = SILO_TITLES.get(silo_num, "Unclassified")
                    nuggets = await extract_nuggets(ollama, chunk.text, topic_name, silo_title)
                    append_to_silo(slug, silo_num, nuggets)

                source.status = "extracted"
            except Exception:
                source.status = "failed"

        await session.commit()
