"""Trend candidate endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.trend_monitor import TrendMonitor

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("", response_model=list[schemas.TrendCandidateOut])
async def list_trends(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.TrendCandidate).order_by(models.TrendCandidate.discovered_at.desc())
    )
    return result.scalars().all()


@router.post("/refresh", response_model=list[schemas.TrendCandidateOut])
async def refresh_trends(db: AsyncSession = Depends(get_db)):
    monitor = TrendMonitor()
    new_candidates = monitor.fetch()

    for candidate in new_candidates:
        db.add(candidate)

    await db.commit()
    return new_candidates
