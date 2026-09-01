from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml

from .model import Book, BookMetadata, BookSection, Chapter, Part


PART_HEADING = re.compile(r"^#\s+PART\s+(.+?)\s*$", re.IGNORECASE)
H1_HEADING = re.compile(r"^#\s+(.+?)\s*$")
H2_HEADING = re.compile(r"^##\s+(.+?)\s*$")
CHAPTER_HEADING = re.compile(r"^(\d+)\.\s+(.+?)\s*$")
BUILD_NOTES_HEADING = re.compile(r"^##\s+Build notes\b", re.IGNORECASE)
BACK_MATTER_HEADINGS = {
    "sources and currency",
    "sources",
    "source notes",
    "disclaimers",
    "disclaimer",
    "further reading",
    "acknowledgements",
    "about directorhelp",
}

WEB_ONLY_PATTERNS = [
    re.compile(r"^\s*\[(?:ADVERTISEMENT|AD|TMD|CTA)(?::[^\]]*)?\]\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:Download the PDF|Download this guide|Join the Directors['’] Briefing|Subscribe to continue)\b.*$", re.IGNORECASE),
    re.compile(r"^\s*Commercial disclosure\.\s*DirectorHelp.*advertis", re.IGNORECASE),
]


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "section"


def normalize_typography(value: str) -> str:
    replacements = {
        "\u00a0": " ",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": " - ",
        "\u2212": "-",
        "\u2026": "...",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r" {2,}", " ", value)
    return value


class DirectorHelpMarkdownAdapter:
    """Convert canonical DirectorHelp Markdown into a deterministic book model."""

    def __init__(self, base_url: str = "https://www.directorhelp.org/") -> None:
        self.base_url = base_url.rstrip("/") + "/"

    def convert(
        self,
        source_path: str | Path,
        *,
        author: str = "DirectorHelp Editorial Team",
        publisher: str = "New Marylebone Press",
        copyright_holder: str = "Moxon AI Group Ltd",
        edition: str = "2026/27 Edition 1",
        isbn: str = "",
    ) -> Book:
        path = Path(source_path)
        raw = path.read_text(encoding="utf-8")
        yaml_metadata, markdown = self._extract_front_matter(raw)
        cleaned, removed = self._clean_markdown(markdown)
        lines = cleaned.splitlines()

        title, subtitle = self._extract_title_and_subtitle(lines, path.stem)
        checked_date = self._extract_checked_date(cleaned)
        metadata = BookMetadata(
            title=str(yaml_metadata.get("title") or title),
            subtitle=str(yaml_metadata.get("subtitle") or subtitle),
            author=str(yaml_metadata.get("author") or author),
            publisher=str(yaml_metadata.get("publisher") or publisher),
            copyright_holder=str(yaml_metadata.get("copyright_holder") or copyright_holder),
            edition=str(yaml_metadata.get("edition") or edition),
            language=str(yaml_metadata.get("language") or "en-GB"),
            isbn=str(yaml_metadata.get("isbn") or isbn),
            source_url=str(yaml_metadata.get("source_url") or self.base_url),
            checked_date=checked_date,
        )

        book = Book(metadata=metadata, removed_content=removed)
        self._map_structure(lines, book)
        self._validate_structure(book)
        return book

    @staticmethod
    def _extract_front_matter(raw: str) -> tuple[dict, str]:
        if not raw.startswith("---\n"):
            return {}, raw
        closing = raw.find("\n---\n", 4)
        if closing == -1:
            raise ValueError("YAML front matter starts but does not close")
        metadata = yaml.safe_load(raw[4:closing]) or {}
        if not isinstance(metadata, dict):
            raise ValueError("YAML front matter must be a mapping")
        return metadata, raw[closing + 5 :]

    def _clean_markdown(self, markdown: str) -> tuple[str, list[str]]:
        lines = markdown.splitlines()
        kept: list[str] = []
        removed: list[str] = []
        in_html_comment = False
        seen_disclosures: set[str] = set()

        for line in lines:
            if BUILD_NOTES_HEADING.match(line):
                removed.append("Build notes and everything below them")
                break

            if "<!--" in line:
                in_html_comment = True
            if in_html_comment:
                removed.append(line.strip())
                if "-->" in line:
                    in_html_comment = False
                continue

            plain_line = re.sub(r"[*_`]", "", line)
            if any(pattern.search(line) or pattern.search(plain_line) for pattern in WEB_ONLY_PATTERNS):
                removed.append(line.strip())
                continue

            disclosure_key = re.sub(r"\s+", " ", re.sub(r"[*_`]", "", line)).strip().lower()
            if disclosure_key.startswith(("this is information, not advice", "independent expert verification is pending")):
                if disclosure_key in seen_disclosures:
                    removed.append(f"Repeated disclosure: {line.strip()}")
                    continue
                seen_disclosures.add(disclosure_key)

            if re.match(r"^\s*(?:<AdSlot\b|<aside\b[^>]*class=[\"'][^\"']*ad)", line, re.IGNORECASE):
                removed.append(line.strip())
                continue

            kept.append(line)

        cleaned = normalize_typography("\n".join(kept))
        cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned).strip() + "\n"
        return cleaned, removed

    @staticmethod
    def _extract_title_and_subtitle(lines: list[str], fallback: str) -> tuple[str, str]:
        title = fallback.replace("-", " ").title()
        subtitle = ""
        for index, line in enumerate(lines):
            match = H1_HEADING.match(line)
            if not match or PART_HEADING.match(line):
                continue
            title = re.sub(r"[*_`]", "", match.group(1)).strip()
            for candidate in lines[index + 1 : index + 8]:
                if candidate.startswith("### "):
                    subtitle = re.sub(r"[*_`]", "", candidate[4:]).strip()
                    break
                if PART_HEADING.match(candidate):
                    break
            break
        return title, subtitle

    @staticmethod
    def _extract_checked_date(markdown: str) -> str:
        match = re.search(r"Research reviewed on\s+([^.*\n]+)", markdown, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _map_structure(self, lines: list[str], book: Book) -> None:
        first_part_index = next((i for i, line in enumerate(lines) if PART_HEADING.match(line)), None)
        if first_part_index is None:
            raise ValueError("DirectorHelp book source must contain explicit '# PART ...' headings")

        introduction = self._clean_introduction(lines[:first_part_index])
        book.introduction_markdown = introduction

        current_part: Part | None = None
        current_chapter: Chapter | None = None
        current_back: BookSection | None = None
        buffer: list[str] = []
        pending_part_label: str | None = None

        def flush() -> None:
            nonlocal buffer
            text = self._trim_section(buffer)
            if current_chapter is not None:
                current_chapter.markdown = text
            elif current_back is not None:
                current_back.markdown = text
            buffer = []

        for line in lines[first_part_index:]:
            part_match = PART_HEADING.match(line)
            if part_match:
                flush()
                current_chapter = None
                current_back = None
                pending_part_label = f"Part {part_match.group(1).strip().title()}"
                current_part = None
                continue

            h1_match = H1_HEADING.match(line)
            if pending_part_label and h1_match:
                part_title = re.sub(r"[*_`]", "", h1_match.group(1)).strip()
                current_part = Part(
                    label=pending_part_label,
                    title=part_title,
                    slug=slugify(f"{pending_part_label}-{part_title}"),
                )
                book.parts.append(current_part)
                pending_part_label = None
                continue

            h2_match = H2_HEADING.match(line)
            if h2_match:
                heading = re.sub(r"[*_`]", "", h2_match.group(1)).strip()
                chapter_match = CHAPTER_HEADING.match(heading)
                if chapter_match:
                    if current_part is None:
                        raise ValueError(f"Chapter appears before a part: {heading}")
                    flush()
                    current_back = None
                    current_chapter = Chapter(
                        number=int(chapter_match.group(1)),
                        title=chapter_match.group(2).strip(),
                        markdown="",
                        slug=slugify(f"chapter-{chapter_match.group(1)}-{chapter_match.group(2)}"),
                    )
                    current_part.chapters.append(current_chapter)
                    continue
                if heading.lower() in BACK_MATTER_HEADINGS:
                    flush()
                    current_chapter = None
                    current_back = BookSection(title=heading, markdown="", slug=slugify(heading))
                    book.back_matter.append(current_back)
                    continue

            if pending_part_label and line.strip() in {"", "---"}:
                continue
            if current_part is None and current_chapter is None and current_back is None:
                continue
            buffer.append(line)

        flush()

    @staticmethod
    def _clean_introduction(lines: list[str]) -> str:
        kept: list[str] = []
        skipping_contents = False
        skipped_subtitle = False
        for index, line in enumerate(lines):
            if index == 0 and H1_HEADING.match(line):
                continue
            if line.startswith("### ") and not skipped_subtitle and not any(item.strip() for item in kept):
                skipped_subtitle = True
                continue
            if H2_HEADING.match(line) and H2_HEADING.match(line).group(1).strip().lower() == "contents":
                skipping_contents = True
                continue
            if skipping_contents:
                if line.strip() == "---":
                    skipping_contents = False
                continue
            kept.append(line)
        return DirectorHelpMarkdownAdapter._trim_section(kept)

    @staticmethod
    def _trim_section(lines: list[str]) -> str:
        while lines and lines[0].strip() in {"", "---"}:
            lines.pop(0)
        while lines and lines[-1].strip() in {"", "---"}:
            lines.pop()
        text = "\n".join(lines).strip()
        return text + ("\n" if text else "")

    @staticmethod
    def _validate_structure(book: Book) -> None:
        if not book.metadata.title:
            raise ValueError("Book title is missing")
        if not book.parts:
            raise ValueError("No parts were mapped")
        if not book.chapters:
            raise ValueError("No chapters were mapped")

        chapter_numbers = [chapter.number for chapter in book.chapters]
        if chapter_numbers != list(range(1, len(chapter_numbers) + 1)):
            raise ValueError(f"Chapter numbering is not sequential: {chapter_numbers}")

        empty = [chapter.number for chapter in book.chapters if not chapter.markdown.strip()]
        if empty:
            raise ValueError(f"Chapters have no content: {empty}")
