"""Autopilot endpoints for continuous discovery + ingestion."""
from __future__ import annotations

import asyncio
import json

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.autopilot import run_autopilot
from app.services.storage import topic_dir

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
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    topic = await _get_topic(db, slug)
    metrics_dir = topic_dir(slug) / "metrics"
    stop_path = metrics_dir / "autopilot_stop"
    if stop_path.exists():
        stop_path.unlink()
    if request.headers.get("content-type", "").startswith("application/json"):
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    autopilot_req = schemas.AutopilotRequest(**payload)
    background.add_task(_schedule_autopilot, topic.id, slug, topic.name, autopilot_req)
    if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        return RedirectResponse(url=f"/dashboard?topic={slug}", status_code=303)
    return schemas.AutopilotResponse(
        message="Autopilot started",
        log_path=f"data/topics/{slug}/metrics/autopilot.jsonl",
    )


@router.post("/stop", response_model=schemas.AutopilotResponse)
async def stop_autopilot(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _get_topic(db, slug)
    metrics_dir = topic_dir(slug) / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    stop_path = metrics_dir / "autopilot_stop"
    stop_path.write_text("stop", encoding="utf-8")
    status_path = metrics_dir / "autopilot_status.json"
    status_path.write_text(
        json.dumps({"running": False, "stop_requested": True}),
        encoding="utf-8",
    )
    if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        return RedirectResponse(url=f"/dashboard?topic={slug}", status_code=303)
    return schemas.AutopilotResponse(
        message="Autopilot stop requested",
        log_path=f"data/topics/{slug}/metrics/autopilot.jsonl",
    )


@router.get("/status")
async def autopilot_status(slug: str, db: AsyncSession = Depends(get_db)):
    await _get_topic(db, slug)
    metrics_dir = topic_dir(slug) / "metrics"
    status_path = metrics_dir / "autopilot_status.json"
    log_path = metrics_dir / "autopilot.jsonl"

    status = {}
    if status_path.exists():
        status = json.loads(status_path.read_text(encoding="utf-8"))

    last_line = None
    if log_path.exists():
        with open(log_path, "rb") as handle:
            try:
                handle.seek(-2048, 2)
            except OSError:
                handle.seek(0)
            chunk = handle.read().decode("utf-8", errors="ignore")
            lines = [line for line in chunk.splitlines() if line.strip()]
            if lines:
                last_line = json.loads(lines[-1])

    return {"status": status, "last": last_line}
