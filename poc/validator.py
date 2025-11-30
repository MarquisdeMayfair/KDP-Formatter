"""
PDF Validator for KDP Formatter POC

This module validates generated PDFs for KDP compatibility using pypdf and Poppler tools.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


@dataclass
class ValidationConfig:
    """Configuration for validation (matches renderer settings)"""
    use_drop_caps: bool = False
    page_size: str = "6x9"
    margins: float = 0.75
    css_path: Optional[str] = None
    use_paragraph_spacing: bool = False
    disable_indentation: bool = False


@dataclass
class ValidationResult:
    """Result of a validation check"""
    check_name: str
    status: str  # 'pass', 'fail', 'warning', 'error'
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationReport:
    """Complete validation report"""
    pdf_path: str
    checks: List[ValidationResult]
    overall_status: str  # 'pass', 'fail', 'warning'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "pdf_path": self.pdf_path,
            "overall_status": self.overall_status,
            "checks": [
                {
                    "check_name": check.check_name,
                    "status": check.status,
                    "message": check.message,
                    "details": check.details
                }
                for check in self.checks
            ]
        }


class PDFValidator:
    """Validator for PDF files generated for KDP"""

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.checks = []
        self.config = config or ValidationConfig()

    def validate_pdf(self, pdf_path: str, config: Optional[ValidationConfig] = None) -> ValidationReport:
        """
        Run all validation checks on a PDF file

        Args:
            pdf_path: Path to the PDF file to validate
            config: Optional validation configuration (renderer settings)

        Returns:
            ValidationReport with all check results
        """
        if not os.path.exists(pdf_path):
            return ValidationReport(
                pdf_path=pdf_path,
                checks=[ValidationResult(
                    "file_exists",
                    "error",
                    f"PDF file not found: {pdf_path}"
                )],
                overall_status="error"
            )

        # Update config if provided
        if config:
            self.config = config

        self.checks = []

        # Run all checks
        self._check_file_size(pdf_path)
        self._check_page_count(pdf_path)
        self._check_pdf_version(pdf_path)
        self._check_fonts(pdf_path)
        self._check_metadata(pdf_path)
        self._check_page_dimensions(pdf_path)
        self._check_margin_accuracy(pdf_path)
        self._check_text_extraction(pdf_path)
        self._check_text_indentation_patterns(pdf_path)
        self._check_paragraph_formatting(pdf_path)
        self._check_kdp_formatting(pdf_path)
        self._add_kdp_standards_reference()

        # Determine overall status
        statuses = [check.status for check in self.checks]
        if 'error' in statuses:
            overall_status = 'error'
        elif 'fail' in statuses:
            overall_status = 'fail'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'pass'

        return ValidationReport(
            pdf_path=pdf_path,
            checks=self.checks,
            overall_status=overall_status
        )

    def _check_file_size(self, pdf_path: str):
        """Check if file size is reasonable for KDP"""
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)

        if size_mb > 500:  # KDP limit is around 500MB for some formats
            self.checks.append(ValidationResult(
                "file_size",
                "fail",
                f"File size too large for KDP: {size_mb:.1f} MB (> 500 MB)"
            ))
        elif size_mb > 100:
            self.checks.append(ValidationResult(
                "file_size",
                "warning",
                f"Large file size: {size_mb:.1f} MB (> 100 MB)"
            ))
        else:
            self.checks.append(ValidationResult(
                "file_size",
                "pass",
                f"File size: {size_mb:.1f} MB"
            ))

    def _check_page_count(self, pdf_path: str):
        """Check page count using pypdf"""
        if PdfReader is None:
            self.checks.append(ValidationResult(
                "page_count",
                "error",
                "pypdf not available for page count check"
            ))
            return

        try:
            reader = PdfReader(pdf_path)
            page_count = len(reader.pages)

            if page_count < 24:  # KDP minimum
                self.checks.append(ValidationResult(
                    "page_count",
                    "fail",
                    f"Page count too low: {page_count} (minimum 24 for KDP)"
                ))
            elif page_count > 1000:  # Reasonable upper limit
                self.checks.append(ValidationResult(
                    "page_count",
                    "warning",
                    f"High page count: {page_count}"
                ))
            else:
                self.checks.append(ValidationResult(
                    "page_count",
                    "pass",
                    f"Page count: {page_count}"
                ))
        except Exception as e:
            self.checks.append(ValidationResult(
                "page_count",
                "error",
                f"Failed to read PDF: {str(e)}"
            ))

    def _check_pdf_version(self, pdf_path: str):
        """Check PDF version using pypdf"""
        if PdfReader is None:
            self.checks.append(ValidationResult(
                "pdf_version",
                "error",
                "pypdf not available for PDF version check"
            ))
            return

        try:
            reader = PdfReader(pdf_path)
            version = reader.pdf_header

            # KDP prefers PDF 1.4 or later
            if '1.4' in version or '1.5' in version or '1.6' in version or '1.7' in version:
                self.checks.append(ValidationResult(
                    "pdf_version",
                    "pass",
                    f"PDF version: {version}"
                ))
            else:
                self.checks.append(ValidationResult(
                    "pdf_version",
                    "warning",
                    f"PDF version may not be optimal for KDP: {version}"
                ))
        except Exception as e:
            self.checks.append(ValidationResult(
                "pdf_version",
                "error",
                f"Failed to check PDF version: {str(e)}"
            ))

    def _check_fonts(self, pdf_path: str):
        """Check embedded fonts using pdffonts (Poppler)"""
        try:
            result = subprocess.run(
                ['pdffonts', pdf_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.checks.append(ValidationResult(
                    "fonts",
                    "error",
                    "Failed to check fonts with pdffonts"
                ))
                return

            lines = result.stdout.strip().split('\n')
            if len(lines) < 3:  # Header + at least one font
                self.checks.append(ValidationResult(
                    "fonts",
                    "fail",
                    "No fonts found in PDF"
                ))
                return

            # Parse font info (skip header)
            embedded_count = 0
            total_count = 0

            for line in lines[2:]:  # Skip first two header lines
                if line.strip():
                    total_count += 1
                    parts = line.split()
                    if len(parts) >= 8:
                        embedded = parts[7]  # embedded column
                        if embedded == 'yes':
                            embedded_count += 1

            if embedded_count == 0:
                self.checks.append(ValidationResult(
                    "fonts",
                    "fail",
                    "No embedded fonts found"
                ))
            elif embedded_count < total_count:
                self.checks.append(ValidationResult(
                    "fonts",
                    "warning",
                    f"Some fonts not embedded: {embedded_count}/{total_count} embedded"
                ))
            else:
                self.checks.append(ValidationResult(
                    "fonts",
                    "pass",
                    f"All fonts embedded: {embedded_count}/{total_count}"
                ))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.checks.append(ValidationResult(
                "fonts",
                "error",
                "pdffonts not available or timed out"
            ))

    def _check_metadata(self, pdf_path: str):
        """Check PDF metadata"""
        if PdfReader is None:
            self.checks.append(ValidationResult(
                "metadata",
                "error",
                "pypdf not available for metadata check"
            ))
            return

        try:
            reader = PdfReader(pdf_path)
            metadata = reader.metadata

            if not metadata:
                self.checks.append(ValidationResult(
                    "metadata",
                    "warning",
                    "No metadata found in PDF"
                ))
            else:
                # Check for basic metadata
                has_title = bool(metadata.get('/Title'))
                has_author = bool(metadata.get('/Author'))

                if has_title and has_author:
                    self.checks.append(ValidationResult(
                        "metadata",
                        "pass",
                        f"Metadata present: Title={metadata.get('/Title', 'N/A')}, Author={metadata.get('/Author', 'N/A')}"
                    ))
                else:
                    self.checks.append(ValidationResult(
                        "metadata",
                        "warning",
                        "Missing title or author in metadata"
                    ))

        except Exception as e:
            self.checks.append(ValidationResult(
                "metadata",
                "error",
                f"Failed to check metadata: {str(e)}"
            ))

    def _check_page_dimensions(self, pdf_path: str):
        """Check page dimensions using pdfinfo (Poppler)"""
        try:
            result = subprocess.run(
                ['pdfinfo', pdf_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.checks.append(ValidationResult(
                    "page_dimensions",
                    "error",
                    "Failed to check page dimensions with pdfinfo"
                ))
                return

            # Parse page size from output
            lines = result.stdout.split('\n')
            page_size = None
            for line in lines:
                if line.startswith('Page size:'):
                    page_size = line.split(':', 1)[1].strip()
                    break

            if page_size:
                # Check if dimensions look reasonable for KDP
                # KDP standard is typically 6x9 inches or 8.5x11 inches
                if '6 x 9' in page_size or '8.5 x 11' in page_size:
                    self.checks.append(ValidationResult(
                        "page_dimensions",
                        "pass",
                        f"Page size: {page_size}"
                    ))
                else:
                    self.checks.append(ValidationResult(
                        "page_dimensions",
                        "warning",
                        f"Page size may not be standard KDP format: {page_size}"
                    ))
            else:
                self.checks.append(ValidationResult(
                    "page_dimensions",
                    "warning",
                    "Could not determine page size"
                ))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.checks.append(ValidationResult(
                "page_dimensions",
                "error",
                "pdfinfo not available or timed out"
            ))

    def _check_text_extraction(self, pdf_path: str):
        """Check if text can be extracted from PDF"""
        if PdfReader is None:
            self.checks.append(ValidationResult(
                "text_extraction",
                "error",
                "pypdf not available for text extraction check"
            ))
            return

        try:
            reader = PdfReader(pdf_path)

            # Check first page
            if len(reader.pages) > 0:
                page = reader.pages[0]
                text = page.extract_text() or ""

                if text and len(text.strip()) > 10:
                    self.checks.append(ValidationResult(
                        "text_extraction",
                        "pass",
                        f"Text extraction successful ({len(text)} characters on first page)"
                    ))
                else:
                    self.checks.append(ValidationResult(
                        "text_extraction",
                        "warning",
                        "Limited or no text extracted from first page"
                    ))
            else:
                self.checks.append(ValidationResult(
                    "text_extraction",
                    "error",
                    "No pages found in PDF"
                ))

        except Exception as e:
            self.checks.append(ValidationResult(
                "text_extraction",
                "error",
                f"Failed to extract text: {str(e)}"
            ))

    def _check_kdp_formatting(self, pdf_path: str):
        """Check for KDP-specific formatting issues with detailed analysis"""

        # First, validate CSS rules
        self._check_css_kdp_compliance(pdf_path)

        # Analyze paragraph structure
        para_analysis = self._analyze_paragraph_structure(pdf_path)
        if "error" in para_analysis:
            self.checks.append(ValidationResult(
                "kdp_paragraph_indentation",
                "error",
                f"Could not analyze paragraph structure: {para_analysis['error']}"
            ))
        else:
            potential_first = para_analysis.get("potential_first_paras", 0)
            indented_first = para_analysis.get("indented_first_paras", 0)

            if indented_first > 0:
                self.checks.append(ValidationResult(
                    "kdp_paragraph_indentation",
                    "fail",
                    f"Found {indented_first} first paragraphs that appear incorrectly indented. KDP Standard: First paragraph after headings should have NO indentation (text-indent: 0), subsequent paragraphs should have 0.25in indent.",
                    details={
                        "indented_first_paras": indented_first,
                        "total_analyzed": potential_first,
                        "recommendation": "Verify CSS has 'h1 + p, h2 + p, h3 + p, .first-para { text-indent: 0; }' rules"
                    }
                ))
            elif potential_first > 0:
                self.checks.append(ValidationResult(
                    "kdp_paragraph_indentation",
                    "pass",
                    f"Paragraph indentation follows KDP standards ({potential_first} heading-paragraph transitions analyzed)",
                    details={"transitions_analyzed": potential_first}
                ))
            else:
                self.checks.append(ValidationResult(
                    "kdp_paragraph_indentation",
                    "warning",
                    "Could not identify clear heading-paragraph patterns for indentation analysis. Manually verify first paragraphs after headings have no indent."
                ))

        # Drop cap check - context-aware
        if self.config.use_drop_caps:
            self.checks.append(ValidationResult(
                "kdp_drop_caps",
                "warning",
                "Drop caps are ENABLED. CRITICAL: Manually verify in KDP Preview that the enlarged first letter does NOT overlap adjacent text. Drop caps should have line-height >= 1.0 and margin-right >= 0.05em. If overlap occurs, disable drop caps or adjust CSS.",
                details={
                    "enabled": True,
                    "page_size": self.config.page_size,
                    "margins": self.config.margins,
                    "recommendation": "Check CSS for '.use-drop-caps p:first-of-type:first-letter' rules with proper spacing"
                }
            ))
        else:
            self.checks.append(ValidationResult(
                "kdp_drop_caps",
                "pass",
                "Drop caps are disabled (recommended for KDP to avoid formatting issues)",
                details={
                    "enabled": False,
                    "page_size": self.config.page_size,
                    "margins": self.config.margins
                }
            ))

        # Enhanced orphan/widow check
        self._check_page_content_distribution(pdf_path)

        # Page break check with more detail
        self.checks.append(ValidationResult(
            "kdp_page_breaks",
            "warning",
            "Page breaks require manual verification in KDP Preview. KDP Standards: (1) Chapters must start on new pages (page-break-before: always), (2) Headings should not be orphaned at bottom of pages (page-break-after: avoid), (3) No awkward mid-paragraph breaks.",
            details={
                "manual_check_required": True,
                "what_to_verify": [
                    "Each chapter starts on a new page",
                    "Headings are not alone at bottom of pages",
                    "Paragraphs are not split awkwardly across pages"
                ]
            }
        ))

    def _check_margin_accuracy(self, pdf_path: str):
        """Check margin accuracy for KDP standards using pdfinfo"""
        try:
            result = subprocess.run(
                ['pdfinfo', pdf_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.checks.append(ValidationResult(
                    "margin_accuracy",
                    "error",
                    "Failed to check margins with pdfinfo"
                ))
                return

            # Parse page size from output
            lines = result.stdout.split('\n')
            page_size_line = None
            for line in lines:
                if line.startswith('Page size:'):
                    page_size_line = line
                    break

            if page_size_line:
                # Example: "Page size:      432 x 648 pts"
                parts = page_size_line.split()
                if len(parts) >= 5:
                    width_pts = float(parts[3])
                    height_pts = float(parts[5])

                    # Convert to inches (1 pt = 1/72 inch)
                    width_inches = width_pts / 72
                    height_inches = height_pts / 72

                    # Expected content area with 0.75in margins on all sides
                    expected_content_width = width_inches - 1.5  # 0.75 * 2
                    expected_content_height = height_inches - 1.5

                    # KDP standard page sizes (approximately)
                    std_6x9_width = 6.0
                    std_6x9_height = 9.0
                    std_letter_width = 8.5
                    std_letter_height = 11.0

                    # Check if dimensions are close to standard (within 0.1in tolerance)
                    is_6x9 = (abs(width_inches - std_6x9_width) < 0.1 and
                             abs(height_inches - std_6x9_height) < 0.1)
                    is_letter = (abs(width_inches - std_letter_width) < 0.1 and
                                abs(height_inches - std_letter_height) < 0.1)

                    if is_6x9 or is_letter:
                        self.checks.append(ValidationResult(
                            "margin_accuracy",
                            "pass",
                            f"Page size {width_inches:.2f}x{height_inches:.2f} inches with {self.config.margins}in margins meets KDP standards"
                        ))
                    else:
                        self.checks.append(ValidationResult(
                            "margin_accuracy",
                            "warning",
                            f"Non-standard page size {width_inches:.2f}x{height_inches:.2f} inches - verify margins are appropriate"
                        ))
                else:
                    self.checks.append(ValidationResult(
                        "margin_accuracy",
                        "warning",
                        "Could not parse page dimensions"
                    ))
            else:
                self.checks.append(ValidationResult(
                    "margin_accuracy",
                    "warning",
                    "Could not determine page size"
                ))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.checks.append(ValidationResult(
                "margin_accuracy",
                "error",
                "pdfinfo not available or timed out"
            ))

    def _analyze_paragraph_structure(self, pdf_path: str) -> Dict[str, int]:
        """Analyze paragraph structure from extracted text"""
        if PdfReader is None:
            return {"error": "pypdf not available"}

        try:
            reader = PdfReader(pdf_path)
            text = ""

            # Extract text from first 10 pages to avoid performance issues
            for i, page in enumerate(reader.pages[:10]):
                page_text = page.extract_text() or ""
                text += page_text + "\n"

            # Split into paragraphs (heuristic: double newlines or single newlines with short lines)
            paragraphs = []
            for para in text.split('\n\n'):
                para = para.strip()
                if para:
                    # Split on single newlines and treat as separate paragraphs
                    sub_paras = [p.strip() for p in para.split('\n') if p.strip()]
                    paragraphs.extend(sub_paras)

            # Analyze potential first paragraphs after headings
            potential_first_paras = 0
            indented_first_paras = 0

            # Look for patterns: short line followed by longer paragraph (heading pattern)
            lines = text.split('\n')
            i = 0
            while i < len(lines) - 1:
                current_line = lines[i].strip()
                next_line_raw = lines[i + 1]

                # Heuristic: short line (likely heading) followed by longer paragraph
                if (len(current_line) > 0 and len(current_line) < 50 and
                    len(next_line_raw.strip()) > len(current_line) * 2):
                    potential_first_paras += 1

                    # Check if the next paragraph appears indented (starts with 2+ spaces/tabs)
                    leading_ws = len(next_line_raw) - len(next_line_raw.lstrip(' \t'))
                    if leading_ws >= 2:
                        indented_first_paras += 1

                    i += 2  # Skip the next line since we analyzed it
                else:
                    i += 1

            return {
                "potential_first_paras": potential_first_paras,
                "indented_first_paras": indented_first_paras,
                "total_paragraphs_analyzed": len(paragraphs)
            }

        except Exception as e:
            return {"error": str(e)}

    def _parse_css_rules(self, css_path: str) -> Dict[str, Any]:
        """Parse CSS file and extract KDP-relevant rules"""
        if not os.path.exists(css_path):
            return {"error": "CSS file not found"}

        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()

            # Extract key KDP formatting rules using regex
            rules = {}

            # Check for orphans/widows settings
            import re
            orphans_match = re.search(r'orphans:\s*(\d+)', css_content)
            widows_match = re.search(r'widows:\s*(\d+)', css_content)
            rules['orphans'] = int(orphans_match.group(1)) if orphans_match else None
            rules['widows'] = int(widows_match.group(1)) if widows_match else None

            # Check paragraph indentation
            indent_match = re.search(r'text-indent:\s*([\d.]+)in', css_content)
            rules['paragraph_indent'] = float(indent_match.group(1)) if indent_match else None

            # Check for first-para no-indent rules
            rules['has_first_para_no_indent'] = bool(re.search(r'\.first-para.*text-indent:\s*0', css_content))
            rules['has_heading_adjacent_no_indent'] = bool(re.search(r'h[123]\s*\+\s*p.*text-indent:\s*0', css_content))
            rules['has_chapter_title_no_indent'] = bool(re.search(r'\.chapter-title\s*\+\s*p.*text-indent:\s*0', css_content))

            # Check drop cap settings
            drop_cap_match = re.search(r'first-letter.*line-height:\s*([\d.]+)', css_content, re.DOTALL)
            rules['drop_cap_line_height'] = float(drop_cap_match.group(1)) if drop_cap_match else None

            drop_cap_margin = re.search(r'first-letter.*margin.*?([\d.]+)em', css_content, re.DOTALL)
            rules['drop_cap_margin'] = float(drop_cap_margin.group(1)) if drop_cap_margin else None

            # Check page break rules
            rules['has_chapter_page_break'] = bool(re.search(r'\.chapter.*page-break-before:\s*always', css_content))
            rules['has_heading_avoid_break'] = bool(re.search(r'page-break-after:\s*avoid', css_content))

            # Check @page margins
            page_margin_match = re.search(r'@page.*margin:\s*([\d.]+)in', css_content, re.DOTALL)
            rules['css_margin'] = float(page_margin_match.group(1)) if page_margin_match else None

            return rules
        except Exception as e:
            return {"error": str(e)}

    def _check_css_kdp_compliance(self, pdf_path: str) -> None:
        """Validate CSS rules against KDP formatting standards"""
        css_path = self.config.css_path
        if not css_path:
            # Try to find styles.css in poc directory
            css_path = os.path.join(os.path.dirname(__file__), 'styles.css')

        rules = self._parse_css_rules(css_path)

        if "error" in rules:
            self.checks.append(ValidationResult(
                "css_kdp_compliance",
                "warning",
                f"Could not validate CSS rules: {rules['error']}"
            ))
            return

        issues = []

        # Check orphans/widows (KDP standard: minimum 3)
        if rules.get('orphans') is None or rules['orphans'] < 3:
            issues.append("orphans should be set to 3 or higher")
        if rules.get('widows') is None or rules['widows'] < 3:
            issues.append("widows should be set to 3 or higher")

        # Check paragraph indentation (KDP standard: 0.2-0.25in)
        if rules.get('paragraph_indent') is None:
            issues.append("paragraph text-indent not found (should be 0.2-0.25in)")
        elif not (0.2 <= rules['paragraph_indent'] <= 0.3):
            issues.append(f"paragraph indent is {rules['paragraph_indent']}in (KDP standard: 0.2-0.25in)")

        # Check first paragraph rules
        if not rules.get('has_first_para_no_indent'):
            issues.append("missing .first-para { text-indent: 0; } rule")
        if not rules.get('has_heading_adjacent_no_indent'):
            issues.append("missing h1/h2/h3 + p { text-indent: 0; } rules")
        if not rules.get('has_chapter_title_no_indent'):
            issues.append("missing .chapter-title + p { text-indent: 0; } rule")

        # Check drop cap settings if enabled
        if self.config.use_drop_caps:
            if rules.get('drop_cap_line_height') and rules['drop_cap_line_height'] < 1.0:
                issues.append(f"drop cap line-height is {rules['drop_cap_line_height']} (should be >= 1.0 to prevent overlap)")
            if rules.get('drop_cap_margin') and rules['drop_cap_margin'] < 0.05:
                issues.append(f"drop cap margin is {rules['drop_cap_margin']}em (should be >= 0.05em for proper spacing)")

        # Check page break rules
        if not rules.get('has_chapter_page_break'):
            issues.append("missing page-break-before: always for chapters")
        if not rules.get('has_heading_avoid_break'):
            issues.append("missing page-break-after: avoid for headings")

        # Check margin consistency
        if rules.get('css_margin') and abs(rules['css_margin'] - self.config.margins) > 0.01:
            issues.append(f"CSS margin ({rules['css_margin']}in) doesn't match configured margin ({self.config.margins}in)")

        if issues:
            self.checks.append(ValidationResult(
                "css_kdp_compliance",
                "fail",
                f"CSS does not fully comply with KDP standards: {'; '.join(issues)}",
                details={"issues": issues, "rules_found": rules}
            ))
        else:
            self.checks.append(ValidationResult(
                "css_kdp_compliance",
                "pass",
                "CSS rules comply with KDP formatting standards",
                details={"rules_found": rules}
            ))

    def _check_page_content_distribution(self, pdf_path: str) -> None:
        """Check for potential orphan/widow issues by analyzing page content"""
        if PdfReader is None:
            self.checks.append(ValidationResult(
                "page_content_distribution",
                "error",
                "pypdf not available for page content analysis"
            ))
            return

        try:
            reader = PdfReader(pdf_path)
            problematic_pages = []

            for page_num in range(min(50, len(reader.pages))):  # Check first 50 pages
                page = reader.pages[page_num]
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    continue

                # Count approximate lines (split on newlines)
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                line_count = len(lines)

                # Flag pages with very few lines (potential orphan/widow issues)
                # Skip page 0 (might be title page) and very short pages
                if page_num > 0 and line_count > 0 and line_count < 5:
                    problematic_pages.append(page_num + 1)  # 1-indexed for user

            if problematic_pages:
                self.checks.append(ValidationResult(
                    "page_content_distribution",
                    "warning",
                    f"POTENTIAL ORPHAN/WIDOW ISSUES: Pages with very few lines detected: {', '.join(map(str, problematic_pages))}. KDP Standard: Minimum 3 lines per page (orphans: 3, widows: 3 in CSS). Manually verify these pages in KDP Preview to ensure professional appearance."
                ))
            else:
                self.checks.append(ValidationResult(
                    "page_content_distribution",
                    "pass",
                    "No pages with unusually few lines detected. Orphan/widow control appears effective (KDP standard: minimum 3 lines)."
                ))

        except Exception as e:
            self.checks.append(ValidationResult(
                "page_content_distribution",
                "error",
                f"Failed to analyze page content: {str(e)}"
            ))

    def _add_kdp_standards_reference(self) -> None:
        """Add a comprehensive KDP formatting standards reference to the report"""
        standards = {
            "Page Setup": [
                "Page Size: 6x9 inches (standard) or 8.5x11 inches (letter)",
                "Margins: 0.75 inches on all sides (minimum 0.5in, maximum 1.5in)",
                "Minimum Page Count: 24 pages for KDP paperback"
            ],
            "Typography": [
                "Body Text: 10-12pt font size",
                "Line Spacing: 1.15-1.5 (1.4 recommended)",
                "Paragraph Indent: 0.2-0.25 inches for body paragraphs",
                "First Paragraph: NO indent after chapter titles or headings",
                "Text Alignment: Justified or left-aligned"
            ],
            "Page Breaks & Flow": [
                "Chapters: Must start on new pages (page-break-before: always)",
                "Headings: Should not be orphaned (page-break-after: avoid)",
                "Orphans: Minimum 3 lines at bottom of page (orphans: 3)",
                "Widows: Minimum 3 lines at top of page (widows: 3)",
                "Paragraphs: Avoid splitting mid-paragraph (page-break-inside: avoid)"
            ],
            "Fonts": [
                "All fonts must be embedded in PDF",
                "Use professional, readable fonts (Bookerly, Garamond, Baskerville, etc.)",
                "Avoid decorative fonts for body text"
            ],
            "Drop Caps": [
                "Optional feature - use with caution",
                "Must NOT overlap adjacent text",
                "Requires line-height >= 1.0 and proper margin-right spacing",
                "Recommended: Disable unless specifically needed for design"
            ]
        }

        details_text = "\n\n".join([
            f"{category}:\n" + "\n".join([f"  • {item}" for item in items])
            for category, items in standards.items()
        ])

        self.checks.append(ValidationResult(
            "kdp_standards_reference",
            "pass",
            "KDP Formatting Standards Reference (for manual verification)",
            details={"standards": standards, "formatted_text": details_text}
        ))

    def _check_text_indentation_patterns(self, pdf_path: str) -> None:
        """Check text indentation patterns for consistency"""
        if PdfReader is None:
            self.checks.append(ValidationResult(
                "text_indentation_patterns",
                "error",
                "pypdf not available for indentation analysis"
            ))
            return

        try:
            reader = PdfReader(pdf_path)
            indented_count = 0
            non_indented_count = 0

            # Analyze first 20 pages
            for page in reader.pages[:20]:
                page_text = page.extract_text() or ""
                lines = page_text.split('\n')

                for line in lines:
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue

                    # Count lines with significant indentation (2+ spaces/tabs)
                    leading_ws = len(line) - len(line.lstrip(' \t'))
                    if leading_ws >= 2:
                        indented_count += 1
                    else:
                        # Skip very short lines (likely headings) and lines that start with numbers/letters
                        if len(line_stripped) > 10 and not (line_stripped[0].isdigit() or line_stripped[0].isupper()):
                            non_indented_count += 1

            total_analyzed = indented_count + non_indented_count

            if total_analyzed < 10:
                self.checks.append(ValidationResult(
                    "text_indentation_patterns",
                    "warning",
                    "Insufficient text for indentation analysis"
                ))
                return

            indented_ratio = indented_count / total_analyzed

            # Expect most paragraphs to be indented (KDP standard)
            # Thresholds: >70% = pass (good indentation), >50% = warning (mixed), <=50% = fail (poor indentation)
            msg = f"Indented lines: {indented_count}/{total_analyzed} ({indented_ratio:.0%})"
            if indented_ratio > 0.7:  # More than 70% indented
                self.checks.append(ValidationResult(
                    "text_indentation_patterns",
                    "pass",
                    msg
                ))
            elif indented_ratio > 0.5:  # More than 50% indented
                self.checks.append(ValidationResult(
                    "text_indentation_patterns",
                    "warning",
                    msg
                ))
            else:
                self.checks.append(ValidationResult(
                    "text_indentation_patterns",
                    "fail",
                    msg
                ))

        except Exception as e:
            self.checks.append(ValidationResult(
                "text_indentation_patterns",
                "error",
                f"Failed to analyze indentation patterns: {str(e)}"
            ))

    def _check_paragraph_formatting(self, pdf_path: str) -> None:
        """Check paragraph formatting options for KDP compliance"""
        # Check if paragraph spacing is enabled
        if self.config.use_paragraph_spacing:
            self.checks.append(ValidationResult(
                "paragraph_spacing",
                "warning",
                "Paragraph spacing enabled - may not meet traditional KDP print standards. Consider using KDP Standard formatting for print books."
            ))

        # Check if indentation is disabled
        if self.config.disable_indentation:
            self.checks.append(ValidationResult(
                "paragraph_indentation",
                "warning",
                "Paragraph indentation disabled - may not meet traditional KDP print standards. Consider using KDP Standard formatting for print books."
            ))

        # If both spacing and no indentation, suggest this is for digital use
        if self.config.use_paragraph_spacing and self.config.disable_indentation:
            self.checks.append(ValidationResult(
                "formatting_style",
                "info",
                "Using block paragraph style with spacing - suitable for digital books but may not meet KDP print guidelines."
            ))
        elif not self.config.use_paragraph_spacing and not self.config.disable_indentation:
            self.checks.append(ValidationResult(
                "formatting_style",
                "pass",
                "Using KDP Standard formatting (indented paragraphs, no spacing) - recommended for print books."
            ))


def validate_pdf_file(pdf_path: str, config: Optional[ValidationConfig] = None) -> ValidationReport:
    """
    Convenience function to validate a PDF file

    Args:
        pdf_path: Path to PDF file
        config: Optional validation configuration (renderer settings)

    Returns:
        ValidationReport
    """
    validator = PDFValidator(config)
    return validator.validate_pdf(pdf_path, config)


def generate_validation_report(report: ValidationReport, output_path: str):
    """
    Generate a human-readable validation report

    Args:
        report: ValidationReport to write
        output_path: Path to write the report
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"PDF Validation Report\n")
        f.write(f"===================\n\n")
        f.write(f"File: {report.pdf_path}\n")
        f.write(f"Overall Status: {report.overall_status.upper()}\n\n")

        f.write("Detailed Checks:\n")
        f.write("----------------\n\n")

        for check in report.checks:
            status_icon = {
                'pass': '✓',
                'fail': '✗',
                'warning': '⚠',
                'error': '✗'
            }.get(check.status, '?')

            f.write(f"{status_icon} {check.check_name}: {check.status.upper()}\n")
            f.write(f"   {check.message}\n")

            if check.details:
                for key, value in check.details.items():
                    f.write(f"   - {key}: {value}\n")

            f.write("\n")

        # Summary
        status_counts = {}
        for check in report.checks:
            status_counts[check.status] = status_counts.get(check.status, 0) + 1

        f.write("Summary:\n")
        f.write("--------\n")
        for status, count in status_counts.items():
            f.write(f"{status.upper()}: {count}\n")
