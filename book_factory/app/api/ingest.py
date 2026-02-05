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
    background.add_task(_schedule_ingest, topic.id, slug, topic.name, topic.keywords)
    return {"message": "Ingestion started"}


@router.get("/ingest/failures")
async def ingest_failures(slug: str, db: AsyncSession = Depends(get_db)):
    await _get_topic(db, slug)
    from app.services.storage import topic_dir
    import json

    path = topic_dir(slug) / "metrics" / "ingest_failures.jsonl"
    if not path.exists():
        return {"failures": []}
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    return {"failures": records[-50:]}


def _schedule_ingest(
    topic_id: int,
    slug: str,
    topic_name: str,
    topic_keywords: list[str] | None = None,
) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(run_ingest(topic_id, slug, topic_name, topic_keywords=topic_keywords))
    except RuntimeError:
        asyncio.run(run_ingest(topic_id, slug, topic_name, topic_keywords=topic_keywords))
