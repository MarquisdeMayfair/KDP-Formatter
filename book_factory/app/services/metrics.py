"""Utility metrics for dashboard."""
from __future__ import annotations

from pathlib import Path


def word_count(path: str) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    text = p.read_text(encoding="utf-8", errors="ignore")
    return len(text.split())


def total_word_count(paths: list[str]) -> int:
    return sum(word_count(path) for path in paths)
