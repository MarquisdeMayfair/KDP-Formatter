"""
Converters for various document formats to IDM (Internal Document Model)

This module provides converters for:
- .txt files (plain text)
- .pdf files (using pdfminer.six)
- .docx and .md files (using Pandoc -> HTML -> BeautifulSoup)
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, List
from abc import ABC, abstractmethod
import re

try:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
except ImportError:
    extract_text = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from .idm_schema import IDMDocument, IDMChapter, IDMParagraph, IDMMetadata, IDMHeading, IDMQuote, IDMFootnote
except ImportError:
    from idm_schema import IDMDocument, IDMChapter, IDMParagraph, IDMMetadata, IDMHeading, IDMQuote, IDMFootnote

try:
    from .ai_structure_detector import detect_document_structure
except ImportError:
    try:
        from ai_structure_detector import detect_document_structure
    except ImportError:
        detect_document_structure = None


class BaseConverter(ABC):
    """Abstract base class for document converters"""

    @abstractmethod
    def convert(self, input_path: str) -> IDMDocument:
        """Convert input file to IDM document"""
        pass

    @abstractmethod
    def convert_with_ai(self, input_path: str, ai_model: str | None = None) -> IDMDocument:
        """Convert input file to IDM document using AI structure detection"""
        pass

    def _map_ai_structure_to_idm(self, detection_result: dict, metadata: IDMMetadata) -> IDMDocument:
        """Map AI-detected structure to IDM objects"""
        structured_blocks = detection_result.get("structured_blocks", [])
        cost_summary = detection_result.get("cost_summary", {})

        # Update metadata with AI detection info
        metadata.detected_by_ai = True
        metadata.ai_cost = cost_summary.get("total_cost", 0.0)

        chapters = []
        front_matter = []
        back_matter = []
        current_chapter = None
        current_blocks = []

        for block in structured_blocks:
            block_type = block.get("type", "paragraph")
            text = block.get("text", "").strip()

            if not text:
                continue

            if block_type == "front_matter":
                front_matter.append(IDMParagraph(text=text, style="normal"))
                metadata.has_front_matter = True
            elif block_type == "back_matter":
                back_matter.append(IDMParagraph(text=text, style="normal"))
                metadata.has_back_matter = True
            elif block_type == "chapter":
                # Save previous chapter if exists
                if current_chapter and current_blocks:
                    current_chapter.blocks = current_blocks
                    chapters.append(current_chapter)

                # Start new chapter
                current_chapter = IDMChapter(
                    title=text,
                    blocks=[],
                    number=len(chapters) + 1
                )
                current_blocks = []
            elif block_type == "heading":
                level = block.get("level", 1)
                if level == 1 and not current_chapter:
                    # H1 without chapter - treat as chapter title
                    current_chapter = IDMChapter(
                        title=text,
                        blocks=[],
                        number=len(chapters) + 1
                    )
                    current_blocks = []
                else:
                    # Add as heading block
                    heading = IDMHeading(text=text, level=level)
                    current_blocks.append(heading)
            elif block_type == "quote":
                attribution = block.get("metadata", {}).get("attribution", "")
                quote = IDMQuote(text=text, attribution=attribution)
                current_blocks.append(quote)
            elif block_type == "footnote":
                # Parse footnote number from metadata or reference
                footnote_metadata = block.get("metadata", {})
                footnote_number = footnote_metadata.get("number", 1)
                if isinstance(footnote_number, str):
                    # Try to extract number from string like "[1]" or "¹"
                    number_match = re.search(r'\d+', footnote_number)
                    footnote_number = int(number_match.group()) if number_match else 1

                footnote = IDMFootnote(
                    number=footnote_number,
                    text=text,
                    reference_location=footnote_metadata.get("reference_location", "")
                )
                if current_chapter:
                    current_chapter.footnotes.append(footnote)
            elif block_type == "image":
                # Create paragraph with image style, preserving caption and metadata
                image_metadata = block.get("metadata", {})
                caption = image_metadata.get("caption", "")
                full_bleed = image_metadata.get("full_bleed", False)

                # Combine image description with caption if present
                image_text = text
                if caption:
                    image_text = f"{text}\n{caption}"

                paragraph = IDMParagraph(text=image_text, style="image")
                # Store additional metadata in the paragraph object if needed
                current_blocks.append(paragraph)
            else:  # paragraph or unknown
                style = block.get("style", "normal")
                if style == "blockquote":
                    paragraph = IDMParagraph(text=text, style=style, is_quote=True)
                else:
                    paragraph = IDMParagraph(text=text, style=style)
                current_blocks.append(paragraph)

        # Add final chapter
        if current_chapter and current_blocks:
            current_chapter.blocks = current_blocks
            chapters.append(current_chapter)

        # If no chapters found, create one with all blocks
        if not chapters and current_blocks:
            chapters = [IDMChapter(title="Main Content", blocks=current_blocks)]

        return IDMDocument(
            metadata=metadata,
            chapters=chapters,
            front_matter=front_matter,
            back_matter=back_matter
        )


class TextConverter(BaseConverter):
    """Converter for plain text files"""

    def convert(self, input_path: str) -> IDMDocument:
        """Convert text file to IDM document"""
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create metadata
        metadata = IDMMetadata()
        filename = Path(input_path).stem
        metadata.title = filename.replace('_', ' ').title()
        metadata.word_count = len(content.split())

        # Split into chapters (basic heuristic: look for CHAPTER or numbered sections)
        chapters = []
        lines = content.split('\n')

        current_chapter = None
        current_paragraphs = []

        # Buffer for accumulating consecutive non-empty lines
        paragraph_buffer = []

        for line in lines:
            stripped_line = line.strip()

            # Check if this is a chapter header
            # Recognized patterns: "Chapter 1", "Letter 1", "Part 1", "Section A", "1.", "I.", etc.
            if stripped_line and (re.match(r'^(chapter|letter|part|section)\s+(\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten|[a-z])', stripped_line.lower()) or re.match(r'^(\d+|[ivxlcdm]+)\.(\s+\S.{0,40})?$', stripped_line.lower())):
                # Flush any buffered paragraph first
                if paragraph_buffer:
                    combined_text = self._join_lines_with_hyphenation(paragraph_buffer)
                    current_paragraphs.append(IDMParagraph(text=combined_text))
                    paragraph_buffer = []

                # Save previous chapter if exists
                if current_chapter and current_paragraphs:
                    current_chapter.blocks = current_paragraphs
                    chapters.append(current_chapter)

                # Start new chapter
                current_chapter = IDMChapter(
                    title=stripped_line,
                    number=len(chapters) + 1 if stripped_line.lower().startswith('chapter') else None
                )
                current_paragraphs = []
            elif stripped_line:
                # Add non-empty line to buffer
                paragraph_buffer.append(line.rstrip())  # Keep original trailing spaces for potential hyphenation
            else:
                # Empty line - flush buffered paragraph
                if paragraph_buffer:
                    combined_text = self._join_lines_with_hyphenation(paragraph_buffer)
                    current_paragraphs.append(IDMParagraph(text=combined_text))
                    paragraph_buffer = []

        # Flush final buffered paragraph
        if paragraph_buffer:
            combined_text = self._join_lines_with_hyphenation(paragraph_buffer)
            current_paragraphs.append(IDMParagraph(text=combined_text))

        # Add final chapter
        if current_chapter and current_paragraphs:
            current_chapter.blocks = current_paragraphs
            chapters.append(current_chapter)

        # If no chapters found, create one chapter with all content
        if not chapters:
            # Process lines into paragraphs using the same buffering logic
            paragraphs = []
            paragraph_buffer = []

            for line in lines:
                stripped_line = line.strip()
                if stripped_line:
                    paragraph_buffer.append(line.rstrip())
                else:
                    if paragraph_buffer:
                        combined_text = self._join_lines_with_hyphenation(paragraph_buffer)
                        paragraphs.append(IDMParagraph(text=combined_text))
                        paragraph_buffer = []

            # Flush final buffered paragraph
            if paragraph_buffer:
                combined_text = self._join_lines_with_hyphenation(paragraph_buffer)
                paragraphs.append(IDMParagraph(text=combined_text))

            chapters = [IDMChapter(title="Main Content", blocks=paragraphs)]

        return IDMDocument(metadata=metadata, chapters=chapters)

    def _join_lines_with_hyphenation(self, lines: List[str]) -> str:
        """Join lines with proper hyphenation handling"""
        if not lines:
            return ""

        result = lines[0]

        for line in lines[1:]:
            # Check if previous line ends with hyphen (indicating word continuation)
            if result.endswith('-'):
                # Remove the hyphen and join directly
                result = result[:-1] + line.lstrip()
            else:
                # Join with space
                result += ' ' + line.lstrip()

        return result

    def convert_with_ai(self, input_path: str, ai_model: str | None = None) -> IDMDocument:
        """Convert text file to IDM document using AI structure detection"""
        if detect_document_structure is None:
            raise ImportError("AI structure detection not available. Install openai package.")

        # Read full text content
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Create basic metadata
        metadata = IDMMetadata()
        filename = Path(input_path).stem
        metadata.title = filename.replace('_', ' ').title()
        metadata.word_count = len(text.split())

        # Detect structure using AI
        detection_result = detect_document_structure(text, {"source": "text_file"}, model=ai_model)

        # Map AI-detected structure to IDM objects
        document = self._map_ai_structure_to_idm(detection_result, metadata)

        return document


class PDFConverter(BaseConverter):
    """Converter for PDF files using pdfminer.six"""

    def convert(self, input_path: str) -> IDMDocument:
        """Convert PDF file to IDM document"""
        if extract_text is None:
            raise ImportError("pdfminer.six is required for PDF conversion")

        # Extract text from PDF
        laparams = LAParams()
        text = extract_text(input_path, laparams=laparams)

        # Create metadata
        metadata = IDMMetadata()
        filename = Path(input_path).stem
        metadata.title = filename.replace('_', ' ').title()
        metadata.word_count = len(text.split())

        # Split into paragraphs (basic approach)
        paragraphs = []
        lines = text.split('\n')

        current_paragraph = []
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    paragraphs.append(IDMParagraph(text=' '.join(current_paragraph)))
                    current_paragraph = []
            else:
                current_paragraph.append(line)

        # Add final paragraph
        if current_paragraph:
            paragraphs.append(IDMParagraph(text=' '.join(current_paragraph)))

        # Create single chapter
        chapter = IDMChapter(title="PDF Content", blocks=paragraphs)

        return IDMDocument(metadata=metadata, chapters=[chapter])

    def convert_with_ai(self, input_path: str, ai_model: str | None = None) -> IDMDocument:
        """Convert PDF file to IDM document using AI structure detection"""
        if detect_document_structure is None:
            raise ImportError("AI structure detection not available. Install openai package.")

        if extract_text is None:
            raise ImportError("pdfminer.six is required for PDF conversion")

        # Extract text from PDF
        laparams = LAParams()
        text = extract_text(input_path, laparams=laparams)

        # Create basic metadata
        metadata = IDMMetadata()
        filename = Path(input_path).stem
        metadata.title = filename.replace('_', ' ').title()
        metadata.word_count = len(text.split())

        # Detect structure using AI
        detection_result = detect_document_structure(text, {"source": "pdf_file"}, model=ai_model)

        # Map AI-detected structure to IDM objects
        document = self._map_ai_structure_to_idm(detection_result, metadata)

        return document


class PandocConverter(BaseConverter):
    """Converter for DOCX and Markdown files using Pandoc"""

    def convert(self, input_path: str) -> IDMDocument:
        """Convert DOCX/MD file to IDM document using Pandoc"""
        if BeautifulSoup is None:
            raise ImportError("beautifulsoup4 is required for Pandoc conversion")

        # Convert to HTML using Pandoc
        try:
            result = subprocess.run(
                ['pandoc', input_path, '-t', 'html'],
                capture_output=True,
                text=True,
                check=True
            )
            html_content = result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Pandoc is required for DOCX/MD conversion")

        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract text for word count
        text = soup.get_text()

        # Create metadata
        metadata = IDMMetadata()
        filename = Path(input_path).stem
        metadata.title = filename.replace('_', ' ').title()
        metadata.word_count = len(text.split())

        # Extract content
        chapters = []
        current_chapter = None
        current_paragraphs = []

        for element in soup.find_all(['h1', 'h2', 'h3', 'p']):
            if element.name in ['h1', 'h2', 'h3']:
                # Save previous chapter
                if current_chapter and current_paragraphs:
                    current_chapter.blocks = current_paragraphs
                    chapters.append(current_chapter)

                # Start new chapter
                current_chapter = IDMChapter(
                    title=element.get_text().strip(),
                    number=None
                )
                current_paragraphs = []
            elif element.name == 'p':
                text = element.get_text().strip()
                if text:
                    style = "normal"
                    if element.find_parent('blockquote'):
                        style = "blockquote"
                    current_paragraphs.append(IDMParagraph(text=text, style=style))

        # Add final chapter
        if current_chapter and current_paragraphs:
            current_chapter.blocks = current_paragraphs
            chapters.append(current_chapter)

        # If no chapters found, create one chapter
        if not chapters:
            paragraphs = []
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if text:
                    paragraphs.append(IDMParagraph(text=text))
            chapters = [IDMChapter(title="Document Content", blocks=paragraphs)]

        return IDMDocument(metadata=metadata, chapters=chapters)

    def convert_with_ai(self, input_path: str, ai_model: str | None = None) -> IDMDocument:
        """Convert DOCX/MD file to IDM document using AI structure detection"""
        if detect_document_structure is None:
            raise ImportError("AI structure detection not available. Install openai package.")

        if BeautifulSoup is None:
            raise ImportError("beautifulsoup4 is required for Pandoc conversion")

        # Convert to HTML using Pandoc
        try:
            result = subprocess.run(
                ['pandoc', input_path, '-t', 'html'],
                capture_output=True,
                text=True,
                check=True
            )
            html_content = result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Pandoc is required for DOCX/MD conversion")

        # Parse HTML and extract plain text
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()

        # Create basic metadata
        metadata = IDMMetadata()
        filename = Path(input_path).stem
        metadata.title = filename.replace('_', ' ').title()
        metadata.word_count = len(text.split())

        # Detect structure using AI
        detection_result = detect_document_structure(text, {"source": "pandoc_file"}, model=ai_model)

        # Map AI-detected structure to IDM objects
        document = self._map_ai_structure_to_idm(detection_result, metadata)

        return document


def convert(input_path: str, use_ai: bool = False, ai_model: str | None = None) -> IDMDocument:
    """
    Factory function to convert any supported file format to IDM document

    Args:
        input_path: Path to input file (.txt, .pdf, .docx, .md)
        use_ai: Whether to use AI-powered structure detection
        ai_model: OpenAI model to use for AI detection (default: gpt-4-turbo-preview)

    Returns:
        IDMDocument instance

    Raises:
        ValueError: If file format is not supported
        ImportError: If required dependencies are missing
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Check for OpenAI API key if using AI
    if use_ai and not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable required for AI detection")

    file_ext = Path(input_path).suffix.lower()

    if file_ext == '.txt':
        converter = TextConverter()
    elif file_ext == '.pdf':
        converter = PDFConverter()
    elif file_ext in ['.docx', '.md']:
        converter = PandocConverter()
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

    if use_ai:
        print(f"Using AI-powered structure detection for {input_path}")
        return converter.convert_with_ai(input_path, ai_model)
    else:
        print(f"Using regex-based structure detection for {input_path}")
        return converter.convert(input_path)


def compare_detection_methods(input_path: str) -> dict:
    """
    Compare regex vs AI detection methods for the same file

    Args:
        input_path: Path to input file to compare

    Returns:
        Dictionary with comparison results
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    results = {
        "file": input_path,
        "regex": {},
        "ai": {},
        "comparison": {}
    }

    try:
        # Run regex detection
        print("Running regex detection...")
        regex_doc = convert(input_path, use_ai=False)
        results["regex"] = {
            "chapters_detected": len(regex_doc.chapters),
            "paragraphs_detected": sum(len(chapter.paragraphs) for chapter in regex_doc.chapters),
            "word_count": regex_doc.metadata.word_count,
            "cost": 0.0
        }
    except Exception as e:
        results["regex"]["error"] = str(e)

    try:
        # Run AI detection
        print("Running AI detection...")
        ai_doc = convert(input_path, use_ai=True)
        results["ai"] = {
            "chapters_detected": len(ai_doc.chapters),
            "blocks_detected": sum(len(chapter.blocks) for chapter in ai_doc.chapters),
            "word_count": ai_doc.metadata.word_count,
            "cost": ai_doc.metadata.ai_cost,
            "has_front_matter": ai_doc.metadata.has_front_matter,
            "has_back_matter": ai_doc.metadata.has_back_matter
        }
    except Exception as e:
        results["ai"]["error"] = str(e)

    # Calculate differences
    if "error" not in results["regex"] and "error" not in results["ai"]:
        results["comparison"] = {
            "chapter_difference": results["ai"]["chapters_detected"] - results["regex"]["chapters_detected"],
            "cost_difference": results["ai"]["cost"] - results["regex"]["cost"],
            "ai_improved_chapter_detection": results["ai"]["chapters_detected"] > results["regex"]["chapters_detected"]
        }

    return results
