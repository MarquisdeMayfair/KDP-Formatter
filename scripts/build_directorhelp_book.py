#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from directorhelp_formatter import DirectorHelpMarkdownAdapter
from directorhelp_formatter.cover import prepare_ebook_cover
from directorhelp_formatter.epub_renderer import EPUBRenderer
from directorhelp_formatter.print_renderer import PrintConfig, PrintRenderer, TRIM_SIZES
from directorhelp_formatter.validator import ValidationFailure, validate_epub, validate_pdf


def main() -> int:
    parser = argparse.ArgumentParser(description="Build DirectorHelp Markdown as a KDP print PDF and reflowable EPUB")
    parser.add_argument("--input", required=True, help="Canonical DirectorHelp Markdown source")
    parser.add_argument("--output-dir", required=True, help="Directory for final and audit files")
    parser.add_argument("--slug", required=True, help="Stable filename stem")
    parser.add_argument("--cover", help="Approved front-cover image")
    parser.add_argument("--trim", choices=sorted(TRIM_SIZES), default="6x9")
    parser.add_argument("--author", default="DirectorHelp Editorial Team")
    parser.add_argument("--publisher", default="New Marylebone Press")
    parser.add_argument("--copyright-holder", default="Moxon AI Group Ltd")
    parser.add_argument("--edition", default="2026/27 Edition 1")
    parser.add_argument("--isbn", default="")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir = output_dir / "audit"
    audit_dir.mkdir(exist_ok=True)

    adapter = DirectorHelpMarkdownAdapter()
    book = adapter.convert(
        args.input,
        author=args.author,
        publisher=args.publisher,
        copyright_holder=args.copyright_holder,
        edition=args.edition,
        isbn=args.isbn,
    )
    (audit_dir / f"{args.slug}-book-model.json").write_text(json.dumps(book.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    cover_output: Path | None = None
    if args.cover:
        cover_output = prepare_ebook_cover(args.cover, output_dir / f"{args.slug}-ebook-cover.jpg")

    config = PrintConfig(trim_size=args.trim)
    pdf_path = output_dir / f"{args.slug}-print-{args.trim}.pdf"
    epub_path = output_dir / f"{args.slug}.epub"
    html_path = audit_dir / f"{args.slug}-print-source.html"

    PrintRenderer(config).render(book, pdf_path, html_output=html_path)
    EPUBRenderer().render(book, epub_path, cover_path=cover_output)

    try:
        pdf_report = validate_pdf(pdf_path, book, config)
        epub_report = validate_epub(epub_path, book)
    except ValidationFailure as exc:
        print(str(exc), file=sys.stderr)
        return 1

    validation = {
        "status": "pass",
        "source": str(Path(args.input).resolve()),
        "book": {
            "title": book.metadata.title,
            "subtitle": book.metadata.subtitle,
            "edition": book.metadata.edition,
            "parts": len(book.parts),
            "chapters": len(book.chapters),
            "source_words": book.word_count,
            "removed_content": book.removed_content,
        },
        "pdf": pdf_report,
        "epub": epub_report,
        "manual_release_gate": "Open the EPUB in Kindle Previewer and upload both files to the relevant KDP previewers before publication.",
    }
    (output_dir / f"{args.slug}-validation.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_upload_readme(
        output_dir,
        args.slug,
        pdf_path.name,
        epub_path.name,
        cover_output.name if cover_output else None,
        args.trim,
        pdf_report["summary"]["page_count"],
    )

    print(f"PASS: {book.metadata.title}")
    print(f"Print PDF: {pdf_path}")
    print(f"EPUB: {epub_path}")
    if cover_output:
        print(f"Ebook cover: {cover_output}")
    print(f"Validation: {output_dir / f'{args.slug}-validation.json'}")
    return 0


def _write_upload_readme(
    output_dir: Path,
    slug: str,
    pdf_name: str,
    epub_name: str,
    cover_name: str | None,
    trim: str,
    page_count: int,
) -> None:
    cover_line = f"- Ebook cover: `{cover_name}`\n" if cover_name else ""
    text = f"""# KDP upload package: {slug}

Automated validation has passed. The final Amazon preview remains a human release gate.

## Files

- Paperback interior: `{pdf_name}`
- Kindle manuscript: `{epub_name}`
{cover_line}- Validation evidence: `{slug}-validation.json`

## Paperback setup

- Trim size: {trim.replace('x', ' x ')} inches
- Interior page count: {page_count}
- Interior: black ink, no bleed
- Upload `{pdf_name}` as the manuscript interior
- Use the final page count reported in validation to create the full paperback cover and spine
- At this short page count, use the KDP cover template without spine text
- Open Print Previewer and inspect every page, especially tables, part openings and blank recto/verso pages

## Kindle setup

- Upload `{epub_name}` as the reflowable manuscript
- Upload the ebook cover separately
- Open Kindle Previewer and inspect phone, tablet and e-reader views
- Test the navigation table of contents, links, tables, footnotes and font resizing

Do not publish if either Amazon previewer introduces a warning or a layout defect.
"""
    (output_dir / "KDP-UPLOAD-README.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
