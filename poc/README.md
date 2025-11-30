# KDP Formatter POC (Proof of Concept)

This directory contains a Proof of Concept implementation demonstrating the KDP formatting workflow. The POC converts manuscripts to KDP-compliant PDFs and EPUBs, validating them for publishing requirements.

## Overview

The POC implements a complete document processing pipeline:

1. **Convert** various input formats (.txt, .pdf, .docx, .md) to IDM (Internal Document Model)
2. **Render** IDM to KDP-formatted PDF and/or EPUB using WeasyPrint/Pandoc and custom CSS
3. **Validate** generated files for KDP compatibility using pypdf/Poppler and epubcheck tools
4. **Generate** validation reports for manual KDP Preview and Kindle Previewer verification

## AI-Powered Structure Detection

The POC now supports both regex-based and AI-powered document structure detection using OpenAI's GPT models. AI detection provides more accurate chapter, heading, and structure recognition while preserving exact original text.

### Key Features

- **Intelligent Structure Detection**: Identifies chapters, headings (H1-H3), paragraphs, quotes, footnotes, and front/back matter
- **Cost Tracking**: Monitors API usage and costs for each document
- **Fallback Support**: Automatically falls back to regex detection if AI fails
- **Chunking Strategy**: Handles large documents by processing in 5-10 page chunks
- **JSON Mode**: Uses deterministic output for consistent results

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
sudo apt install pandoc poppler-utils  # For document conversion and PDF validation
sudo apt install default-jre  # For EPUB validation with epubcheck

# Set up AI detection (optional)
export OPENAI_API_KEY=your-openai-api-key-here

# Run basic test (PDF only)
python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf

# Generate both PDF and EPUB
python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf --epub

# Generate EPUB only
python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample.epub --epub --skip-pdf

# Run with AI detection
python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_ai.pdf --epub --use-ai

# Run all tests
bash poc/run_tests.sh
```

## Usage

### Command Line Interface

```bash
python poc/kdp_poc.py [OPTIONS]
```

#### Required Arguments

- `--input, -i INPUT` - Input document path (supports .txt, .pdf, .docx, .md)
- `--output, -o OUTPUT` - Output PDF path

#### Optional Arguments

- `--css CSS` - Custom CSS stylesheet path (default: poc/styles.css)
- `--validate-only` - Only validate existing PDF, do not generate
- `--epub` - Generate EPUB output alongside PDF (or instead of PDF if --skip-pdf is used)
- `--epub-output EPUB_OUTPUT` - Custom EPUB output path (default: replace .pdf extension with .epub)
- `--skip-pdf` - Skip PDF generation, only generate EPUB (requires --epub flag)
- `--use-ai` - Use OpenAI for intelligent structure detection (requires OPENAI_API_KEY)
- `--compare-methods` - Compare regex vs AI detection methods and show differences
- `--verbose, -v` - Enable verbose output
- `--help` - Show help message

#### Examples

```bash
# Basic conversion (PDF only)
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/sample.pdf

# Generate both PDF and EPUB
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/sample.pdf --epub

# Generate EPUB only
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/sample.epub --epub --skip-pdf

# Custom EPUB output path
python poc/kdp_poc.py -i manuscript.docx -o output/book.pdf --epub --epub-output output/custom.epub

# Convert with custom CSS
python poc/kdp_poc.py -i manuscript.docx -o output/book.pdf -css my_styles.css --epub

# Validate existing PDF
python poc/kdp_poc.py -i dummy.txt -o output/existing.pdf --validate-only

# Verbose output
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/sample.pdf --epub -v

# AI-powered structure detection
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/sample.pdf --epub --use-ai -v

# Compare detection methods
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/sample.pdf --compare-methods
```

## Input Formats

### Supported Formats

- **`.txt`** - Plain text files (best supported)
- **`.pdf`** - PDF documents (text extraction via pdfminer.six)
- **`.docx`** - Microsoft Word documents (via Pandoc)
- **`.md`** - Markdown files (via Pandoc)

### Format Requirements

- **Text files**: UTF-8 encoded, basic chapter detection
- **PDF files**: Must contain selectable text (not image-based)
- **DOCX/MD files**: Standard formatting supported via Pandoc
- **File size**: Reasonable limits (< 50MB recommended)

## AI Detection

### How It Works

The AI detection system uses OpenAI's GPT models with JSON mode for deterministic, structured output:

1. **Text Chunking**: Documents are split into 5-10 page chunks (approximately 2000 characters) to stay within token limits
2. **Structured Prompts**: Each chunk is processed with detailed prompts specifying the expected JSON structure
3. **Cost Tracking**: All API calls are tracked with token usage and cost calculations
4. **Result Aggregation**: Chunk results are combined into a unified document structure

### Detected Elements

- **Chapters**: Automatic chapter identification and numbering
- **Headings**: H1-H3 heading hierarchy detection
- **Paragraphs**: Text block segmentation with style hints
- **Quotes**: Blockquote and attribution detection
- **Front/Back Matter**: Preface, introduction, appendices, etc.
- **Footnotes**: Reference and content extraction

### Cost Tracking

API usage is tracked per document with detailed breakdowns:

- **Token counting**: Precise input/output token tracking
- **Cost calculation**: Per-call and total cost reporting
- **Model pricing**: Automatic pricing for GPT-4-turbo-preview and GPT-3.5-turbo
- **Estimates**: ~$0.01-0.05 per 10k words (varies by model and content complexity)

See [`docs/ai_cost_analysis.md`](../docs/ai_cost_analysis.md) for detailed cost analysis and projections.

### Accuracy

AI detection typically provides superior accuracy compared to regex patterns:

- **Better chapter detection**: Handles varied numbering schemes and implicit chapters
- **Context awareness**: Understands document structure and relationships
- **Style preservation**: Maintains original formatting and emphasis markers
- **Edge case handling**: Manages complex documents with mixed content types

## EPUB Generation

The POC now generates EPUB 3 files compatible with Kindle Direct Publishing:

- **Reflowable layout**: Text reflows for different screen sizes and devices
- **Semantic HTML5**: Proper structure with headings, chapters, and navigation
- **Embedded fonts**: Source Serif 4 (OFL-licensed) for consistent typography
- **Table of contents**: Hierarchical nav.xhtml with proper EPUB 3 structure
- **Endnotes**: Footnotes converted with backlinks for enhanced navigation
- **KDP compliance**: Passes epubcheck and supports Enhanced Typesetting

### How EPUB Generation Works

1. **IDM Conversion**: IDM documents are converted to semantic HTML5
2. **Pandoc Processing**: HTML is converted to EPUB 3 using Pandoc with metadata
3. **Post-processing**: EPUB is enhanced with nav.xhtml, fonts, and endnotes
4. **Validation**: Files are validated with epubcheck for EPUB 3 compliance
5. **KDP Testing**: Manual testing with Kindle Previewer and KDP Preview

### EPUB Features

- **Chapter Structure**: Proper `<section epub:type="chapter">` elements
- **Navigation**: Hierarchical table of contents with `nav.xhtml`
- **Typography**: Source Serif 4 fonts with CSS `@font-face` declarations
- **Footnotes**: Converted to endnotes section with bidirectional links
- **Metadata**: Dublin Core elements in OPF package file
- **Accessibility**: Semantic HTML5 with proper heading hierarchy

### Kindle Previewer Testing

EPUB files require manual testing with Kindle Previewer 3:

1. **Device Simulation**: Test on phone, tablet, and e-reader profiles
2. **Navigation Testing**: Verify TOC links and page turning
3. **Font Rendering**: Confirm Source Serif 4 displays correctly
4. **Enhanced Typesetting**: Check KDP Enhanced Typesetting activation

### EPUB vs PDF Comparison

| Feature | PDF | EPUB |
|---------|-----|------|
| Layout | Fixed | Reflowable |
| File Size | Smaller | Larger (HTML structure) |
| Generation | Faster | Slower (Pandoc + post-processing) |
| Validation | Automated | epubcheck + manual |
| KDP Preview | Direct upload | Enhanced Typesetting |
| Use Case | Print books | Digital reading |

## Output Files

For each conversion, the POC generates:

- **`{filename}_print.pdf`** - KDP-formatted PDF ready for upload (if PDF generation enabled)
- **`{filename}_print.epub`** - KDP-formatted EPUB 3 ready for upload (if EPUB generation enabled)
- **`{filename}_print_idm.json`** - Internal Document Model (JSON)
- **`{filename}_print_report.txt`** - PDF validation report (if PDF generated)
- **`{filename}_print_epub_report.html`** - EPUB validation report (if EPUB generated)

### IDM JSON Structure

```json
{
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "isbn": "ISBN-13",
    "language": "en",
    "word_count": 12500,
    "page_count_estimate": 45
  },
  "chapters": [
    {
      "title": "Chapter 1",
      "number": 1,
      "paragraphs": [
        {
          "text": "Paragraph text...",
          "style": "normal",
          "alignment": "left",
          "indent": 0.25,
          "spacing_before": 0.0,
          "spacing_after": 0.0
        }
      ]
    }
  ]
}
```

## Validation Checks

The POC validates generated files for KDP compatibility:

### PDF Validation
- **File size**: < 500MB (KDP limit)
- **Page count**: > 24 pages (KDP minimum)
- **PDF version**: 1.4+ recommended
- **Embedded fonts**: All fonts properly embedded
- **Metadata**: Title and author present
- **Page dimensions**: Standard print sizes
- **Text extraction**: Text can be extracted from PDF

### EPUB Validation
- **File size**: Reasonable limits (< 50MB recommended)
- **HTML files**: < 300 files per EPUB (KDP limit)
- **Individual files**: < 30MB per file (KDP limit)
- **EPUB version**: Valid EPUB 3.0 format
- **epubcheck**: Passes automated validation
- **Embedded fonts**: Source Serif 4 properly embedded
- **Metadata**: Title, author, language, ISBN present
- **Navigation**: nav.xhtml present and valid
- **Structure**: Proper EPUB 3 package structure

## Dependencies

### Python Packages
- `weasyprint` - PDF generation
- `pdfminer.six` - PDF text extraction
- `pypdf` - PDF validation
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML processing
- `jsonschema` - JSON validation
- `openai` - AI structure detection (optional)
- `tiktoken` - Token counting for cost estimation (optional)
- `tenacity` - Retry logic for API resilience (optional)

### System Dependencies
- `pandoc` - Document format conversion and EPUB generation
- `poppler-utils` - PDF analysis tools (pdffonts, pdfinfo)

### EPUB-Specific Dependencies
- `epubcheck` - EPUB validation (requires Java)
- `default-jre` - Java Runtime Environment for epubcheck
- `zip/unzip` - EPUB file manipulation (usually pre-installed)

### Manual Installation
- **Kindle Previewer 3**: Download from KDP website (Windows/Mac only)
  - Required for manual EPUB testing and device simulation
  - No CLI version available - GUI testing required

### Installation

```bash
# Python dependencies
pip install -r requirements.txt

# System dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install pandoc poppler-utils

# EPUB-specific dependencies
sudo apt install default-jre  # For epubcheck

# Install epubcheck manually (see scripts/install_system_deps.sh)
bash scripts/install_system_deps.sh

# Optional: Additional fonts (see fonts/README.md)
# Optional: Kindle Previewer 3 (download manually from KDP website)
```

## Customization

### CSS Styling

Modify `poc/styles.css` to customize:

- **Page dimensions**: `@page` rule for size/orientation
- **Typography**: Font families, sizes, line heights
- **Spacing**: Margins, padding, paragraph spacing
- **Headers/footers**: Running headers with title/page numbers
- **Chapter styling**: Breaks, titles, spacing

### Font Configuration

See `poc/fonts/README.md` for font setup instructions.

## Testing

### Automated Tests

```bash
# Run all available test files (PDF + EPUB)
bash poc/run_tests.sh

# Test individual files (PDF only)
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/test.pdf

# Test EPUB generation
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/test.pdf --epub

# Test EPUB-only generation
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/test.epub --epub --skip-pdf

# Test AI detection (requires OPENAI_API_KEY)
python poc/test_ai_detection.py

# Compare detection methods
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/test.pdf --compare-methods
```

### Test Data

See `test_data/README.md` for sample manuscripts.

## KDP Preview Integration

### PDF Testing
After generating PDFs:

1. Go to [KDP Preview](https://kdp.amazon.com/en_US/preview)
2. Select "Paperback" format and upload `{filename}_print.pdf`
3. Check formatting in the preview interface
4. Document results in `docs/poc_results.md`

### EPUB Testing
After generating EPUBs:

1. **epubcheck validation**: Automated validation (integrated)
2. **Kindle Previewer 3**: Manual testing for device compatibility
   - Download from: https://kdp.amazon.com/en_US/help/topic/G202131170
   - Test on phone, tablet, and e-reader profiles
   - Verify Enhanced Typesetting activation
3. **KDP Preview**: Upload EPUB for publishing
   - Select "Kindle" format (not Print)
   - Enable Enhanced Typesetting if available
   - Check reflowable layout and navigation

### Testing Documentation
- Document all results in `docs/poc_results.md`
- Follow the protocol in `docs/kdp_preview_testing_protocol.md`
- Include screenshots for any issues found

## Troubleshooting

### Common Issues

**"ImportError: weasyprint not found"**
- Install with: `pip install weasyprint`
- May require additional system packages

**"Pandoc not found"**
- Install with: `sudo apt install pandoc`
- Verify: `pandoc --version`

**"pdffonts not found"**
- Install with: `sudo apt install poppler-utils`
- Verify: `pdffonts -v`

**"OpenAI API key not found"**
- Set environment variable: `export OPENAI_API_KEY=your-key-here`
- Or add to `.env` file in project root
- Verify: `echo $OPENAI_API_KEY`

**"OpenAI API rate limit exceeded"**
- Wait and retry the request
- Consider upgrading OpenAI plan for higher limits
- Use smaller chunks or fewer API calls

**"Font not embedded"**
- Check CSS `@font-face` declarations
- Ensure font files exist in `poc/fonts/`
- Verify font licensing

**"PDF looks wrong"**
- Check CSS for syntax errors
- Verify HTML generation in IDM JSON
- Test with different input formats

**"Conversion fails"**
- Check input file format and encoding
- Verify file is not corrupted
- Use verbose mode (`-v`) for details

### Debug Mode

Enable verbose output for detailed logging:

```bash
python poc/kdp_poc.py -i input.txt -o output.pdf -v
```

### Validation Only

Test validation on existing PDFs:

```bash
python poc/kdp_poc.py -i dummy.txt -o existing.pdf --validate-only
```

## File Structure

```
poc/
├── kdp_poc.py          # Main CLI script
├── converters.py       # Document format converters
├── renderer.py         # PDF renderer using WeasyPrint
├── validator.py        # PDF validation using pypdf/Poppler
├── epub_generator.py   # EPUB 3 generator using Pandoc
├── epub_validator.py   # EPUB validation using epubcheck
├── idm_schema.py       # Internal Document Model definitions
├── styles.css          # PDF KDP-compatible CSS styling
├── epub_styles.css     # EPUB KDP-compatible CSS styling
├── fonts/              # Font files and licensing
│   ├── SourceSerif4-Regular.ttf
│   ├── SourceSerif4-Semibold.ttf
│   ├── OFL-LICENSE.txt
│   └── README.md
├── run_tests.sh        # Test runner script
└── README.md           # This file
```

## Performance Notes

- **Small documents** (< 10 pages): Instant processing
- **Medium documents** (10-100 pages): Few seconds
- **Large documents** (> 100 pages): May take longer
- **Memory usage**: ~100-500MB depending on document size

## Limitations

- Basic text-only layout (no images, tables, complex formatting)
- AI detection requires internet connection and API costs
- EPUB generation requires Pandoc and epubcheck for full validation
- Kindle Previewer 3 required for comprehensive EPUB testing (GUI-only, Windows/Mac)
- Limited font subset (expand as needed)
- AI detection may have token limits for very large documents

## Contributing

When adding features:

1. Update relevant modules
2. Add test cases in `test_data/`
3. Update documentation
4. Test with multiple input formats
5. Validate with KDP Preview
