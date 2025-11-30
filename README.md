# KDP Formatter SaaS

## Project Overview
- KDP Formatter SaaS application for converting manuscripts to KDP-compliant PDF and EPUB
- Deployed on e2-medium VM at `kdppublish.newmarylebonepress.com`
- Isolated installation at `/opt/kdp-formatter`

## Quick Start

### 1. Install System Dependencies
```bash
# Run the system dependency installer
bash scripts/install_system_deps.sh
```

### 2. Install Python Dependencies
```bash
# Install all required Python packages
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key (required for AI detection)
# OPENAI_API_KEY=your_key_here
```

### 4. Start the Local Testing UI
```bash
# Start the web interface on localhost:8001
bash scripts/start_localhost.sh

# Or run directly:
python -m uvicorn app.main:app --host localhost --port 8001 --reload
```

### 5. Open in Browser
Navigate to `http://localhost:8001` to access the KDP Formatter UI.

## Testing the POC

Before deployment, thoroughly test the KDP formatting to ensure all fixes are working correctly.

### Automated Testing

Run comprehensive tests on all sample files:

```bash
bash scripts/run_comprehensive_tests.sh
```

This will generate PDFs with various configurations and create validation reports in `output/test_results/`.

### Manual Testing with Web UI

1. **Start the localhost web interface:**
   ```bash
   bash scripts/start_localhost.sh
   ```

2. **Access the interface:**
   Open your browser to http://localhost:8001

3. **Test formatting:**
   - Upload your manuscript files (.txt, .docx, .pdf, .md)
   - Configure options (page size, margins, drop caps, AI detection)
   - Generate PDF and preview results
   - Download and inspect generated files
   - Review validation reports

4. **Visual inspection:**
   - Check drop cap rendering (if enabled)
   - Verify paragraph indentation (0.25" for subsequent paragraphs, none after headings)
   - Confirm proper page breaks (no single-line orphans/widows)
   - Measure margins (should be exactly 0.75" or configured value)

### KDP Preview Upload

After local testing, upload generated PDFs to Amazon KDP Preview for official validation:

1. Log in to your KDP account
2. Navigate to KDP Preview tool
3. Upload the generated PDF
4. Review KDP validation messages
5. Test on different devices (phone, tablet, e-reader)
6. Document results in `docs/poc_results.md`

### Testing Documentation

For detailed testing instructions, see:
- `docs/MANUAL_TESTING_GUIDE.md` - Comprehensive testing guide
- `docs/TESTING_CHECKLIST.md` - Quick reference checklist
- `docs/poc_results.md` - Test results documentation template

### Known Issues

- **Drop caps**: Enabled by default in earlier versions, now disabled to avoid overlap issues. Use `--drop-caps` flag to enable if needed.
- **AI detection**: Requires OpenAI API key and incurs costs (~$0.01-0.05 per 10k words). Use `--use-ai` flag to enable.
- **EPUB generation**: Requires Pandoc installation. Use `--epub` flag to generate EPUB alongside PDF.

### Quick POC Usage

```bash
# Generate PDF with validation
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/sample.pdf -v

# Test with web UI
bash scripts/start_localhost.sh
# Then open http://localhost:8001

# Run comprehensive tests
bash scripts/run_comprehensive_tests.sh
```

## GitHub Repository
- **Repository**: https://github.com/MarquisdeMayfair/KDP-Formatter.git
- **Clone**: `git clone https://github.com/MarquisdeMayfair/KDP-Formatter.git`
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Contributions**: See `CONTRIBUTING.md` for guidelines

## Start with POC

Before deploying the full SaaS application, try the Proof of Concept (POC) to understand the formatting workflow. The `/poc` directory contains the working proof-of-concept code, while `/src` is reserved for future production implementation (currently empty).

### Quick POC Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   sudo apt install pandoc poppler-utils  # For PDF conversion and validation
   ```

2. **Download fonts** (optional but recommended):
   - See `poc/fonts/README.md` for font installation instructions
   - Professional fonts improve KDP Preview compatibility

3. **Run the POC:**
   ```bash
   # Basic usage (recommended)
   python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf

   # With drop caps enabled (use with caution, test in KDP Preview)
   python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf --drop-caps

   # With AI detection for complex documents
   python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf --use-ai

   # Generate both PDF and EPUB
   python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf --epub
   ```

4. **Alternative: Use the Web UI for manual testing:**
   ```bash
   cd app
   pip install -r ../requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```
   Then open `http://localhost:8001` in your browser for an interactive testing interface.

## Local Web UI

For manual testing and verification of formatting issues before deployment, use the FastAPI-based web interface at `http://localhost:8001`.

### Features
- **Drag-and-drop file upload** with instant validation
- **Flexible paragraph formatting**: KDP Standard, Modern, or No Indentation styles
- **Configurable chapter detection**: Recognizes Chapter, Letter, Part, Section patterns
- **Configuration options**: page size, margins, drop caps, AI detection, paragraph spacing
- **PDF preview** with PDF.js viewer and zoom controls
- **Validation results** displayed side-by-side with PDF
- **Download options** for PDF, EPUB, validation reports, and IDM JSON
- **Recent conversions** stored in browser localStorage
- **Session management** with automatic cleanup

## Formatting Options

The KDP Formatter provides three paragraph formatting styles to accommodate different publishing needs:

### KDP Standard (Recommended for Print)
- **Indentation**: 0.25" first-line indentation on all paragraphs except after headings
- **Spacing**: No spacing between paragraphs (traditional book formatting)
- **Use Case**: Standard print books, novels, traditional publishing
- **KDP Compliance**: ✅ Fully compliant

### Modern (Enhanced Readability)
- **Indentation**: 0.25" first-line indentation on all paragraphs except after headings
- **Spacing**: 0.5em spacing between paragraphs for improved readability
- **Use Case**: Digital-first books, modern publishing, accessibility
- **KDP Compliance**: ⚠️ May not meet traditional KDP guidelines but accepted

### No Indentation (Block Style)
- **Indentation**: No indentation on any paragraphs
- **Spacing**: 0.5em spacing between paragraphs for clear separation
- **Use Case**: Digital books, academic papers, modern web-style formatting
- **KDP Compliance**: ⚠️ May not meet traditional KDP guidelines

### Quick Start
```bash
cd app
uvicorn main:app --host localhost --port 8001 --reload
```
Then open `http://localhost:8001` in your browser.

### Usage Instructions
1. **Upload File**: Drag & drop or click to browse for .txt, .pdf, .docx, or .md files (max 50MB)
2. **Configure Options**:
   - **Output Format**: PDF only, EPUB only, or both
   - **Structure Detection**: Regex-based (free) or AI-powered (requires OpenAI API key)
   - **Page Size**: 6" x 9" (Standard KDP) or 8.5" x 11" (Letter)
   - **Margins**: 0.5" to 1.5" (default 0.75" per KDP standards)
   - **Drop Caps**: Enable with caution (may cause formatting issues)
3. **Generate & Validate**: Click the button to process your document
4. **Review Results**: PDF preview with validation results and configuration summary
5. **Download Files**: PDF, EPUB (if generated), validation report, or IDM JSON

### Testing Formatting Issues

Use the web UI to verify the fixes for the two critical formatting issues:

#### Paragraph Indentation Consistency
- **Issue**: Single-line paragraphs appeared indented, making multi-line paragraphs look misaligned
- **Solution**: Implemented class-based `.first-para` selectors with fallback adjacent sibling selectors
- **Verification**:
  - Look for first paragraph after chapter titles (should have no indent)
  - Look for first paragraph after h2/h3 headings (should have no indent)
  - Look for subsequent paragraphs (should have 0.25in indent)
  - Verify multi-line paragraphs align consistently with single-line paragraphs

#### Drop Cap Rendering
- **Issue**: Drop caps were overlapping text when enabled
- **Solution**: Fixed spacing and line-height in CSS (though disabled by default)
- **Verification**:
  - Enable drop caps in configuration (warning displayed)
  - Check first letter doesn't overlap adjacent text
  - Verify proper spacing and alignment
  - Test in KDP Preview for final validation

### KDP Preview Testing Protocol

After generating PDFs with the web UI, always upload to KDP Preview for final verification:

#### Essential Checks
- **Margins**: Verify 0.75" margins on all sides
- **Page Breaks**: Chapters start on new pages
- **Indentation**: 0.25" indent on body paragraphs, none after headings
- **Fonts**: All text renders correctly (Source Serif 4 embedded)
- **Metadata**: Title, author, and other info displays properly

#### Advanced Validation
- **Drop Caps**: If enabled, ensure no text overlap
- **Orphan/Widow Control**: Check for single-line pages
- **Page Numbers**: Verify header/footer placement
- **Hyphenation**: Justified text breaks properly
- **Image Handling**: Any images display correctly (if present)

#### Documentation Template
Use the template in `docs/poc_results.md` to document your testing results for each manuscript.

5. **Upload to KDP Preview:**
   - Go to [KDP Preview](https://kdp.amazon.com/en_US/preview)
   - Upload the generated `output/sample_print.pdf`
   - Check formatting in the preview interface

### POC Files
- [`poc/README.md`](poc/README.md) - Detailed usage and CLI options
- [`test_data/README.md`](test_data/README.md) - Sample manuscripts and test files
- [`docs/poc_results.md`](docs/poc_results.md) - KDP Preview validation template

### Manual Testing with Web UI

For interactive testing and validation before deployment, use the FastAPI-based web interface:

**Features:**
- Drag & drop file upload (.txt, .docx, .pdf, .md)
- Real-time configuration options (margins, page size, AI detection, drop caps)
- Live PDF preview with zoom controls
- Validation reports with detailed checks
- Download generated PDFs and validation reports
- Automatic cleanup of temporary files

**Quick Start:**
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
Access at: `http://localhost:8001`

**Testing Workflow:**
1. Upload manuscript via drag & drop
2. Configure formatting options
3. Generate PDF (and optionally EPUB)
4. Review validation results and preview
5. Download files and test in KDP Preview
6. Document results in `docs/poc_results.md`

### POC Workflow
1. Convert manuscript → IDM (Internal Document Model)
2. Render IDM → KDP-formatted PDF
3. Validate PDF for KDP requirements
4. Upload to KDP Preview for final verification

**Formatting Test Generator:**

Use the `/formatting-test` endpoint to generate a test PDF with known formatting patterns:
- First paragraphs after headings (should have no indent)
- Subsequent paragraphs (should have 0.25" indent)
- Drop caps test (if enabled)
- Multiple heading levels
- Long content for page break testing

Access via: `http://localhost:8001/formatting-test?use_drop_caps=false&page_size=6x9&margins=0.75`

### Formatting Standards

The POC implements KDP-compliant formatting standards:

**Typography:**
- Font: Source Serif 4 (Regular/Semibold) with fallbacks
- Font Size: 11pt body text, 18pt chapter titles
- Line Height: 1.4 for optimal readability
- Text Alignment: Justified with proper hyphenation

**Layout:**
- Page Size: 6" × 9" (standard KDP paperback)
- Margins: 0.75" on all sides (KDP requirement)
- Paragraph Indent: 0.25" (no indent after headings)
- Page Breaks: Automatic chapter breaks, avoid paragraph splitting

**Advanced Features:**
- Drop Caps: Optional decorative first letters (disabled by default)
- Orphan/Widow Control: Minimum 3 lines per page
- AI Detection: Optional OpenAI-powered structure analysis
- EPUB Generation: Reflowable e-book format with enhanced typesetting

**Validation:**
- Automated validation checks CSS compliance with KDP standards
- Verifies orphan/widow control (minimum 3 lines per page)
- Validates paragraph indentation rules
- Checks drop cap configuration (if enabled)
- Provides detailed KDP compliance report

For complete formatting standards, see [KDP Formatting Standards Reference](docs/kdp_formatting_standards.md).

### Validation Features

The KDP Formatter includes comprehensive validation to ensure your PDF meets KDP requirements:

**Automated Checks:**
- ✅ File size and page count
- ✅ PDF version and font embedding
- ✅ Page dimensions and margins
- ✅ CSS compliance with KDP standards
- ✅ Paragraph indentation patterns
- ✅ Orphan/widow control (no single-line pages)
- ✅ Drop cap configuration (if enabled)

**Manual Verification Required:**
- ⚠️ Drop cap rendering (visual inspection in KDP Preview)
- ⚠️ Page breaks and chapter starts
- ⚠️ Overall visual appearance

**Configuration-Aware Validation:**
The validator knows your renderer settings (drop caps, margins, page size) and provides context-specific feedback.

**Detailed Reports:**
- Pass/Warning/Fail status for each check
- Actionable recommendations for fixing issues
- KDP standards reference embedded in report
- Export validation report as text or view in browser

**KDP Compliance:**
- All fonts embedded (no external dependencies)
- PDF 1.4+ compatibility
- File size limits respected (< 500MB)
- Metadata properly set (title, author, etc.)

**Important Notes:**
- Drop caps are disabled by default due to potential formatting issues
- Always test final PDFs in KDP Preview before publishing
- AI detection adds cost but improves complex document handling
- Manual verification required for visual formatting elements

### Troubleshooting Formatting Issues

**Drop Cap Overlapping Text:**
- **Cause**: Drop cap CSS has insufficient line-height or margin-right
- **Solution**: Disable drop caps or ensure CSS has `line-height: 1.0` and `margin-right: 0.15em`
- **Validation**: Check `kdp_drop_caps` validation result

**Inconsistent Paragraph Indentation:**
- **Cause**: Missing CSS rules for first paragraphs after headings
- **Solution**: Ensure CSS has `h1 + p, h2 + p, h3 + p, .first-para { text-indent: 0; }`
- **Validation**: Check `kdp_paragraph_indentation` validation result

**Single-Line Pages (Orphan/Widow Issues):**
- **Cause**: Missing or insufficient orphan/widow CSS rules
- **Solution**: Ensure CSS has `orphans: 3; widows: 3;` on body and paragraph elements
- **Validation**: Check `page_content_distribution` validation result

**CSS Compliance Failures:**
- **Cause**: Stylesheet doesn't meet KDP standards
- **Solution**: Review `css_kdp_compliance` validation details for specific issues
- **Reference**: See [KDP Formatting Standards](docs/kdp_formatting_standards.md)

**PDF Upload Fails:**
- **Error**: "pdfminer.six is required for PDF conversion"
- **Solution**: Install the missing dependency with `pip install pdfminer.six`
- **Prevention**: Always run `pip install -r requirements.txt` before starting

**Chapters Not Detected:**
- **Problem**: All content appears as "Main Content" chapter, no proper indentation
- **Cause**: Chapter headings don't match recognized patterns
- **Solutions**: Use standard formats like "Chapter 1", "Letter 2", "Part I", or enable AI detection

**All Paragraphs Indented:**
- **Problem**: Every paragraph has indentation, including after headings
- **Cause**: Chapter detection failed, so first-paragraph rules don't apply
- **Solution**: Fix chapter detection or use "No Indentation" formatting style

**Always verify in KDP Preview:**
Automated validation catches most issues, but manual review in KDP Preview is essential before publishing.

## Project Status
- ✅ Phase 1: VM Environment Setup - Complete
- ✅ Phase 2: POC Core Processing - Complete
- ✅ Phase 3: POC AI Detection - Complete
- ✅ Phase 4: POC EPUB Generation - Complete
- 🔄 Phase 5: GitHub Setup & Documentation - In Progress
- ⏳ Phase 6: Production Backend - Pending
- ⏳ Phase 7+: Authentication, Stripe, Deployment - Pending

## Prerequisites
- Ubuntu 24.04 (Noble) VM with 4GB RAM
- SSH access: `ssh mrdeansgate@35.234.146.243` (or appropriate user for tax-treaty-server)
- Google Cloud project with Secret Manager API enabled
- Service account with Secret Manager access

## Installation Steps
1. Clone/transfer this repository to the VM
2. Run `sudo bash scripts/install_system_deps.sh` to install system packages
3. Run `bash scripts/setup_vm.sh` to create virtual environment and install Python dependencies
4. Configure secrets in Google Cloud Secret Manager (OpenAI API key, Stripe keys)
5. Copy systemd service: `sudo cp deployment/kdp-formatter.service /etc/systemd/system/`
6. Enable and start service: `sudo systemctl enable kdp-formatter && sudo systemctl start kdp-formatter`

## Installed Versions
Document exact versions after installation:
- Python: 3.11+
- Pandoc: 3.x
- Tesseract: 5.x
- ImageMagick: 7.x
- Ghostscript: 10.x
- WeasyPrint: 60.x
- epubcheck: 5.x

## Directory Structure
- `/opt/kdp-formatter/app/` - FastAPI application code
- `/opt/kdp-formatter/uploads/` - Temporary file uploads
- `/opt/kdp-formatter/outputs/` - Generated PDFs and EPUBs
- `/opt/kdp-formatter/logs/` - Application logs
- `/opt/kdp-formatter/venv/` - Python virtual environment

## Dependencies

### Required Python Packages
- **pdfminer.six** (20231228): PDF text extraction for PDF file uploads
- **weasyprint** (60.2): PDF rendering and generation
- **beautifulsoup4** (4.12.3): HTML parsing for DOCX/Pandoc conversion and EPUB generation
- **lxml** (5.1.0): XML/HTML processing for EPUB OPF manipulation and validation
- **pypdf** (4.0.1): PDF validation and analysis
- **fastapi** (0.109.0): Web API framework
- **uvicorn** (0.27.0): ASGI server
- **python-multipart** (0.0.6): File upload handling
- **jinja2** (3.1.2): HTML templating
- **openai** (1.12.0): AI-powered structure detection (optional)

### System Dependencies
- **Pandoc** (3.x): Document format conversion
- **Poppler** (24.x): PDF processing tools
- **Tesseract** (5.x): OCR for image text extraction (optional)
- **ImageMagick** (7.x): Image processing (optional)
- **Ghostscript** (10.x): PostScript/PDF processing

### Installation
```bash
# System dependencies
bash scripts/install_system_deps.sh

# Python dependencies
pip install -r requirements.txt
```

## Service Management
- Start: `sudo systemctl start kdp-formatter`
- Stop: `sudo systemctl stop kdp-formatter`
- Restart: `sudo systemctl restart kdp-formatter`
- Status: `sudo systemctl status kdp-formatter`
- Logs: `sudo journalctl -u kdp-formatter -f`

## Troubleshooting
- Check logs in `/opt/kdp-formatter/logs/app.log`
- Verify virtual environment: `source /opt/kdp-formatter/venv/bin/activate && python --version`
- Test dependencies: `pandoc --version`, `tesseract --version`, etc.
- Ensure port 8001 is not in use: `sudo lsof -i :8001`

### Dependency Installation Issues

### "pdfminer.six is required for PDF conversion"
This means Python dependencies aren't installed. Run:
```bash
pip install -r requirements.txt
```

### "Pandoc is required for DOCX/MD conversion"
Install system dependencies:
```bash
bash scripts/install_system_deps.sh
```

### "WeasyPrint installation failed"
WeasyPrint requires system libraries. On macOS:
```bash
brew install cairo pango gdk-pixbuf libffi
```

### Verify Installation
Check if all dependencies are installed:
```bash
python -c "from poc.converters import convert; from poc.renderer import render_document_to_pdf; print('All dependencies installed successfully!')"
```

### Common Formatting Issues

**Drop Cap Overlap:**
- **Symptom**: First letter overlaps with adjacent text
- **Cause**: Compressed line-height in CSS
- **Solution**: Keep drop caps disabled (default) or test carefully in KDP Preview
- **Prevention**: Use `--drop-caps` flag only when specifically requested by client

**Paragraph Indentation Problems:**
- **Symptom**: Inconsistent indentation in multi-line paragraphs
- **Cause**: Generic CSS selectors affecting all paragraphs
- **Solution**: Fixed with specific selectors for paragraphs after headings
- **Prevention**: Always test indentation in KDP Preview before publishing

**Single-Line Pages:**
- **Symptom**: Pages with only one line of text
- **Cause**: Insufficient orphan/widow control
- **Solution**: Enhanced with `orphans: 3` and `widows: 3` rules
- **Prevention**: Check page breaks in long documents

**Font Rendering Issues:**
- **Symptom**: Fonts not displaying correctly in KDP Preview
- **Cause**: Fonts not properly embedded or incompatible versions
- **Solution**: Ensure Source Serif 4 fonts are installed and embedded
- **Prevention**: Always use embedded fonts, test in KDP Preview

**Margin Inconsistencies:**
- **Symptom**: Margins appear different than expected
- **Cause**: PDF viewer interpretation or CSS margin settings
- **Solution**: Verify 0.75" margins in KDP Preview interface
- **Prevention**: Use standard KDP margin settings (0.75" on all sides)

### Web UI Specific Issues

**PDF Not Loading in Preview:**
- **Symptom**: PDF viewer shows blank or error message
- **Cause**: Browser compatibility or PDF.js loading issues
- **Solution**: Try different browser (Chrome recommended), clear cache, check console for errors
- **Prevention**: Test with multiple browsers during development

**File Upload Fails:**
- **Symptom**: Upload rejected or hangs indefinitely
- **Cause**: File size limit exceeded or unsupported format
- **Solution**: Check file size (max 50MB) and format (.txt, .pdf, .docx, .md only)
- **Prevention**: Validate files before upload on frontend

**Server Connection Issues:**
- **Symptom**: "Failed to fetch" or network errors
- **Cause**: Server not running or port conflict
- **Solution**: Verify server is running with `uvicorn main:app --host localhost --port 8001 --reload`
- **Prevention**: Check port availability and server logs

**Validation Results Missing:**
- **Symptom**: Validation shows "Loading..." indefinitely
- **Cause**: PDF generation failed or validation timeout
- **Solution**: Check server logs for errors, try smaller file or simpler document
- **Prevention**: Implement proper error handling and timeouts

**Session Files Not Found:**
- **Symptom**: Download links return 404 errors
- **Cause**: Automatic cleanup removed files or session expired
- **Solution**: Regenerate the document or check `app/output/` directory
- **Prevention**: Files auto-delete after 1 hour to manage disk space

## Security Notes
- All API keys stored in Google Cloud Secret Manager
- Service runs as `kdp-formatter` user (non-root)
- Resource limits configured in systemd service
- File uploads restricted to 50MB
