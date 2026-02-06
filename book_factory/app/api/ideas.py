"""Idea pool endpoints (scrum-style backlog)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.swarm import auto_assign_ideas

router = APIRouter(prefix="/topics/{slug}/ideas", tags=["ideas"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("", response_model=list[schemas.IdeaOut])
async def list_ideas(
    slug: str,
    status: str | None = None,
    silo_number: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    query = select(models.IdeaItem).where(models.IdeaItem.topic_id == topic.id)
    if status:
        query = query.where(models.IdeaItem.status == status)
    if silo_number is not None:
        query = query.where(models.IdeaItem.silo_number == silo_number)
    result = await db.execute(query.order_by(models.IdeaItem.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=list[schemas.IdeaOut])
async def add_ideas(
    slug: str,
    payload: schemas.IdeaCreate,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    ideas = [idea.strip() for idea in payload.ideas if idea.strip()]
    if not ideas:
        raise HTTPException(status_code=400, detail="No ideas provided")
    created = []
    for idea in ideas:
        item = models.IdeaItem(
            topic_id=topic.id,
            text=idea,
            status="backlog",
            source=payload.source,
        )
        db.add(item)
        created.append(item)
    await db.commit()
    for item in created:
        await db.refresh(item)
    return created


@router.patch("/{idea_id}", response_model=schemas.IdeaOut)
async def update_idea(
    slug: str,
    idea_id: int,
    payload: schemas.IdeaUpdate,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    result = await db.execute(
        select(models.IdeaItem).where(
            models.IdeaItem.topic_id == topic.id,
            models.IdeaItem.id == idea_id,
        )
    )
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    if payload.status is not None:
        idea.status = payload.status
    if payload.silo_number is not None:
        idea.silo_number = payload.silo_number
    if payload.tags is not None:
        idea.tags = payload.tags

    await db.commit()
    await db.refresh(idea)
    return idea


@router.post("/auto-assign")
async def auto_assign(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)
    updated = await auto_assign_ideas(topic.id, topic.name)
    return {"updated": updated}
