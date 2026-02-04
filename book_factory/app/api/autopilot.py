"""Autopilot endpoints for continuous discovery + ingestion."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.autopilot import run_autopilot

router = APIRouter(prefix="/topics/{slug}/autopilot", tags=["autopilot"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


def _schedule_autopilot(
    topic_id: int,
    slug: str,
    topic_name: str,
    request: schemas.AutopilotRequest,
) -> None:
    async def _runner():
        await run_autopilot(
            topic_id=topic_id,
            slug=slug,
            topic_name=topic_name,
            max_cycles=request.max_cycles,
            cooldown_seconds=request.cooldown_seconds,
            stop_wordcount=request.stop_wordcount,
            stop_on_no_new=request.stop_on_no_new,
        )

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_runner())
    except RuntimeError:
        asyncio.run(_runner())


@router.post("", response_model=schemas.AutopilotResponse)
async def start_autopilot(
    slug: str,
    request: schemas.AutopilotRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    background.add_task(_schedule_autopilot, topic.id, slug, topic.name, request)
    return schemas.AutopilotResponse(
        message="Autopilot started",
        log_path=f"data/topics/{slug}/metrics/autopilot.jsonl",
    )
