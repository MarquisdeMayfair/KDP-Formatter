"""
EPUB 3 Generator for KDP Formatter POC

This module generates EPUB 3 files from IDM documents with KDP compliance,
including semantic HTML5, nav.xhtml, embedded fonts, and footnote conversion.
"""

import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from xml.dom import minidom
from xml.etree import ElementTree as ET

try:
    from .idm_schema import IDMDocument, IDMChapter, IDMParagraph, IDMHeading, IDMQuote, IDMFootnote
except ImportError:
    from idm_schema import IDMDocument, IDMChapter, IDMParagraph, IDMHeading, IDMQuote, IDMFootnote


class EPUBGenerator:
    """Generator for converting IDM documents to EPUB 3 format"""

    def __init__(self, css_path: Optional[str] = None, fonts_dir: Optional[str] = None):
        """
        Initialize EPUB generator

        Args:
            css_path: Path to EPUB CSS stylesheet (defaults to poc/epub_styles.css)
            fonts_dir: Directory containing font files (defaults to poc/fonts/)
        """
        self.css_path = css_path or os.path.join(
            os.path.dirname(__file__),
            'epub_styles.css'
        )
        self.fonts_dir = fonts_dir or os.path.join(
            os.path.dirname(__file__),
            'fonts'
        )

    def generate_epub(self, document: IDMDocument, output_path: str, use_paragraph_spacing: bool = False, disable_indentation: bool = False) -> None:
        """
        Generate EPUB 3 file from IDM document

        Args:
            document: IDM document to convert
            output_path: Path for output EPUB file
            use_paragraph_spacing: Whether to add spacing between paragraphs (not traditional KDP)
            disable_indentation: Whether to disable all paragraph indentation (not traditional KDP)
        """
        # Store configuration options
        self.use_paragraph_spacing = use_paragraph_spacing
        self.disable_indentation = disable_indentation

        # Validate Pandoc availability
        self._check_pandoc_available()

        # Generate semantic HTML5 content
        html_content = self._generate_html_content(document)

        # Create metadata dictionary for Pandoc
        metadata = self._create_metadata_dict(document)

        # Convert HTML to EPUB using Pandoc
        temp_epub_path = self._convert_with_pandoc(html_content, metadata, output_path)

        # Post-process EPUB for KDP compliance
        self._post_process_epub(temp_epub_path)

        # Clean up temporary file if different from output
        if temp_epub_path != output_path:
            os.rename(temp_epub_path, output_path)

    def _generate_html_content(self, document: IDMDocument) -> str:
        """Generate semantic HTML5 content from IDM document"""
        html_parts = []

        # HTML5 doctype and head
        body_classes = []
        if self.use_paragraph_spacing:
            body_classes.append('use-paragraph-spacing')
        if self.disable_indentation:
            body_classes.append('no-indent')

        body_class_attr = f' class="{" ".join(body_classes)}"' if body_classes else ''
        html_parts.append("""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
    <meta charset="utf-8"/>
    <meta name="generator" content="KDP Formatter"/>
    <title>{title}</title>
</head>
<body{body_class_attr}>
""".format(title=document.metadata.title or "Untitled"))

        # Front matter
        if document.front_matter:
            html_parts.append('<section epub:type="frontmatter">')
            for para in document.front_matter:
                html_parts.append(self._paragraph_to_html(para))
            html_parts.append('</section>')

        # Chapters
        for chapter in document.chapters:
            html_parts.append(f'<section class="chapter" epub:type="chapter">')
            html_parts.append(f'<h1 class="chapter-title">{self._escape_html(chapter.title)}</h1>')

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
                elif isinstance(block, IDMHeading):
                    html_parts.append(self._heading_to_html(block))
                    previous_block_was_heading = True
                elif isinstance(block, IDMQuote):
                    html_parts.append(self._quote_to_html(block))
                    # Do not reset previous_block_was_heading here

            html_parts.append('</section>')

        # Endnotes section (converted from footnotes)
        if any(chapter.footnotes for chapter in document.chapters):
            html_parts.append(self._generate_endnotes_section(document.chapters))

        # Back matter
        if document.back_matter:
            html_parts.append('<section epub:type="backmatter">')
            for para in document.back_matter:
                html_parts.append(self._paragraph_to_html(para))
            html_parts.append('</section>')

        # HTML footer
        html_parts.append("""
</body>
</html>""")

        return '\n'.join(html_parts)

    def _paragraph_to_html(self, paragraph: IDMParagraph, is_first_after_heading: bool = False) -> str:
        """Convert IDM paragraph to HTML"""
        # Determine tag based on style
        tag_map = {
            'normal': 'p',
            'heading1': 'h1',
            'heading2': 'h2',
            'heading3': 'h3',
            'blockquote': 'blockquote'
        }

        tag = tag_map.get(paragraph.style, 'p')

        # Build classes and attributes
        classes = []
        attrs = []

        if is_first_after_heading:
            classes.append('first-para')

        if paragraph.is_quote:
            classes.append('quote')

        # Use local text variable to avoid mutating paragraph.text
        text = paragraph.text
        if paragraph.footnote_refs:
            # Add footnote reference links with IDs for backlinks
            footnote_links = []
            for ref_num in paragraph.footnote_refs:
                footnote_links.append(f'<a id="noteref-{ref_num}" epub:type="noteref" href="#endnote-{ref_num}">[{ref_num}]</a>')
            footnote_refs_html = ''.join(footnote_links)
            # Append footnote references to the text
            text += f' {footnote_refs_html}'

        class_attr = f' class="{" ".join(classes)}"' if classes else ''

        # Escape HTML entities
        escaped_text = self._escape_html(text)

        return f'<{tag}{class_attr}>{escaped_text}</{tag}>'

    def _heading_to_html(self, heading: IDMHeading) -> str:
        """Convert IDM heading to HTML"""
        tag = f'h{heading.level}'
        text = self._escape_html(heading.text)
        return f'<{tag}>{text}</{tag}>'

    def _quote_to_html(self, quote: IDMQuote) -> str:
        """Convert IDM quote to HTML"""
        text = self._escape_html(quote.text)
        cite_attr = f' cite="{self._escape_html(quote.attribution)}"' if quote.attribution else ''
        return f'<blockquote{cite_attr}><p>{text}</p></blockquote>'

    def _generate_endnotes_section(self, chapters: List[IDMChapter]) -> str:
        """Generate endnotes section from chapter footnotes"""
        html_parts = []
        html_parts.append('<section class="endnotes" epub:type="endnotes">')
        html_parts.append('<h1>Notes</h1>')

        footnote_count = 1
        for chapter in chapters:
            for footnote in chapter.footnotes:
                html_parts.append(f'<div class="endnote" id="endnote-{footnote.number}">')
                html_parts.append(f'<p class="endnote-number"><a href="#noteref-{footnote.number}">[{footnote.number}]</a></p>')
                html_parts.append(f'<p class="endnote-text">{self._escape_html(footnote.text)}</p>')
                html_parts.append('</div>')

        html_parts.append('</section>')
        return '\n'.join(html_parts)

    def _create_metadata_dict(self, document: IDMDocument) -> Dict[str, Any]:
        """Create metadata dictionary for Pandoc"""
        metadata = {
            'title': document.metadata.title or "Untitled",
            'author': document.metadata.author or "Unknown Author",
            'language': document.metadata.language or "en",
        }

        if document.metadata.isbn:
            metadata['identifier'] = f'ISBN:{document.metadata.isbn}'

        return metadata

    def _convert_with_pandoc(self, html_content: str, metadata: Dict[str, Any], output_path: str) -> str:
        """Convert HTML to EPUB using Pandoc"""
        # Ensure CSS file exists
        if not os.path.exists(self.css_path):
            raise RuntimeError(f"CSS file not found: {self.css_path}")

        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_html_path = f.name

        # Create temporary EPUB path if needed
        temp_epub_path = output_path
        if not output_path.endswith('.epub'):
            temp_epub_path = output_path.replace('.epub', '_temp.epub')

        try:
            # Build Pandoc command
            cmd = [
                'pandoc',
                temp_html_path,
                '-f', 'html',
                '-t', 'epub3',
                '-o', temp_epub_path,
                '--epub-chapter-level=1',
                '--toc-depth=3',
                '--css', self.css_path,
                '--resource-path', os.path.dirname(self.css_path)
            ]

            # Add metadata
            for key, value in metadata.items():
                cmd.extend(['--metadata', f'{key}={value}'])

            # Run Pandoc
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return temp_epub_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pandoc conversion failed: {e.stderr}")
        finally:
            # Clean up temporary HTML file
            os.unlink(temp_html_path)

    def _post_process_epub(self, epub_path: str) -> None:
        """Post-process EPUB for KDP compliance"""
        # Create temporary directory for EPUB contents
        with tempfile.TemporaryDirectory() as temp_dir:
            # Unzip EPUB
            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                epub_zip.extractall(temp_dir)

            # Enhance OPF metadata
            self._enhance_opf_metadata(temp_dir)

            # Generate nav.xhtml
            self._generate_nav_xhtml(temp_dir)

            # Embed fonts
            self._embed_fonts(temp_dir)

            # Convert footnotes to endnotes with backlinks
            self._convert_footnotes_to_endnotes(temp_dir)

            # Re-zip as EPUB
            self._repackage_epub(temp_dir, epub_path)

    def _enhance_opf_metadata(self, epub_dir: str) -> None:
        """Enhance OPF metadata for KDP compliance"""
        opf_path = self._find_opf_file(epub_dir)
        if not opf_path:
            return

        # Parse OPF file with proper namespaces
        ET.register_namespace('opf', 'http://www.idpf.org/2007/opf')
        ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
        tree = ET.parse(opf_path)
        root = tree.getroot()

        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        # Add Dublin Core metadata if missing
        metadata_elem = root.find('.//opf:metadata', ns)
        if metadata_elem is not None:
            # Add creator if missing
            if metadata_elem.find('.//dc:creator', ns) is None:
                creator = ET.SubElement(metadata_elem, '{http://purl.org/dc/elements/1.1/}creator')
                creator.text = "Unknown Author"

            # Add language if missing
            if metadata_elem.find('.//dc:language', ns) is None:
                language = ET.SubElement(metadata_elem, '{http://purl.org/dc/elements/1.1/}language')
                language.text = "en"

        # Write back enhanced OPF
        tree.write(opf_path, encoding='utf-8', xml_declaration=True)

    def _generate_nav_xhtml(self, epub_dir: str) -> Optional[str]:
        """Generate nav.xhtml table of contents if not already present"""
        # Find OPF file and compute OPF directory
        opf_path = self._find_opf_file(epub_dir)
        if not opf_path:
            return None

        opf_dir = os.path.dirname(opf_path)
        nav_path = os.path.join(opf_dir, 'nav.xhtml')

        # Check if nav.xhtml already exists (generated by Pandoc)
        if os.path.exists(nav_path):
            return nav_path

        # Parse OPF to get spine items with proper namespaces
        ET.register_namespace('opf', 'http://www.idpf.org/2007/opf')
        tree = ET.parse(opf_path)
        root = tree.getroot()

        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        spine_items = []
        spine_elem = root.find('.//opf:spine', ns)
        if spine_elem is not None:
            for itemref in spine_elem:
                idref = itemref.get('idref')
                if idref:
                    spine_items.append(idref)

        # Generate nav.xhtml content
        nav_content = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Table of Contents</title>
</head>
<body>
    <nav epub:type="toc">
        <h1>Table of Contents</h1>
        <ol>
"""

        for item_id in spine_items:
            # Get title from manifest item
            manifest_item = root.find(f'.//opf:item[@id="{item_id}"]', ns)
            if manifest_item is not None:
                href = manifest_item.get('href', '')
                title = href.replace('.xhtml', '').replace('_', ' ').title()
                nav_content += f'            <li><a href="{href}">{title}</a></li>\n'

        nav_content += """        </ol>
    </nav>
</body>
</html>"""

        # Write nav.xhtml
        with open(nav_path, 'w', encoding='utf-8') as f:
            f.write(nav_content)

        # Update OPF manifest to include nav.xhtml
        manifest_elem = root.find('.//opf:manifest', ns)
        if manifest_elem is not None:
            nav_item = ET.SubElement(manifest_elem, '{http://www.idpf.org/2007/opf}item')
            nav_item.set('id', 'nav')
            nav_item.set('href', 'nav.xhtml')
            nav_item.set('media-type', 'application/xhtml+xml')
            nav_item.set('properties', 'nav')

        # Update spine to include nav
        if spine_elem is not None:
            nav_itemref = ET.SubElement(spine_elem, '{http://www.idpf.org/2007/opf}itemref')
            nav_itemref.set('idref', 'nav')
            nav_itemref.set('linear', 'no')

        tree.write(opf_path, encoding='utf-8', xml_declaration=True)

        return nav_path

    def _embed_fonts(self, epub_dir: str) -> None:
        """Embed OFL-licensed fonts in EPUB if not already handled by Pandoc"""
        fonts_to_embed = [
            ('SourceSerif4-Regular.ttf', 'font-regular'),
            ('SourceSerif4-Semibold.ttf', 'font-semibold')
        ]

        # Find OPF file and compute OPF directory
        opf_path = self._find_opf_file(epub_dir)
        if not opf_path:
            return

        opf_dir = os.path.dirname(opf_path)
        fonts_dir = os.path.join(opf_dir, 'fonts')
        os.makedirs(fonts_dir, exist_ok=True)

        # Parse OPF with proper namespaces
        ET.register_namespace('opf', 'http://www.idpf.org/2007/opf')
        tree = ET.parse(opf_path)
        root = tree.getroot()

        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        manifest_elem = root.find('.//opf:manifest', ns)

        if manifest_elem is not None:
            for font_file, font_id in fonts_to_embed:
                font_src_path = os.path.join(self.fonts_dir, font_file)
                if os.path.exists(font_src_path):
                    # Check if font is already in manifest (embedded by Pandoc)
                    existing_font = manifest_elem.find(f'.//opf:item[@href="{font_file}"]', ns)
                    if existing_font is not None:
                        continue  # Already embedded by Pandoc

                    # Copy font to OPF fonts subdirectory
                    font_dest_path = os.path.join(fonts_dir, font_file)
                    with open(font_src_path, 'rb') as src, open(font_dest_path, 'wb') as dest:
                        dest.write(src.read())

                    # Add to manifest with namespaced tag and correct media type
                    font_item = ET.SubElement(manifest_elem, '{http://www.idpf.org/2007/opf}item')
                    font_item.set('id', font_id)
                    font_item.set('href', f'fonts/{font_file}')
                    font_item.set('media-type', 'font/ttf')

        tree.write(opf_path, encoding='utf-8', xml_declaration=True)

    def _convert_footnotes_to_endnotes(self, epub_dir: str) -> None:
        """Convert footnotes to endnotes with backlinks (placeholder - Pandoc handles this)"""
        # Pandoc's epub3 output already handles footnote conversion
        # This method is for any additional post-processing if needed
        pass

    def _repackage_epub(self, epub_dir: str, output_path: str) -> None:
        """Repackage directory contents as EPUB file"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
            # Add mimetype first (must be uncompressed)
            mimetype_path = os.path.join(epub_dir, 'mimetype')
            if os.path.exists(mimetype_path):
                epub_zip.write(mimetype_path, 'mimetype', zipfile.ZIP_STORED)
            else:
                # Create mimetype file
                epub_zip.writestr('mimetype', 'application/epub+zip', zipfile.ZIP_STORED)

            # Add all other files
            for root, dirs, files in os.walk(epub_dir):
                for file in files:
                    if file == 'mimetype':
                        continue  # Already added

                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, epub_dir)
                    epub_zip.write(file_path, arc_path)

    def _find_opf_file(self, epub_dir: str) -> Optional[str]:
        """Find the OPF file in the EPUB directory"""
        for root, dirs, files in os.walk(epub_dir):
            for file in files:
                if file.endswith('.opf'):
                    return os.path.join(root, file)
        return None

    def _check_pandoc_available(self) -> None:
        """Check if Pandoc is available"""
        try:
            result = subprocess.run(['pandoc', '--version'],
                                  capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Pandoc is required for EPUB generation. Install Pandoc first.")

    def _escape_html(self, text: str) -> str:
        """Escape HTML entities in text"""
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#39;'))


def generate_epub(document: IDMDocument, output_path: str, css_path: Optional[str] = None, fonts_dir: Optional[str] = None,
                 use_paragraph_spacing: bool = False, disable_indentation: bool = False) -> None:
    """
    Convenience function to generate EPUB from IDM document

    Args:
        document: IDM document to convert
        output_path: Path for output EPUB file
        css_path: Optional path to EPUB CSS stylesheet
        fonts_dir: Optional directory containing font files
        use_paragraph_spacing: Whether to add spacing between paragraphs (not traditional KDP)
        disable_indentation: Whether to disable all paragraph indentation (not traditional KDP)
    """
    generator = EPUBGenerator(css_path, fonts_dir)
    generator.generate_epub(document, output_path, use_paragraph_spacing, disable_indentation)
