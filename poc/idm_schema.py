"""
IDM Schema Definition for KDP Formatter POC

This module defines the Internal Document Model (IDM) used for processing
manuscripts into KDP-compatible formats.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field


@dataclass
class IDMMetadata:
    """Metadata for the document"""
    title: str = ""
    author: str = ""
    isbn: str = ""
    language: str = "en"
    word_count: int = 0
    page_count_estimate: int = 0
    has_front_matter: bool = False
    has_back_matter: bool = False
    detected_by_ai: bool = False
    ai_cost: float = 0.0


@dataclass
class IDMHeading:
    """Represents a heading in the document"""
    text: str
    level: int  # 1-3 for H1-H3
    style: str = "normal"


@dataclass
class IDMQuote:
    """Represents a quote or blockquote in the document"""
    text: str
    attribution: str = ""
    style: str = "blockquote"


@dataclass
class IDMFootnote:
    """Represents a footnote in the document"""
    number: int
    text: str
    reference_location: str = ""


@dataclass
class IDMParagraph:
    """Represents a paragraph in the document"""
    text: str
    style: str = "normal"  # normal, heading1, heading2, blockquote, etc.
    alignment: str = "left"  # left, center, right, justify
    indent: float = 0.0  # in inches
    spacing_before: float = 0.0  # in points
    spacing_after: float = 0.0  # in points
    footnote_refs: List[int] = field(default_factory=list)
    is_quote: bool = False
    heading_level: Optional[int] = None  # for paragraphs that are actually headings (backward compatibility)


@dataclass
class IDMChapter:
    """Represents a chapter in the document"""
    title: str
    blocks: List[Union[IDMParagraph, IDMHeading, IDMQuote]] = field(default_factory=list)
    number: Optional[int] = None
    footnotes: List[IDMFootnote] = field(default_factory=list)
    start_on_recto: bool = True  # for chapter layout control

    @property
    def paragraphs(self) -> List[IDMParagraph]:
        """Backward compatibility: return only paragraphs from blocks"""
        return [block for block in self.blocks if isinstance(block, IDMParagraph)]


@dataclass
class IDMDocument:
    """Internal Document Model representing a complete manuscript"""
    metadata: IDMMetadata = field(default_factory=IDMMetadata)
    chapters: List[IDMChapter] = field(default_factory=list)
    front_matter: List[IDMParagraph] = field(default_factory=list)
    back_matter: List[IDMParagraph] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        def block_to_dict(block: Union[IDMParagraph, IDMHeading, IDMQuote]) -> Dict[str, Any]:
            """Convert a block to dictionary with type information"""
            if isinstance(block, IDMParagraph):
                return {
                    "type": "paragraph",
                    "text": block.text,
                    "style": block.style,
                    "alignment": block.alignment,
                    "indent": block.indent,
                    "spacing_before": block.spacing_before,
                    "spacing_after": block.spacing_after,
                    "footnote_refs": block.footnote_refs,
                    "is_quote": block.is_quote,
                    "heading_level": block.heading_level
                }
            elif isinstance(block, IDMHeading):
                return {
                    "type": "heading",
                    "text": block.text,
                    "level": block.level,
                    "style": block.style
                }
            elif isinstance(block, IDMQuote):
                return {
                    "type": "quote",
                    "text": block.text,
                    "attribution": block.attribution,
                    "style": block.style
                }
            else:
                raise ValueError(f"Unknown block type: {type(block)}")

        return {
            "metadata": {
                "title": self.metadata.title,
                "author": self.metadata.author,
                "isbn": self.metadata.isbn,
                "language": self.metadata.language,
                "word_count": self.metadata.word_count,
                "page_count_estimate": self.metadata.page_count_estimate,
                "has_front_matter": self.metadata.has_front_matter,
                "has_back_matter": self.metadata.has_back_matter,
                "detected_by_ai": self.metadata.detected_by_ai,
                "ai_cost": self.metadata.ai_cost
            },
            "chapters": [
                {
                    "title": chapter.title,
                    "number": chapter.number,
                    "blocks": [block_to_dict(block) for block in chapter.blocks],
                    "footnotes": [
                        {
                            "number": fn.number,
                            "text": fn.text,
                            "reference_location": fn.reference_location
                        }
                        for fn in chapter.footnotes
                    ],
                    "start_on_recto": chapter.start_on_recto
                }
                for chapter in self.chapters
            ],
            "front_matter": [
                {
                    "text": p.text,
                    "style": p.style,
                    "alignment": p.alignment,
                    "indent": p.indent,
                    "spacing_before": p.spacing_before,
                    "spacing_after": p.spacing_after
                }
                for p in self.front_matter
            ],
            "back_matter": [
                {
                    "text": p.text,
                    "style": p.style,
                    "alignment": p.alignment,
                    "indent": p.indent,
                    "spacing_before": p.spacing_before,
                    "spacing_after": p.spacing_after
                }
                for p in self.back_matter
            ]
        }
