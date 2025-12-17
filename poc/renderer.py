"""
PDF Renderer for KDP Formatter POC

This module renders IDM documents to PDF using ReportLab (primary) or WeasyPrint (legacy).
ReportLab generates simpler, more KDP-compatible PDFs.
"""

import os
from pathlib import Path
from typing import Optional
from string import Template

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    HTML = None
    CSS = None

try:
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
    from reportlab.lib.units import inch as rl_inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from .idm_schema import IDMDocument, IDMChapter, IDMParagraph, IDMHeading, IDMQuote
except ImportError:
    from idm_schema import IDMDocument, IDMChapter, IDMParagraph, IDMHeading, IDMQuote


class ReportLabPDFRenderer:
    """KDP-compatible PDF renderer using ReportLab (recommended)"""

    # Page sizes in inches
    PAGE_SIZES = {
        '6x9': (6, 9),
        '5x8': (5, 8),
        '5.5x8.5': (5.5, 8.5),
        '8.5x11': (8.5, 11),
    }

    def __init__(self, page_size: str = "6x9", margins: float = 0.75):
        """
        Initialize ReportLab renderer

        Args:
            page_size: Page size ('6x9', '5x8', '5.5x8.5', or '8.5x11')
            margins: Margin size in inches
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF rendering. Install with: pip install reportlab")

        self.page_size = page_size
        self.margins = margins
        self._register_fonts()

    def _register_fonts(self):
        """Register embedded fonts for PDF generation"""
        # Use Source Serif 4 fonts from the project
        fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        serif_regular = os.path.join(fonts_dir, 'SourceSerif4-Regular.ttf')
        serif_bold = os.path.join(fonts_dir, 'SourceSerif4-Semibold.ttf')

        if os.path.exists(serif_regular) and os.path.exists(serif_bold):
            try:
                pdfmetrics.registerFont(TTFont('SourceSerif', serif_regular))
                pdfmetrics.registerFont(TTFont('SourceSerifBold', serif_bold))
                self.font_regular = 'SourceSerif'
                self.font_bold = 'SourceSerifBold'
            except Exception:
                self.font_regular = 'Times-Roman'
                self.font_bold = 'Times-Bold'
        else:
            # Fallback to standard PDF fonts
            self.font_regular = 'Times-Roman'
            self.font_bold = 'Times-Bold'

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text to ASCII-safe characters for maximum KDP compatibility"""
        if not text:
            return ""

        replacements = {
            '\xa0': ' ',      # Non-breaking space
            '\u2018': "'",    # Left single quote
            '\u2019': "'",    # Right single quote
            '\u201c': '"',    # Left double quote
            '\u201d': '"',    # Right double quote
            '\u2013': '-',    # En dash
            '\u2014': '--',   # Em dash
            '\u2026': '...',  # Ellipsis
            '\u2022': '-',    # Bullet
            '\u25CF': '*',    # Black circle
            '\u25CB': 'o',    # White circle
            '\u2192': '->',   # Right arrow
            '\u2190': '<-',   # Left arrow
        }
        for orig, repl in replacements.items():
            text = text.replace(orig, repl)

        # Remove emojis and high unicode (keep Latin-1 range)
        text = ''.join(c for c in text if ord(c) < 256)
        return text

    def render_to_pdf(self, document: IDMDocument, output_path: str):
        """
        Render IDM document to KDP-compatible PDF

        Args:
            document: IDM document to render
            output_path: Path for output PDF file
        """
        # Get page dimensions
        width_in, height_in = self.PAGE_SIZES.get(self.page_size, (6, 9))
        page_width = width_in * rl_inch
        page_height = height_in * rl_inch
        margin = self.margins * rl_inch

        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=(page_width, page_height),
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
            title=self._normalize_text(document.metadata.title or 'Untitled'),
            author=self._normalize_text(document.metadata.author or 'Unknown Author'),
        )

        # Define styles
        title_style = ParagraphStyle(
            'ChapterTitle',
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            spaceBefore=50,
            fontName=self.font_bold,
            leading=22
        )

        body_style = ParagraphStyle(
            'BodyText',
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=0,
            spaceBefore=0,
            fontName=self.font_regular,
            leading=16,
            firstLineIndent=24
        )

        first_para_style = ParagraphStyle(
            'FirstPara',
            parent=body_style,
            firstLineIndent=0
        )

        blockquote_style = ParagraphStyle(
            'BlockQuote',
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=12,
            spaceBefore=12,
            fontName=self.font_regular,
            leading=14,
            leftIndent=36,
            rightIndent=36
        )

        # Build story (content)
        story = []

        for i, chapter in enumerate(document.chapters):
            if i > 0:
                story.append(PageBreak())

            # Chapter title
            title = self._normalize_text(chapter.title or 'Untitled')
            story.append(Paragraph(self._escape_xml(title), title_style))

            # Track first paragraph
            is_first_para = True

            # Get blocks
            blocks = getattr(chapter, 'blocks', None) or getattr(chapter, 'paragraphs', [])

            for block in blocks:
                if isinstance(block, IDMParagraph):
                    text = self._normalize_text(block.text or '')
                    if not text.strip():
                        continue

                    # Skip decorative markers
                    if text.strip() in ['*', '-', 'o', '']:
                        continue

                    escaped_text = self._escape_xml(text)

                    if block.style == 'blockquote':
                        story.append(Paragraph(escaped_text, blockquote_style))
                    elif is_first_para:
                        story.append(Paragraph(escaped_text, first_para_style))
                        is_first_para = False
                    else:
                        story.append(Paragraph(escaped_text, body_style))

                elif isinstance(block, IDMHeading):
                    text = self._normalize_text(block.text or '')
                    if text.strip():
                        story.append(Paragraph(self._escape_xml(text), title_style))
                        is_first_para = True  # Next para has no indent

                elif isinstance(block, IDMQuote):
                    text = self._normalize_text(block.text or '')
                    if text.strip():
                        story.append(Paragraph(self._escape_xml(text), blockquote_style))

        # Build PDF
        doc.build(story)

    @staticmethod
    def _escape_xml(text: str) -> str:
        """Escape XML special characters for ReportLab"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class PDFRenderer:
    """Renderer for converting IDM documents to PDF"""

    def __init__(self, css_path: Optional[str] = None, use_drop_caps: bool = False, page_size: str = "6x9", margins: float = 0.75,
                 use_paragraph_spacing: bool = False, disable_indentation: bool = False):
        """
        Initialize renderer

        Args:
            css_path: Path to CSS stylesheet (defaults to poc/styles.css)
            use_drop_caps: Whether to enable drop caps (disabled by default to avoid formatting issues)
            page_size: Page size ('6x9' or '8.5x11')
            margins: Margin size in inches (applied to all sides)
            use_paragraph_spacing: Whether to add spacing between paragraphs (not traditional KDP)
            disable_indentation: Whether to disable all paragraph indentation (not traditional KDP)
        """
        if HTML is None:
            raise ImportError("weasyprint is required for PDF rendering")

        self.css_path = css_path or os.path.join(
            os.path.dirname(__file__),
            'styles.css'
        )
        self.font_config = FontConfiguration()
        self.use_drop_caps = use_drop_caps
        self.page_size = page_size
        self.margins = margins
        self.use_paragraph_spacing = use_paragraph_spacing
        self.disable_indentation = disable_indentation

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text to improve wrapping and rendering for KDP compatibility."""
        if text is None:
            return ""
        # Replace non-breaking spaces
        text = text.replace('\u00a0', ' ')
        
        # Replace problematic Unicode symbols with ASCII equivalents
        # These characters can trigger fallback fonts (like Hiragino) which KDP may reject
        replacements = {
            '\u25CF': '*',      # BLACK CIRCLE -> asterisk
            '\u25CB': 'o',      # WHITE CIRCLE -> lowercase o
            '\u25E6': '-',      # WHITE BULLET -> hyphen
            '\u25AA': '-',      # BLACK SMALL SQUARE -> hyphen
            '\u25AB': '-',      # WHITE SMALL SQUARE -> hyphen
            '\u2192': '->',     # RIGHTWARDS ARROW -> ASCII arrow
            '\u2190': '<-',     # LEFTWARDS ARROW -> ASCII arrow
            '\u2191': '^',      # UPWARDS ARROW -> caret
            '\u2193': 'v',      # DOWNWARDS ARROW -> v
            '\u2022': '-',      # BULLET -> hyphen
            '\u2026': '...',    # HORIZONTAL ELLIPSIS -> three dots
            '\u2014': '--',     # EM DASH -> double hyphen
            '\u2013': '-',      # EN DASH -> hyphen
            '\u2018': "'",      # LEFT SINGLE QUOTE -> ASCII apostrophe
            '\u2019': "'",      # RIGHT SINGLE QUOTE -> ASCII apostrophe
            '\u201C': '"',      # LEFT DOUBLE QUOTE -> ASCII quote
            '\u201D': '"',      # RIGHT DOUBLE QUOTE -> ASCII quote
        }
        for orig, repl in replacements.items():
            text = text.replace(orig, repl)
        
        # Remove ALL emoji characters to prevent Color Emoji font embedding (KDP rejection)
        import re
        emoji_pattern = re.compile(
            "["
            "\U0001F300-\U0001F9FF"  # Misc Symbols, Emoticons, Dingbats, etc.
            "\U00002702-\U000027B0"  # Dingbats
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F680-\U0001F6FF"  # Transport & Map
            "\U00002600-\U000026FF"  # Misc symbols
            "\U0001FA00-\U0001FAFF"  # Extended symbols
            "\U00002500-\U000025FF"  # Box drawing, block elements
            "\U00002190-\U000021FF"  # Arrows (any we missed)
            "]+", 
            flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)
        return text

    def render_to_pdf(self, document: IDMDocument, output_path: str):
        """
        Render IDM document to PDF (legacy WeasyPrint renderer)

        Args:
            document: IDM document to render
            output_path: Path for output PDF file
        """
        # Generate HTML from IDM
        html_content = self._generate_html(document)

        # Load CSS
        css_content = self._load_css()

        # Create WeasyPrint HTML and CSS objects
        html_doc = HTML(string=html_content)
        css_doc = CSS(string=css_content)

        # Render to PDF
        html_doc.write_pdf(
            output_path,
            stylesheets=[css_doc],
            font_config=self.font_config
        )

    def _generate_html(self, document: IDMDocument) -> str:
        """Generate HTML from IDM document"""
        html_parts = []

        # HTML header
        body_classes = []
        if self.use_paragraph_spacing:
            body_classes.append('use-paragraph-spacing')
        if self.disable_indentation:
            body_classes.append('no-indent')

        body_class_attr = f' class="{" ".join(body_classes)}"' if body_classes else ''
        html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="author" content="{author}">
    <meta name="title" content="{title}">
    <title>{title}</title>
</head>
<body{body_class_attr}>
""".format(
            author=document.metadata.author or "Unknown Author",
            title=document.metadata.title or "Untitled",
            body_class_attr=body_class_attr
        ))

        # Front matter
        if document.front_matter:
            html_parts.append('<div class="front-matter">')
            for para in document.front_matter:
                html_parts.append(self._paragraph_to_html(para, False))  # No indent in front matter
            html_parts.append('</div>')

        # Chapters
        for chapter in document.chapters:
            chapter_class = f'chapter{" use-drop-caps" if self.use_drop_caps else ""}'
            html_parts.append(f'<div class="{chapter_class}">')
            chapter_title = self._normalize_text(getattr(chapter, "title", "") or "")
            html_parts.append(f'<h1 class="chapter-title">{chapter_title}</h1>')

            # Track if previous block was a heading (chapter title counts as heading)
            previous_block_was_heading = True

            # Safe fallback for blocks - preserves compatibility with earlier IDMs
            blocks = getattr(chapter, 'blocks', None)
            if not blocks:
                blocks = getattr(chapter, 'paragraphs', [])

            for block in blocks:
                if isinstance(block, IDMParagraph) and block.style in {"heading1","heading2","heading3"}:
                    # Render as heading and keep heading context
                    html_parts.append(self._paragraph_to_html(block, False))  # Will output <h1/2/3>
                    previous_block_was_heading = True
                elif isinstance(block, IDMParagraph):
                    html_parts.append(self._paragraph_to_html(block, previous_block_was_heading))
                    previous_block_was_heading = False
                    if previous_block_was_heading:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f"First paragraph after heading: {block.text[:50]}...")
                elif isinstance(block, IDMHeading):
                    html_parts.append(self._heading_to_html(block))
                    previous_block_was_heading = True
                elif isinstance(block, IDMQuote):
                    html_parts.append(self._quote_to_html(block))
                    # Do not reset previous_block_was_heading here

            html_parts.append('</div>')

        # Back matter
        if document.back_matter:
            html_parts.append('<div class="back-matter">')
            for para in document.back_matter:
                html_parts.append(self._paragraph_to_html(para, False))  # No indent in back matter
            html_parts.append('</div>')

        # HTML footer
        html_parts.append("""
</body>
</html>""")

        return '\n'.join(html_parts)

    def _paragraph_to_html(self, paragraph: IDMParagraph, is_first_after_heading: bool = False) -> str:
        """Convert IDM paragraph to HTML"""
        normalized_text = self._normalize_text(paragraph.text or "")

        # Normalize decorative markers to a plain bullet to avoid odd glyphs
        marker_map = {
            '●': '',
            '○': '',
            '◦': '',
            '▪': '',
            '▫': '',
            '➤': '',
            '➜': '',
            '✔': '',
            '❖': '',
            '♦': '',
            '❤': '',
            '❤️': '',
            '🖤': '',
        }
        if normalized_text.strip() in marker_map:
            normalized_text = marker_map[normalized_text.strip()]
        if not normalized_text.strip():
            return ''

        # Determine tag based on style
        tag_map = {
            'normal': 'p',
            'blockquote': 'blockquote',
            'greeting': 'p',
            'closing': 'p',
            'signature': 'p',
            'subtitle': 'p'
        }

        tag = tag_map.get(paragraph.style, 'p')

        # Build CSS classes
        classes = []
        if is_first_after_heading:
            classes.append('first-para')
        
        # Add style-specific classes
        if paragraph.style in ('greeting', 'closing', 'signature', 'subtitle', 'emphasis'):
            classes.append(paragraph.style)

        class_attr = f' class="{" ".join(classes)}"' if classes else ''

        # Build style attributes - remove inline text-indent to rely on CSS
        styles = []
        if paragraph.alignment != 'left':
            styles.append(f'text-align: {paragraph.alignment}')
        # Removed inline text-indent - rely on CSS rules instead
        if paragraph.spacing_before > 0:
            styles.append(f'margin-top: {paragraph.spacing_before}pt')
        if paragraph.spacing_after > 0:
            styles.append(f'margin-bottom: {paragraph.spacing_after}pt')

        style_attr = f' style="{"; ".join(styles)}"' if styles else ''

        # Bullet handling: if paragraph contains bullet markers, render as list
        if '•' in normalized_text:
            parts = [p.strip() for p in normalized_text.split('•')]
            preface = parts[0].strip()
            items = [p for p in parts[1:] if p.strip()]

            html_parts = []
            if preface:
                text_preface = preface.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<p{class_attr}{style_attr}>{text_preface}</p>')
            if items:
                html_parts.append('<ul class="bullet-list">')
                for item in items:
                    safe_item = item.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    html_parts.append(f'<li>{safe_item}</li>')
                html_parts.append('</ul>')
            return ''.join(html_parts)

        # Escape HTML entities for normal paragraphs
        text = normalized_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        return f'<{tag}{class_attr}{style_attr}>{text}</{tag}>'

    def _heading_to_html(self, heading: IDMHeading) -> str:
        """Convert IDM heading to HTML"""
        tag = f'h{heading.level}'
        # Escape HTML entities and normalize non-breaking spaces
        text = self._normalize_text(heading.text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<{tag}>{text}</{tag}>'

    def _quote_to_html(self, quote: IDMQuote) -> str:
        """Convert IDM quote to HTML"""
        # Escape HTML entities and normalize non-breaking spaces
        text = self._normalize_text(quote.text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        cite_attr = f' cite="{quote.attribution}"' if quote.attribution else ''
        return f'<blockquote{cite_attr}><p>{text}</p></blockquote>'

    def _load_css(self) -> str:
        """Load CSS content - use CSS file settings directly for KDP compliance"""
        base_css = ""
        if os.path.exists(self.css_path):
            with open(self.css_path, 'r', encoding='utf-8') as f:
                base_css = f.read()

        # Return base CSS only - margins are defined in styles.css for KDP compliance
        # Do NOT add dynamic @page rules as they override the careful margin settings
        return base_css


def render_document_to_pdf(document: IDMDocument, output_path: str, css_path: Optional[str] = None, use_drop_caps: bool = False, page_size: str = "6x9", margins: float = 0.75,
                          use_paragraph_spacing: bool = False, disable_indentation: bool = False, use_reportlab: bool = True):
    """
    Convenience function to render IDM document to PDF

    Args:
        document: IDM document to render
        output_path: Path for output PDF file
        css_path: Optional path to CSS stylesheet
        use_drop_caps: Whether to enable drop caps (disabled by default to avoid formatting issues)
        page_size: Page size ('6x9' or '8.5x11')
        margins: Margin size in inches (applied to all sides)
        use_paragraph_spacing: Whether to add spacing between paragraphs (not traditional KDP)
        disable_indentation: Whether to disable all paragraph indentation (not traditional KDP)
        use_reportlab: Use ReportLab renderer (recommended for KDP compatibility, default True)
    """
    if use_reportlab and REPORTLAB_AVAILABLE:
        renderer = ReportLabPDFRenderer(page_size, margins)
        renderer.render_to_pdf(document, output_path)
    else:
        renderer = PDFRenderer(css_path, use_drop_caps, page_size, margins, use_paragraph_spacing, disable_indentation)
        renderer.render_to_pdf(document, output_path)
