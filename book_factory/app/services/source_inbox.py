"""Store source URLs for later ingestion."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.services.storage import topic_dir


def append_sources(slug: str, urls: Iterable[str], source: str = "manual") -> Path:
    """Append URLs to the topic inbox meta file as JSONL."""
    inbox_meta = topic_dir(slug) / "inbox" / "meta"
    inbox_meta.mkdir(parents=True, exist_ok=True)
    path = inbox_meta / "sources.jsonl"
    timestamp = datetime.utcnow().isoformat()

    with open(path, "a", encoding="utf-8") as handle:
        for url in urls:
            record = {
                "url": url,
                "source": source,
                "status": "pending",
                "added_at": timestamp,
            }
            handle.write(json.dumps(record) + "\n")

    return path
