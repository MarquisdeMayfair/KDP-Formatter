from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from pypdf import PdfReader

from directorhelp_formatter.adapter import DirectorHelpMarkdownAdapter
from directorhelp_formatter.epub_renderer import EPUBRenderer
from directorhelp_formatter.print_renderer import PrintConfig, PrintRenderer


SAMPLE = """---
title: A Director's Test Book
edition: Test Edition
---

# A Director's Test Book

### A deterministic test

**Research reviewed on 10 August 2026. Independent expert verification is pending.**

## Contents
This source contents block is replaced by generated navigation.

---

# PART ONE
# Start here

## 1. First decision

> **In one sentence**
> Make the decision deliberately.

### Preserve structure

- A list item
- Another list item

| Item | Value |
|---|---|
| Threshold | £90,000 |

☐ **Take an action.** Keep the checklist.
☐ Take another action.
☐ Take a third action.

[Read the source](/guides/example)

## 2. Second decision

This is information, not advice.

This is information, not advice.

[ADVERTISEMENT]

## Sources and currency

The source register stays.

## Build notes (remove before publication)

This must never ship.
"""


class DirectorHelpFormatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "book.md"
        self.source.write_text(SAMPLE, encoding="utf-8")
        self.book = DirectorHelpMarkdownAdapter().convert(self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_maps_explicit_parts_and_chapters_without_inference(self) -> None:
        self.assertEqual(self.book.metadata.title, "A Director's Test Book")
        self.assertEqual(len(self.book.parts), 1)
        self.assertEqual([chapter.number for chapter in self.book.chapters], [1, 2])
        self.assertEqual(self.book.parts[0].title, "Start here")
        self.assertEqual(self.book.back_matter[0].title, "Sources and currency")

    def test_removes_build_notes_ads_contents_and_duplicate_disclosures(self) -> None:
        publication_content = "\n".join(
            [self.book.introduction_markdown]
            + [chapter.markdown for chapter in self.book.chapters]
            + [section.markdown for section in self.book.back_matter]
        )
        self.assertNotIn("This must never ship", publication_content)
        self.assertNotIn("[ADVERTISEMENT]", publication_content)
        self.assertNotIn("source contents block", self.book.introduction_markdown)
        self.assertEqual(publication_content.count("This is information, not advice"), 1)
        self.assertIn("[ADVERTISEMENT]", self.book.removed_content)

    def test_preserves_markdown_features_and_canonicalises_links(self) -> None:
        chapter = self.book.chapters[0].markdown
        self.assertIn("| Item | Value |", chapter)
        self.assertIn("> **In one sentence**", chapter)
        self.assertIn("☐ **Take an action.**", chapter)
        pdf = self.root / "test.pdf"
        html = self.root / "test.html"
        PrintRenderer(PrintConfig(trim_size="7x10")).render(self.book, pdf, html_output=html)
        rendered_html = html.read_text(encoding="utf-8")
        self.assertIn("https://www.directorhelp.org/guides/example", rendered_html)
        self.assertIn('class="checkbox"', rendered_html)
        self.assertIn('class="checklist"', rendered_html)
        self.assertEqual(rendered_html.count('class="action-item"'), 3)
        self.assertIn("<table>", rendered_html)
        first_page = PdfReader(pdf).pages[0]
        self.assertAlmostEqual(float(first_page.mediabox.width), 7 * 72, delta=0.5)
        self.assertAlmostEqual(float(first_page.mediabox.height), 10 * 72, delta=0.5)

    def test_builds_reflowable_epub_with_navigation(self) -> None:
        epub = self.root / "test.epub"
        EPUBRenderer().render(self.book, epub)
        with zipfile.ZipFile(epub) as archive:
            self.assertEqual(archive.namelist()[0], "mimetype")
            self.assertEqual(archive.read("mimetype"), b"application/epub+zip")
            nav = archive.read("EPUB/nav.xhtml").decode("utf-8")
            self.assertIn("Chapter 1: First decision", nav)
            self.assertIn("Chapter 2: Second decision", nav)
            chapter = archive.read("EPUB/text/chapter-1-first-decision.xhtml").decode("utf-8")
            self.assertIn("https://www.directorhelp.org/guides/example", chapter)
            self.assertIn("<table>", chapter)


if __name__ == "__main__":
    unittest.main()
