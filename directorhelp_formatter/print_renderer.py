from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from .html import markdown_to_html
from .model import Book


TRIM_SIZES: dict[str, tuple[float, float]] = {
    "5x8": (5.0, 8.0),
    "5.5x8.5": (5.5, 8.5),
    "6x9": (6.0, 9.0),
    "7x10": (7.0, 10.0),
    "8.5x11": (8.5, 11.0),
}


@dataclass(frozen=True)
class PrintConfig:
    trim_size: str = "6x9"
    inside_margin: float = 0.75
    outside_margin: float = 0.58
    top_margin: float = 0.65
    bottom_margin: float = 0.72

    @property
    def dimensions(self) -> tuple[float, float]:
        try:
            return TRIM_SIZES[self.trim_size]
        except KeyError as exc:
            choices = ", ".join(TRIM_SIZES)
            raise ValueError(f"Unsupported trim size '{self.trim_size}'. Choose: {choices}") from exc


class PrintRenderer:
    def __init__(self, config: PrintConfig | None = None) -> None:
        self.config = config or PrintConfig()
        self.package_dir = Path(__file__).resolve().parent
        self.styles_path = self.package_dir / "styles" / "print.css"
        self.fonts_dir = self.package_dir.parent / "poc" / "fonts"

    def render(self, book: Book, output_path: str | Path, html_output: str | Path | None = None) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        html = self._document_html(book)
        css = self._stylesheet()

        if html_output:
            html_path = Path(html_output)
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text(html, encoding="utf-8")

        font_config = FontConfiguration()
        stylesheet = CSS(string=css, base_url=str(self.package_dir.parent), font_config=font_config)
        HTML(string=html, base_url=str(self.package_dir.parent)).write_pdf(
            str(output),
            stylesheets=[stylesheet],
            font_config=font_config,
        )
        return output

    def _stylesheet(self) -> str:
        width, height = self.config.dimensions
        regular = (self.fonts_dir / "SourceSerif4-Regular.ttf").resolve().as_uri()
        semibold = (self.fonts_dir / "SourceSerif4-Semibold.ttf").resolve().as_uri()
        css = self.styles_path.read_text(encoding="utf-8")
        replacements = {
            "__PAGE_WIDTH__": f"{width}in",
            "__PAGE_HEIGHT__": f"{height}in",
            "__INSIDE_MARGIN__": f"{self.config.inside_margin}in",
            "__OUTSIDE_MARGIN__": f"{self.config.outside_margin}in",
            "__TOP_MARGIN__": f"{self.config.top_margin}in",
            "__BOTTOM_MARGIN__": f"{self.config.bottom_margin}in",
            "__CONTENT_HEIGHT__": f"{height - self.config.top_margin - self.config.bottom_margin}in",
            "__FONT_REGULAR__": regular,
            "__FONT_SEMIBOLD__": semibold,
        }
        for key, value in replacements.items():
            css = css.replace(key, value)
        return css

    def _document_html(self, book: Book) -> str:
        meta = book.metadata
        sections: list[str] = [
            "<!doctype html>",
            f'<html lang="{escape(meta.language)}">',
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{escape(meta.title)}</title>",
            f'<meta name="author" content="{escape(meta.author)}">',
            "</head><body>",
            self._title_page(book),
            self._copyright_page(book),
            self._contents(book),
        ]

        if book.introduction_markdown.strip():
            sections.append('<section class="front-section reader-note">')
            sections.append('<p class="section-kicker">Before you begin</p>')
            sections.append(markdown_to_html(book.introduction_markdown, meta.source_url))
            sections.append("</section>")

        for part in book.parts:
            sections.extend([
                '<section class="part-page">',
                f'<p class="part-label">{escape(part.label)}</p>',
                f'<h1>{escape(part.title)}</h1>',
                "</section>",
            ])
            for chapter in part.chapters:
                sections.extend([
                    f'<section class="chapter" id="{escape(chapter.slug)}">',
                    f'<header class="chapter-heading"><p>Chapter {chapter.number}</p><h1>{escape(chapter.title)}</h1></header>',
                    '<div class="chapter-body">',
                    markdown_to_html(chapter.markdown, meta.source_url),
                    "</div></section>",
                ])

        for section in book.back_matter:
            sections.extend([
                f'<section class="back-section" id="{escape(section.slug)}">',
                f'<h1>{escape(section.title)}</h1>',
                markdown_to_html(section.markdown, meta.source_url),
                "</section>",
            ])

        # Paperback interiors must have an even page count. Starting this empty
        # section on a left-hand page adds only the verso needed by the current
        # pagination while keeping the preceding back matter untouched.
        sections.append('<section class="end-page" aria-hidden="true"></section>')
        sections.append("</body></html>")
        return "\n".join(sections)

    @staticmethod
    def _title_page(book: Book) -> str:
        meta = book.metadata
        subtitle = f"<p class=\"book-subtitle\">{escape(meta.subtitle)}</p>" if meta.subtitle else ""
        return "\n".join([
            '<section class="title-page">',
            '<p class="series">The Director\'s Guide To</p>',
            f'<h1>{escape(meta.title)}</h1>',
            subtitle,
            f'<p class="edition">{escape(meta.edition)}</p>',
            '<p class="imprint"><strong>director<span>help</span></strong><br>New Marylebone Press</p>',
            "</section>",
        ])

    @staticmethod
    def _copyright_page(book: Book) -> str:
        meta = book.metadata
        checked = f"Research reviewed on {escape(meta.checked_date)}. " if meta.checked_date else ""
        isbn = f"<p>ISBN: {escape(meta.isbn)}</p>" if meta.isbn else ""
        return "\n".join([
            '<section class="copyright-page">',
            f'<p>Copyright © 2026 {escape(meta.copyright_holder)}.</p>',
            f'<p>Published by {escape(meta.publisher)}.<br>{escape(meta.source_url)}</p>',
            isbn,
            f'<p>{checked}Independent expert verification is pending.</p>',
            '<p>This publication provides general information, not legal, tax, financial or insolvency advice. It is not a personal recommendation. Rules and thresholds change; check the dated live source before acting.</p>',
            '<p>No advertiser has approved, reviewed or altered the editorial content of this edition.</p>',
            "</section>",
        ])

    @staticmethod
    def _contents(book: Book) -> str:
        rows: list[str] = ['<section class="contents"><h1>Contents</h1>']
        for part in book.parts:
            rows.append(f'<h2>{escape(part.label)}: {escape(part.title)}</h2><ol>')
            for chapter in part.chapters:
                rows.append(f'<li><span>{chapter.number}</span> {escape(chapter.title)}</li>')
            rows.append("</ol>")
        if book.back_matter:
            rows.append('<h2>Reference</h2><ul>')
            rows.extend(f'<li>{escape(section.title)}</li>' for section in book.back_matter)
            rows.append("</ul>")
        rows.append("</section>")
        return "\n".join(rows)
