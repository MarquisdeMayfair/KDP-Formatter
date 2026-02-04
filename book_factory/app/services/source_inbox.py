"""Store source URLs for later ingestion."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

import uuid

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


def append_text(slug: str, text: str, source: str = "manual") -> Path:
    """Append raw text into the topic inbox and return the raw file path."""
    inbox_raw = topic_dir(slug) / "inbox" / "raw"
    inbox_raw.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    file_id = uuid.uuid4().hex[:8]
    path = inbox_raw / f"text-{stamp}-{file_id}.txt"
    path.write_text(text.strip(), encoding="utf-8")

    inbox_meta = topic_dir(slug) / "inbox" / "meta"
    inbox_meta.mkdir(parents=True, exist_ok=True)
    meta_path = inbox_meta / "sources.jsonl"
    record = {
        "url": f"file:{path}",
        "source": source,
        "status": "pending",
        "added_at": datetime.utcnow().isoformat(),
        "doc_type": "text",
    }
    with open(meta_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")

    return path
