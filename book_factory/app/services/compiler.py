"""Compile manuscript and manage image placeholders."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from app.services.storage import topic_dir

PLACEHOLDER_RE = re.compile(r"\[\[(IMAGE|COVER|BACK_COVER):(.+?)\]\]", re.IGNORECASE)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def compile_manuscript(slug: str, source_paths: Iterable[Path]) -> Path:
    book_dir = topic_dir(slug) / "book"
    book_dir.mkdir(parents=True, exist_ok=True)

    manuscript_path = book_dir / "manuscript_raw.md"
    parts = []
    for path in source_paths:
        text = _read_text(path)
        if text:
            parts.append(text.strip())

    manuscript_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return manuscript_path


def build_sources_page(slug: str, urls: Iterable[str]) -> Path:
    book_dir = topic_dir(slug) / "book"
    book_dir.mkdir(parents=True, exist_ok=True)
    sources_path = topic_dir(slug) / "sources.md"

    unique = []
    seen = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(url)

    lines = ["# Sources", ""]
    for url in unique:
        lines.append(f"- {url}")
    sources_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sources_path


def build_image_manifest(slug: str, manuscript_path: Path) -> Path:
    book_dir = topic_dir(slug) / "book"
    text = _read_text(manuscript_path)
    manifest = []
    for idx, match in enumerate(PLACEHOLDER_RE.finditer(text), start=1):
        image_type = match.group(1).upper()
        description = match.group(2).strip()
        manifest.append({
            "id": f"img-{idx:03d}",
            "type": image_type,
            "description": description,
            "placeholder": match.group(0),
        })

    manifest_path = book_dir / "image_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def apply_images(slug: str, replacements: dict[str, str]) -> Path:
    book_dir = topic_dir(slug) / "book"
    manuscript_path = book_dir / "manuscript_raw.md"
    output_path = book_dir / "manuscript_with_images.md"
    text = _read_text(manuscript_path)

    for placeholder, image_path in replacements.items():
        text = text.replace(placeholder, f"![Illustration]({image_path})")

    output_path.write_text(text, encoding="utf-8")
    return output_path
