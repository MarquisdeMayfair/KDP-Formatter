from __future__ import annotations

import mimetypes
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .html import markdown_to_html
from .model import Book


class EPUBRenderer:
    """Create a reflowable EPUB 3 without a PDF or heuristic conversion step."""

    def __init__(self) -> None:
        self.package_dir = Path(__file__).resolve().parent
        self.styles_path = self.package_dir / "styles" / "epub.css"
        self.fonts_dir = self.package_dir.parent / "poc" / "fonts"

    def render(self, book: Book, output_path: str | Path, cover_path: str | Path | None = None) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="directorhelp-epub-") as temp:
            root = Path(temp)
            self._write_epub_tree(book, root, Path(cover_path) if cover_path else None)
            self._package(root, output)
        return output

    def _write_epub_tree(self, book: Book, root: Path, cover_path: Path | None) -> None:
        meta_inf = root / "META-INF"
        epub_dir = root / "EPUB"
        text_dir = epub_dir / "text"
        styles_dir = epub_dir / "styles"
        fonts_dir = epub_dir / "fonts"
        images_dir = epub_dir / "images"
        for directory in (meta_inf, text_dir, styles_dir, fonts_dir, images_dir):
            directory.mkdir(parents=True, exist_ok=True)

        (root / "mimetype").write_text("application/epub+zip", encoding="ascii")
        (meta_inf / "container.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>'
            '</rootfiles></container>',
            encoding="utf-8",
        )
        shutil.copy2(self.styles_path, styles_dir / "epub.css")
        for font_name in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"):
            shutil.copy2(self.fonts_dir / font_name, fonts_dir / font_name)

        entries: list[dict[str, str]] = []
        entries.append(self._write_title(book, text_dir))
        entries.append(self._write_copyright(book, text_dir))
        entries.append(self._write_contents(book, text_dir))
        if book.introduction_markdown.strip():
            entries.append(self._write_reader_note(book, text_dir))

        for part in book.parts:
            filename = f"{part.slug}.xhtml"
            body = f'<section class="part-page" epub:type="part"><p class="part-label">{escape(part.label)}</p><h1>{escape(part.title)}</h1></section>'
            self._write_xhtml(text_dir / filename, f"{part.label}: {part.title}", body, book.metadata.language)
            entries.append({"id": part.slug, "href": f"text/{filename}", "title": f"{part.label}: {part.title}", "type": "part"})
            for chapter in part.chapters:
                chapter_file = f"{chapter.slug}.xhtml"
                body = (
                    f'<section class="chapter" epub:type="chapter" id="{escape(chapter.slug)}">'
                    f'<header class="chapter-heading"><p>Chapter {chapter.number}</p><h1>{escape(chapter.title)}</h1></header>'
                    f'<div class="chapter-body">{markdown_to_html(chapter.markdown, book.metadata.source_url)}</div>'
                    '</section>'
                )
                self._write_xhtml(text_dir / chapter_file, chapter.title, body, book.metadata.language)
                entries.append({"id": chapter.slug, "href": f"text/{chapter_file}", "title": f"Chapter {chapter.number}: {chapter.title}", "type": "chapter", "part": part.slug})

        for section in book.back_matter:
            filename = f"{section.slug}.xhtml"
            body = f'<section epub:type="backmatter"><h1>{escape(section.title)}</h1>{markdown_to_html(section.markdown, book.metadata.source_url)}</section>'
            self._write_xhtml(text_dir / filename, section.title, body, book.metadata.language)
            entries.append({"id": section.slug, "href": f"text/{filename}", "title": section.title, "type": "backmatter"})

        cover_info = self._copy_cover(cover_path, images_dir) if cover_path else None
        (epub_dir / "nav.xhtml").write_text(self._nav_xhtml(book, entries), encoding="utf-8")
        (epub_dir / "toc.ncx").write_text(self._toc_ncx(book, entries), encoding="utf-8")
        (epub_dir / "package.opf").write_text(self._package_opf(book, entries, cover_info), encoding="utf-8")

    def _write_title(self, book: Book, text_dir: Path) -> dict[str, str]:
        meta = book.metadata
        subtitle = f'<p class="book-subtitle">{escape(meta.subtitle)}</p>' if meta.subtitle else ""
        body = (
            '<section class="title-page" epub:type="titlepage">'
            '<p class="series">The Director\'s Guide To</p>'
            f'<h1>{escape(meta.title)}</h1>{subtitle}'
            f'<p class="edition">{escape(meta.edition)}</p>'
            '<p class="imprint"><strong>director<span>help</span></strong><br/>New Marylebone Press</p>'
            '</section>'
        )
        self._write_xhtml(text_dir / "title.xhtml", meta.title, body, meta.language)
        return {"id": "title", "href": "text/title.xhtml", "title": meta.title, "type": "frontmatter"}

    def _write_copyright(self, book: Book, text_dir: Path) -> dict[str, str]:
        meta = book.metadata
        checked = f"Research reviewed on {escape(meta.checked_date)}. " if meta.checked_date else ""
        isbn = f"<p>ISBN: {escape(meta.isbn)}</p>" if meta.isbn else ""
        body = (
            '<section class="copyright-page" epub:type="copyright-page">'
            f'<p>Copyright © 2026 {escape(meta.copyright_holder)}.</p>'
            f'<p>Published by {escape(meta.publisher)}.<br/><a href="{escape(meta.source_url)}">{escape(meta.source_url)}</a></p>'
            f'{isbn}<p>{checked}Independent expert verification is pending.</p>'
            '<p>This publication provides general information, not legal, tax, financial or insolvency advice. It is not a personal recommendation. Rules and thresholds change; check the dated live source before acting.</p>'
            '<p>No advertiser has approved, reviewed or altered the editorial content of this edition.</p>'
            '</section>'
        )
        self._write_xhtml(text_dir / "copyright.xhtml", "Copyright", body, meta.language)
        return {"id": "copyright", "href": "text/copyright.xhtml", "title": "Copyright", "type": "frontmatter"}

    def _write_contents(self, book: Book, text_dir: Path) -> dict[str, str]:
        rows = ['<section class="contents-page" epub:type="toc"><h1>Contents</h1>']
        for part in book.parts:
            rows.append(f'<h2><a href="{part.slug}.xhtml">{escape(part.label)}: {escape(part.title)}</a></h2><ol>')
            for chapter in part.chapters:
                rows.append(f'<li><a href="{chapter.slug}.xhtml">{chapter.number}. {escape(chapter.title)}</a></li>')
            rows.append("</ol>")
        if book.back_matter:
            rows.append("<h2>Reference</h2><ul>")
            rows.extend(f'<li><a href="{section.slug}.xhtml">{escape(section.title)}</a></li>' for section in book.back_matter)
            rows.append("</ul>")
        rows.append("</section>")
        self._write_xhtml(text_dir / "contents.xhtml", "Contents", "".join(rows), book.metadata.language)
        return {"id": "contents", "href": "text/contents.xhtml", "title": "Contents", "type": "frontmatter"}

    def _write_reader_note(self, book: Book, text_dir: Path) -> dict[str, str]:
        body = '<section epub:type="preface"><h1>Before you begin</h1>' + markdown_to_html(book.introduction_markdown, book.metadata.source_url) + "</section>"
        self._write_xhtml(text_dir / "before-you-begin.xhtml", "Before you begin", body, book.metadata.language)
        return {"id": "before-you-begin", "href": "text/before-you-begin.xhtml", "title": "Before you begin", "type": "frontmatter"}

    @staticmethod
    def _write_xhtml(path: Path, title: str, body: str, language: str) -> None:
        document = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{escape(language)}" xml:lang="{escape(language)}">'
            f'<head><meta charset="utf-8"/><title>{escape(title)}</title><link rel="stylesheet" type="text/css" href="../styles/epub.css"/></head>'
            f'<body>{body}</body></html>'
        )
        path.write_text(document, encoding="utf-8")

    @staticmethod
    def _copy_cover(cover_path: Path, images_dir: Path) -> dict[str, str]:
        if not cover_path.exists():
            raise FileNotFoundError(f"Cover not found: {cover_path}")
        suffix = cover_path.suffix.lower() or ".jpg"
        filename = f"cover{suffix}"
        shutil.copy2(cover_path, images_dir / filename)
        media_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
        return {"href": f"images/{filename}", "media_type": media_type}

    @staticmethod
    def _book_id(book: Book) -> str:
        seed = f"{book.metadata.title}|{book.metadata.edition}|{book.metadata.author}"
        return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, seed)}"

    def _nav_xhtml(self, book: Book, entries: list[dict[str, str]]) -> str:
        by_part: dict[str, list[dict[str, str]]] = {}
        for entry in entries:
            if entry.get("part"):
                by_part.setdefault(entry["part"], []).append(entry)
        items: list[str] = []
        for entry in entries:
            if entry["type"] == "chapter":
                continue
            if entry["type"] == "part":
                children = "".join(f'<li><a href="{escape(child["href"])}">{escape(child["title"])}</a></li>' for child in by_part.get(entry["id"], []))
                items.append(f'<li><a href="{escape(entry["href"])}">{escape(entry["title"])}</a><ol>{children}</ol></li>')
            else:
                items.append(f'<li><a href="{escape(entry["href"])}">{escape(entry["title"])}</a></li>')
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{escape(book.metadata.language)}">'
            '<head><title>Contents</title></head><body><nav epub:type="toc" id="toc"><h1>Contents</h1><ol>'
            + "".join(items)
            + '</ol></nav><nav epub:type="landmarks" hidden="hidden"><ol>'
              '<li><a epub:type="cover" href="text/title.xhtml">Cover</a></li>'
              '<li><a epub:type="toc" href="text/contents.xhtml">Contents</a></li>'
              '<li><a epub:type="bodymatter" href="' + escape(next(entry["href"] for entry in entries if entry["type"] == "chapter")) + '">Start reading</a></li>'
              '</ol></nav></body></html>'
        )

    def _toc_ncx(self, book: Book, entries: list[dict[str, str]]) -> str:
        points: list[str] = []
        for index, entry in enumerate(entries, start=1):
            points.append(
                f'<navPoint id="navPoint-{index}" playOrder="{index}"><navLabel><text>{escape(entry["title"])}</text></navLabel><content src="{escape(entry["href"])}"/></navPoint>'
            )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
            f'<head><meta name="dtb:uid" content="{self._book_id(book)}"/></head>'
            f'<docTitle><text>{escape(book.metadata.title)}</text></docTitle><navMap>{"".join(points)}</navMap></ncx>'
        )

    def _package_opf(self, book: Book, entries: list[dict[str, str]], cover: dict[str, str] | None) -> str:
        modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest = [
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '<item id="css" href="styles/epub.css" media-type="text/css"/>',
            '<item id="font-regular" href="fonts/SourceSerif4-Regular.ttf" media-type="font/ttf"/>',
            '<item id="font-semibold" href="fonts/SourceSerif4-Semibold.ttf" media-type="font/ttf"/>',
        ]
        manifest.extend(f'<item id="{escape(entry["id"])}" href="{escape(entry["href"])}" media-type="application/xhtml+xml"/>' for entry in entries)
        if cover:
            manifest.append(f'<item id="cover-image" href="{escape(cover["href"])}" media-type="{escape(cover["media_type"])}" properties="cover-image"/>')
        spine = "".join(f'<itemref idref="{escape(entry["id"])}"/>' for entry in entries)
        isbn = f'<dc:identifier id="isbn">{escape(book.metadata.isbn)}</dc:identifier>' if book.metadata.isbn else ""
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="book-id" version="3.0" prefix="rendition: http://www.idpf.org/vocab/rendition/#">'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f'<dc:identifier id="book-id">{self._book_id(book)}</dc:identifier>{isbn}'
            f'<dc:title>{escape(book.metadata.title)}</dc:title>'
            f'<dc:creator>{escape(book.metadata.author)}</dc:creator>'
            f'<dc:publisher>{escape(book.metadata.publisher)}</dc:publisher>'
            f'<dc:language>{escape(book.metadata.language)}</dc:language>'
            f'<dc:rights>Copyright © 2026 {escape(book.metadata.copyright_holder)}</dc:rights>'
            f'<meta property="dcterms:modified">{modified}</meta>'
            '<meta property="rendition:layout">reflowable</meta><meta property="rendition:orientation">auto</meta><meta property="rendition:spread">auto</meta>'
            '</metadata><manifest>' + "".join(manifest) + '</manifest>'
            f'<spine toc="ncx">{spine}</spine></package>'
        )

    @staticmethod
    def _package(root: Path, output: Path) -> None:
        with zipfile.ZipFile(output, "w") as archive:
            archive.write(root / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
            for path in sorted(root.rglob("*")):
                if path.is_dir() or path.name == "mimetype":
                    continue
                archive.write(path, path.relative_to(root).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
