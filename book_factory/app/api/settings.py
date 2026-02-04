"""Silo settings endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/topics/{slug}/settings", tags=["settings"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("/silos", response_model=list[schemas.SiloSettingOut])
async def list_silo_settings(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)
    result = await db.execute(
        select(models.SiloSetting).where(models.SiloSetting.topic_id == topic.id).order_by(models.SiloSetting.silo_number)
    )
    return result.scalars().all()


@router.patch("/silos/{silo_number}", response_model=schemas.SiloSettingOut)
async def update_silo_setting(
    slug: str,
    silo_number: int,
    payload: schemas.SiloSettingUpdate,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    result = await db.execute(
        select(models.SiloSetting).where(
            models.SiloSetting.topic_id == topic.id,
            models.SiloSetting.silo_number == silo_number,
        )
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="Silo setting not found")

    if payload.target_words is not None:
        setting.target_words = payload.target_words
    if payload.min_sources is not None:
        setting.min_sources = payload.min_sources
    if payload.min_nuggets is not None:
        setting.min_nuggets = payload.min_nuggets
    if payload.template_json is not None:
        setting.template_json = payload.template_json

    await db.commit()
    await db.refresh(setting)
    return setting
