"""Author notes storage."""
from __future__ import annotations

from pathlib import Path

from app.services.storage import silo_dir


def notes_path(slug: str, silo_number: int) -> Path:
    return silo_dir(slug, silo_number) / "author_notes.txt"


def append_notes(slug: str, silo_number: int, text: str) -> Path:
    path = notes_path(slug, silo_number)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(text.strip() + "\n")
    return path


def read_notes(slug: str, silo_number: int) -> str:
    path = notes_path(slug, silo_number)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
