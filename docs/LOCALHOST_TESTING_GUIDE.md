# Localhost Testing Guide - KDP Formatter

This guide provides step-by-step instructions for testing the KDP Formatter web UI on localhost, with a focus on verifying the formatting fixes for paragraph indentation, drop caps, and orphan/widow control.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Pandoc installed (`brew install pandoc` on macOS, `apt install pandoc` on Ubuntu)
- Poppler tools (`brew install poppler` on macOS, `apt install poppler-utils` on Ubuntu)

### Quick Start
```bash
# Clone or navigate to project directory
cd /path/to/kdp-formatter

# Activate virtual environment
source venv/bin/activate  # or .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the web server
uvicorn app.main:app --host localhost --port 8001 --reload

# Open browser to http://localhost:8001
```

### Alternative: Use the Convenience Script
```bash
# Make the script executable (first time only)
chmod +x scripts/start_localhost.sh

# Run the script
./scripts/start_localhost.sh
```

## Testing Workflow

### Step 1: Upload Test Document
1. Open http://localhost:8001 in your browser
2. **Drag & drop** or **click to browse** for a test file:
   - Use `test_data/sample_short.txt` for basic testing
   - Use `test_data/sample_medium.txt` for comprehensive validation
   - Use `test_data/sample_long.docx` for performance testing

### Step 2: Configure Options
Select the following settings to test different formatting scenarios:

#### Page Size Options
- **6" x 9"** (Standard KDP): Most common, test default margins
- **8.5" x 11"** (Letter): Verify larger format handling

#### Margin Settings
- **0.5 inches**: Minimal margins
- **0.75 inches** (Standard): KDP requirement
- **1.0 inches**: Generous margins
- **1.25-1.5 inches**: Extra spacious

#### Drop Caps
- **Enable**: Test decorative first letters
- **Disable**: Standard paragraph formatting

#### Structure Detection
- **Regex-based** (Free): Basic document parsing
- **AI-powered**: Enhanced detection (requires OpenAI API key)

### Step 3: Generate & Validate
1. Click **"Generate & Validate"**
2. Wait for processing to complete (shows progress bar)
3. Review **validation status** (PASS/WARNING/FAIL counts)
4. Click **"Preview PDF"** to open the preview page

### Step 4: Manual Inspection
Use the enhanced PDF preview to manually verify formatting:

#### Navigation & Zoom
- Use **arrow keys** or click Previous/Next for page navigation
- **Zoom presets**: 50%, 75%, 100%, 125%, 150%
- **Jump to Page**: Enter page number and press Enter or click "Go"
- **Keyboard shortcuts**: +/- for zoom, 0 for 100%, F for fullscreen

## Formatting Verification Checklist

When testing generated PDFs, verify the following KDP formatting standards:

### Paragraph Formatting
- [ ] First paragraph after chapter title has NO indentation
- [ ] First paragraph after any heading (H1, H2, H3) has NO indentation
- [ ] Subsequent paragraphs have 0.25in first-line indentation
- [ ] No spacing between paragraphs (indentation only)
- [ ] Text is justified (aligned to both left and right margins)

### Drop Caps (if enabled)
- [ ] Large first letter does NOT overlap with text below
- [ ] Drop cap has proper spacing from adjacent text
- [ ] Drop cap aligns properly with paragraph margin

### Page Breaks and Flow
- [ ] Chapters start on new pages
- [ ] No single-line orphans at bottom of pages
- [ ] No single-line widows at top of pages
- [ ] Headings are not separated from following paragraphs
- [ ] No pages with only one line of text

### Margins and Layout
- [ ] All margins are consistent (default: 0.75in)
- [ ] Page size is correct (default: 6" x 9")
- [ ] Text does not extend into margin areas
- [ ] Page numbers are centered and properly positioned

## Common Formatting Issues and Solutions

### Issue: All paragraphs are indented (including first paragraphs)
**Cause**: CSS specificity issue or browser caching
**Solution**:
- Clear browser cache and regenerate PDF
- Verify `poc/styles.css` has correct first-paragraph rules
- Check that `.first-para` class is applied in generated HTML

### Issue: Drop cap overlaps text below
**Cause**: Drop cap font-size too large or line-height too small
**Solution**:
- Disable drop caps in UI settings
- Or adjust drop cap CSS in `poc/styles.css`

### Issue: Too much spacing between paragraphs
**Cause**: Paragraph margin-bottom set incorrectly
**Solution**: Verify `poc/styles.css` has `margin: 0;` for paragraphs

### Step 5: Download & External Testing
1. **Download PDF** for KDP Preview testing
2. **Upload to KDP Preview** tool
3. **Compare results** with web UI validation
4. **Test on different devices** (tablet, phone if applicable)

## Specific Test Cases

### Test Case 1: Basic Paragraph Formatting
- **File**: `test_data/sample_short.txt`
- **Settings**: Page size 6x9, Margins 0.75", Drop caps OFF
- **Expected**: Clean paragraph indentation, no orphans/widows

### Test Case 2: Drop Caps Validation
- **File**: `test_data/sample_short.txt`
- **Settings**: Page size 6x9, Margins 0.75", Drop caps ON
- **Expected**: First chapter letter enlarged, no text overlap

### Test Case 3: Margin Testing
- **File**: `test_data/sample_medium.txt`
- **Settings**: Page size 8.5x11, Margins 0.5", Drop caps OFF
- **Expected**: Tight margins, text fits properly

### Test Case 4: Formatting Test Endpoint
- **URL**: http://localhost:8001/formatting-test
- **Settings**: Query parameters `?use_drop_caps=true&page_size=6x9&margins=0.75`
- **Expected**: Pre-built test document with known formatting patterns

### Test Case 5: Long Document Stress Test
- **File**: `test_data/sample_long.pdf` (convert to text first if needed)
- **Settings**: Page size 6x9, Margins 0.75", Drop caps ON
- **Expected**: Proper page breaks, no formatting degradation

## Using the Formatting Test Endpoint

The `/formatting-test` endpoint generates a test PDF with known formatting patterns:

```bash
# Generate test PDF with default settings
curl "http://localhost:8001/formatting-test"

# Generate test PDF with drop caps enabled
curl "http://localhost:8001/formatting-test?use_drop_caps=true"

# Generate test PDF with custom page size and margins
curl "http://localhost:8001/formatting-test?page_size=8.5x11&margins=1.0"
```

The test PDF includes:
- Basic paragraph indentation patterns
- Drop cap examples (if enabled)
- Multiple heading levels
- Long content for page break testing

Use this to quickly verify formatting changes without uploading files.

## Formatting Verification Details

### Paragraph Indentation Rules
The CSS implements these indentation rules:
```css
/* First paragraph after heading - no indent */
.chapter p:first-of-type,
h1 + p, h2 + p, h3 + p {
    text-indent: 0;
}

/* Subsequent paragraphs - 0.25in indent */
.chapter p {
    text-indent: 0.25in;
}
```

### Drop Caps Implementation
```css
/* Drop caps styling */
.chapter.use-drop-caps p:first-of-type::first-letter {
    font-size: 3em;
    float: left;
    margin-right: 0.1em;
    margin-top: 0.05em;
    line-height: 0.8;
}
```

### Orphan/Widow Control
CSS rules prevent single lines:
```css
p {
    orphans: 2;    /* Minimum 2 lines at page bottom */
    widows: 2;     /* Minimum 2 lines at page top */
}
```

## Troubleshooting

### Server Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check if port is in use
lsof -i :8001

# Kill process using port
kill -9 <PID>

# Alternative port
uvicorn app.main:app --host localhost --port 8002 --reload
```

### File Upload Issues
- **File too large**: Maximum 50MB
- **Unsupported format**: Only .txt, .pdf, .docx, .md allowed
- **Permission denied**: Check write access to `app/output/` directory

### PDF Generation Fails
- **Missing WeasyPrint**: `pip install weasyprint`
- **Font issues**: Check font files in `poc/fonts/`
- **CSS errors**: Review `poc/styles.css` syntax

### Validation Errors
- **Expected failures**: Some checks may fail during development
- **False positives**: PDF validation is conservative
- **Missing fonts**: Ensure fonts are properly embedded

### Performance Issues
- **Large files**: Split into smaller documents for testing
- **Memory usage**: Monitor with `top` or Activity Monitor
- **Slow rendering**: Reduce PDF complexity for quick iterations

## Known Issues & Limitations

### Current Limitations
- PDF validation is basic - focuses on structure over content
- AI detection requires OpenAI API key and credits
- Large documents (>10MB) may be slow to process
- Some complex formatting may not render perfectly

### Common False Positives
- Validation may flag formatting that's actually correct
- PDF text extraction can be imperfect
- Font rendering differences between systems

### Development Notes
- Sessions auto-cleanup after 1 hour
- Files stored in `app/output/` directory
- Logs available in terminal output
- Use browser dev tools for debugging

## Integration Testing

### With KDP Preview Tool
1. Generate PDF using web UI
2. Upload to [KDP Preview](https://kdp.amazon.com/en_US/preview)
3. Compare formatting with web UI checklist
4. Note any discrepancies for bug reports

### With Different Browsers
- Test Chrome, Firefox, Safari, Edge
- Verify PDF.js compatibility
- Check mobile responsiveness

### With Different Input Formats
- Plain text (.txt) - most reliable
- Markdown (.md) - structured content
- Word documents (.docx) - complex formatting
- PDFs (.pdf) - text extraction quality varies

## Quick Reference

### URLs
- **Main UI**: http://localhost:8001
- **Formatting Test**: http://localhost:8001/formatting-test
- **Health Check**: http://localhost:8001/health

### Keyboard Shortcuts (PDF Preview)
- **←/→**: Previous/Next page
- **+/-**: Zoom in/out
- **0**: Reset zoom to 100%
- **F**: Toggle fullscreen

### Test Files
- `test_data/sample_short.txt` - Basic formatting
- `test_data/sample_medium.txt` - Comprehensive test
- `test_data/sample_long.docx` - Performance test

### Configuration Presets
- **Standard KDP**: 6x9, 0.75" margins, drop caps off
- **Drop Caps Test**: 6x9, 0.75" margins, drop caps on
- **Tight Margins**: 6x9, 0.5" margins, drop caps off
- **Large Format**: 8.5x11, 1.0" margins, drop caps off

This testing protocol ensures consistent verification of formatting fixes across different scenarios and configurations.
