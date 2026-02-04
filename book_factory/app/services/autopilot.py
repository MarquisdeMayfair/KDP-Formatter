"""Autopilot loop for discovery + ingestion with metrics."""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, func

from app import models
from app.database import AsyncSessionLocal
from app.services.discovery import collect_discovery_urls, github_search_repos
from app.services.ingest_runner import run_ingest
from app.services.metrics import word_count
from app.services.source_queue import queue_sources
from app.services.storage import silo_paths, topic_dir


def _draft_wordcount_total(slug: str) -> int:
    total = 0
    for silo_number in range(0, 11):
        draft_path, _, _ = silo_paths(slug, silo_number)
        total += word_count(str(draft_path))
    return total


async def _pending_count(session: AsyncSessionLocal, topic_id: int) -> int:
    result = await session.execute(
        select(func.count()).where(
            models.SourceDoc.topic_id == topic_id,
            models.SourceDoc.status == "pending",
        )
    )
    return int(result.scalar() or 0)


async def run_autopilot(
    topic_id: int,
    slug: str,
    topic_name: str,
    max_cycles: int = 6,
    cooldown_seconds: int = 30,
    stop_wordcount: int | None = None,
    stop_on_no_new: bool = True,
) -> str:
    log_dir = topic_dir(slug) / "metrics"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "autopilot.jsonl"

    for cycle in range(1, max_cycles + 1):
        start = time.monotonic()
        async with AsyncSessionLocal() as session:
            pending_before = await _pending_count(session, topic_id)

            per_feed = None if pending_before < 50 else 8
            feed_urls = collect_discovery_urls(topic_name, per_feed=per_feed)
            repos = await github_search_repos(topic_name, limit=8)
            candidates = list(dict.fromkeys(feed_urls + repos))
            queued = await queue_sources(session, topic_id, slug, candidates, source_label="discovery")

            ingest_stats = await run_ingest(topic_id, slug, topic_name)
            pending_after = await _pending_count(session, topic_id)

        draft_words = _draft_wordcount_total(slug)
        duration = round(time.monotonic() - start, 2)

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "cycle": cycle,
            "queued": queued,
            "candidates": len(candidates),
            "pending_before": pending_before,
            "pending_after": pending_after,
            "draft_words": draft_words,
            "duration_seconds": duration,
            "ingest": ingest_stats,
        }
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

        if stop_wordcount and draft_words >= stop_wordcount:
            break
        if stop_on_no_new and queued == 0 and ingest_stats["processed"] == 0:
            break

        time.sleep(cooldown_seconds)

    return str(log_path)
