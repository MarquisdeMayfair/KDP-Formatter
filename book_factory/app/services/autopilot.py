"""Autopilot loop for discovery + ingestion with metrics."""
from __future__ import annotations

import json
import time
import asyncio
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, func

from app import models
from app.database import AsyncSessionLocal
from app.services.discovery import collect_discovery_urls, github_search_repos, cse_discover
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
    status_path = log_dir / "autopilot_status.json"
    stop_path = log_dir / "autopilot_stop"

    status_path.write_text(
        json.dumps({"running": True, "started_at": datetime.utcnow().isoformat()}),
        encoding="utf-8",
    )

    for cycle in range(1, max_cycles + 1):
        if stop_path.exists():
            break

        start = time.monotonic()
        async with AsyncSessionLocal() as session:
            pending_before = await _pending_count(session, topic_id)

            per_feed = None if pending_before < 50 else 8
            feed_urls = collect_discovery_urls(topic_name, per_feed=per_feed)
            repos = await github_search_repos(topic_name, limit=8)
            candidates = list(dict.fromkeys(feed_urls + repos))
            cse_sources = cse_discover(topic_name)
            queued = await queue_sources(session, topic_id, slug, candidates, source_label="discovery")
            queued += await queue_sources(session, topic_id, slug, cse_sources, source_label="cse")

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

        status_path.write_text(
            json.dumps(
                {
                    "running": True,
                    "last_cycle": cycle,
                    "last_update": datetime.utcnow().isoformat(),
                    "draft_words": draft_words,
                }
            ),
            encoding="utf-8",
        )

        if stop_wordcount and draft_words >= stop_wordcount:
            break
        if stop_on_no_new and queued == 0 and ingest_stats["processed"] == 0:
            break

        # Allow responsive stop during cooldown.
        remaining = cooldown_seconds
        while remaining > 0:
            if stop_path.exists():
                break
            step = 2 if remaining >= 2 else remaining
            await asyncio.sleep(step)
            remaining -= step

    status_path.write_text(
        json.dumps({"running": False, "stopped_at": datetime.utcnow().isoformat()}),
        encoding="utf-8",
    )
    if stop_path.exists():
        stop_path.unlink()
    return str(log_path)
