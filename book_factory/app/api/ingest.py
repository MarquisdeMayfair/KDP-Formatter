"""Ingestion endpoints for auto pipeline."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.database import get_db
from app.services.ingest_runner import run_ingest

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
    background.add_task(_schedule_ingest, topic.id, slug, topic.name)
    return {"message": "Ingestion started"}


def _schedule_ingest(topic_id: int, slug: str, topic_name: str) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(run_ingest(topic_id, slug, topic_name))
    except RuntimeError:
        asyncio.run(run_ingest(topic_id, slug, topic_name))
