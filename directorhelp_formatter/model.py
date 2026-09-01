from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BookMetadata:
    title: str
    subtitle: str = ""
    author: str = "DirectorHelp Editorial Team"
    publisher: str = "New Marylebone Press"
    copyright_holder: str = "Moxon AI Group Ltd"
    edition: str = "2026/27 Edition 1"
    language: str = "en-GB"
    isbn: str = ""
    source_url: str = "https://www.directorhelp.org/"
    checked_date: str = ""


@dataclass
class BookSection:
    title: str
    markdown: str
    slug: str


@dataclass
class Chapter:
    number: int
    title: str
    markdown: str
    slug: str


@dataclass
class Part:
    label: str
    title: str
    slug: str
    chapters: list[Chapter] = field(default_factory=list)


@dataclass
class Book:
    metadata: BookMetadata
    introduction_markdown: str = ""
    parts: list[Part] = field(default_factory=list)
    back_matter: list[BookSection] = field(default_factory=list)
    removed_content: list[str] = field(default_factory=list)

    @property
    def chapters(self) -> list[Chapter]:
        return [chapter for part in self.parts for chapter in part.chapters]

    @property
    def word_count(self) -> int:
        content = [self.introduction_markdown]
        content.extend(chapter.markdown for chapter in self.chapters)
        content.extend(section.markdown for section in self.back_matter)
        return len("\n".join(content).split())

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["word_count"] = self.word_count
        result["chapter_count"] = len(self.chapters)
        result["part_count"] = len(self.parts)
        return result
