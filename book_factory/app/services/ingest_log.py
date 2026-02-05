"""Helpers to log ingestion outcomes."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.services.storage import topic_dir


def _log_path(slug: str, name: str) -> Path:
    metrics_dir = topic_dir(slug) / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    return metrics_dir / name


def log_failure(slug: str, url: str, reason: str) -> None:
    path = _log_path(slug, "ingest_failures.jsonl")
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "url": url,
        "reason": reason,
    }
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def log_success(slug: str, url: str, word_count: int, duration_seconds: float) -> None:
    path = _log_path(slug, "ingest_success.jsonl")
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "url": url,
        "word_count": word_count,
        "duration_seconds": round(duration_seconds, 2),
    }
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
