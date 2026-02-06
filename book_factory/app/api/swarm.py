"""Swarm drafting endpoints."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.swarm import run_swarm

router = APIRouter(prefix="/topics/{slug}/swarm", tags=["swarm"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


def _schedule_swarm(
    topic_id: int,
    slug: str,
    topic_name: str,
    voice_preset: str,
    request: schemas.SwarmRunRequest,
) -> None:
    async def _runner():
        await run_swarm(
            topic_id=topic_id,
            slug=slug,
            topic_name=topic_name,
            voice_preset=voice_preset,
            silos=request.silos,
            include_unassigned_ideas=request.include_unassigned_ideas,
        )

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_runner())
    except RuntimeError:
        asyncio.run(_runner())


@router.post("/run")
async def run_swarm_endpoint(
    slug: str,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    if request.headers.get("content-type", "").startswith("application/json"):
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    swarm_req = schemas.SwarmRunRequest(**payload)
    background.add_task(
        _schedule_swarm,
        topic.id,
        slug,
        topic.name,
        topic.author_voice_preset,
        swarm_req,
    )

    if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        return RedirectResponse(url=f"/dashboard?topic={slug}", status_code=303)
    return {"message": "Swarm run started"}
