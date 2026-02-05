"""Reusable ingestion runner with stats."""
from __future__ import annotations

import time

from sqlalchemy import select

from app import models
from app.config import settings
from app.database import AsyncSessionLocal
from app.services.ingestion import (
    append_to_silo,
    classify_chunk,
    extract_nuggets,
    fetch_and_clean,
    is_x_url,
    chunk_text,
)
from app.services.ingest_log import log_failure, log_success
from app.services.ollama_client import OllamaClient
from app.services.storage import SILO_TITLES


async def run_ingest(topic_id: int, slug: str, topic_name: str) -> dict:
    """Process pending sources and return stats."""
    start = time.monotonic()
    ollama = OllamaClient()

    processed = 0
    extracted = 0
    failed = 0
    x_calls = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(models.SourceDoc).where(
                models.SourceDoc.topic_id == topic_id,
                models.SourceDoc.status == "pending",
            )
        )
        sources = result.scalars().all()

        max_calls = settings.x_max_calls_per_run
        for source in sources:
            if is_x_url(source.url) and x_calls >= max_calls:
                continue
            processed += 1
            try:
                started = time.monotonic()
                text = await fetch_and_clean(source.url)
                if len(text.split()) < settings.ingest_min_words:
                    raise ValueError("too_short")
                chunks = chunk_text(text)

                for chunk in chunks:
                    silo_num = await classify_chunk(ollama, chunk.text, topic_name)
                    silo_title = SILO_TITLES.get(silo_num, "Unclassified")
                    nuggets = await extract_nuggets(ollama, chunk.text, topic_name, silo_title)
                    append_to_silo(slug, silo_num, nuggets)

                source.status = "extracted"
                extracted += 1
                if is_x_url(source.url):
                    x_calls += 1
                log_success(slug, source.url, len(text.split()), time.monotonic() - started)
            except Exception as exc:
                source.status = "failed"
                failed += 1
                reason = "failed"
                if isinstance(exc, ValueError):
                    reason = str(exc) or "failed"
                log_failure(slug, source.url, reason)

            await session.commit()

    duration = time.monotonic() - start
    return {
        "processed": processed,
        "extracted": extracted,
        "failed": failed,
        "x_calls": x_calls,
        "duration_seconds": round(duration, 2),
    }
