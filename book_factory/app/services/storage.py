"""Filesystem helpers for topic storage."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Tuple

from app.config import settings


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\\s-]", "", value)
    value = re.sub(r"\\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value or "topic"


SILO_TITLES = {
    0: "Unclassified",
    1: "The Why Now Brief",
    2: "The 1-Hour Quick Start",
    3: "Core Concepts Without the Fluff",
    4: "Step-By-Step Build",
    5: "Real-World Use Cases",
    6: "Gotchas, Fail States, Troubleshooting",
    7: "Security, Privacy, Risks, Compliance",
    8: "Performance, Scale, Cost Control",
    9: "Tooling, Templates, Checklists",
    10: "Roadmap, What's Next, Series Hooks",
}


def topic_dir(slug: str) -> Path:
    return Path(settings.storage_path) / slug


def silo_dir(slug: str, silo_number: int) -> Path:
    return topic_dir(slug) / f"silo_{silo_number:02d}"


def ensure_topic_structure(slug: str) -> None:
    base = topic_dir(slug)
    (base / "inbox" / "raw").mkdir(parents=True, exist_ok=True)
    (base / "inbox" / "clean").mkdir(parents=True, exist_ok=True)
    (base / "inbox" / "meta").mkdir(parents=True, exist_ok=True)
    (base / "chunks").mkdir(parents=True, exist_ok=True)
    (base / "book").mkdir(parents=True, exist_ok=True)

    front_matter = base / "front_matter.md"
    if not front_matter.exists():
        front_matter.write_text("# Author's Opening\n\n", encoding="utf-8")
    conclusion = base / "conclusion.md"
    if not conclusion.exists():
        conclusion.write_text("# Conclusion\n\n", encoding="utf-8")
    sources_page = base / "sources.md"
    if not sources_page.exists():
        sources_page.write_text("# Sources\n\n", encoding="utf-8")

    for silo_num, title in SILO_TITLES.items():
        sdir = silo_dir(slug, silo_num)
        sdir.mkdir(parents=True, exist_ok=True)
        draft_path = sdir / "draft.md"
        if not draft_path.exists():
            draft_path.write_text(f"# {title}\n\n", encoding="utf-8")


def silo_paths(slug: str, silo_number: int) -> Tuple[Path, Path, Path]:
    sdir = silo_dir(slug, silo_number)
    draft_path = sdir / "draft.md"
    final_path = sdir / "final.txt"
    audio_path = sdir / "draft.mp3"
    return draft_path, final_path, audio_path
