# KDP Formatter Manual Testing Guide

This comprehensive guide walks through the visual inspection process for KDP formatting validation. Use this guide alongside the web UI at `http://localhost:8001` to systematically test and document formatting issues.

## Prerequisites

### Localhost Web UI Running
- Start the web interface: `bash scripts/start_localhost.sh`
- Access at: `http://localhost:8001`
- Verify server health by checking the health endpoint

### Test Files Ready
- `test_data/sample_short.txt` (524 lines) - Quick validation tests
- `test_data/sample_medium.txt` (300 lines) - Medium complexity
- `test_data/sample_nonfiction.txt` - Non-fiction formatting tests

### Tools Required
- **PDF Viewer**: Adobe Acrobat or Preview.app for margin measurements
- **KDP Preview Account**: Amazon KDP access for official validation
- **Browser**: Modern browser with PDF.js support for web UI

### Documentation Setup
- `docs/poc_results.md` - Test results template
- `output/test_results/` - Directory for screenshots and reports
- Screenshot naming convention: `[test_name]_[issue]_[before|after].png`

## Testing Workflow

### Step 1: Automated Testing
```bash
# Run comprehensive automated tests
bash scripts/run_comprehensive_tests.sh

# Review generated files
ls -lh output/test_results/
```

### Step 2: Web UI Testing
1. **Navigate to Web UI**: Open `http://localhost:8001`
2. **Upload Test File**: Drag and drop a manuscript file
3. **Configure Options**:
   - Page size: 6x9 or 8.5x11
   - Margins: 0.5", 0.75", 1.0"
   - Drop caps: enabled/disabled
   - AI detection: enabled/disabled
   - EPUB generation: enabled/disabled
4. **Generate PDF**: Click "Generate PDF" button
5. **Inspect Results**: Use the PDF preview and validation report

### Step 3: Visual Inspection
Use the checklists below to systematically inspect each PDF.

### Step 4: KDP Preview Upload
1. Log in to KDP account
2. Navigate to KDP Preview tool
3. Upload generated PDF
4. Review validation messages
5. Test on different devices
6. Document results

### Step 5: Documentation
Fill out results in `docs/poc_results.md` following the provided templates.

## Visual Inspection Checklist

### Drop Cap Rendering (if enabled)

Drop caps should be exactly 3x larger than body text with proper spacing.

**What to Check:**
- [ ] First letter is 3x larger than surrounding text
- [ ] No overlap with adjacent text or paragraphs
- [ ] Proper spacing and alignment within margins
- [ ] Consistent rendering across all chapters

**Correct Drop Cap Examples:**
- Letter extends 2-3 lines down
- 0.15em margin between drop cap and text
- Aligned with first line of paragraph
- No interference with paragraph flow

**Common Issues:**
- Drop cap too small (< 2.5x text size)
- Overlap with adjacent text
- Poor spacing (too close/far from text)
- Alignment issues within margins

**Screenshot Examples:**
- `drop_cap_correct.png` - Shows proper 3x sizing and spacing
- `drop_cap_overlap.png` - Shows text overlap issue
- `drop_cap_spacing.png` - Shows margin measurement

### Paragraph Indentation

Critical for professional book formatting.

**What to Check:**
- [ ] First paragraph after chapter title: NO indent (flush left)
- [ ] First paragraph after any heading: NO indent (flush left)
- [ ] All subsequent paragraphs: exactly 0.25" indent
- [ ] Multi-line paragraphs maintain consistent alignment
- [ ] No extra spacing between paragraphs

**Measurement Method:**
1. Use PDF ruler tool in Acrobat/Preview
2. Measure from left margin to first line of text
3. Verify 0.25" = 18pt indent (at 72 DPI)

**Correct Indentation Examples:**
```
Chapter 1                    ← No indent
   This is the first paragraph of the chapter.
   This is the second paragraph with 0.25" indent.
   This continues the paragraph with same indent.

Section Header               ← No indent
   First paragraph after header.
   Second paragraph with indent.
```

**Common Issues:**
- First paragraphs incorrectly indented
- Inconsistent indent amounts
- Mixed indent styles in same document

**Screenshot Examples:**
- `indentation_correct.png` - Shows proper 0.25" indents
- `indentation_missing.png` - Shows missing indents after headings
- `indentation_inconsistent.png` - Shows varying indent amounts

### Page Breaks and Flow

Ensures professional reading experience.

**What to Check:**
- [ ] Each chapter starts on new page
- [ ] No single-line orphans (minimum 3 lines at page bottom)
- [ ] No single-line widows (minimum 3 lines at page top)
- [ ] Headings not separated from following content
- [ ] Proper page flow and spacing

**Widow/orphan Rules:**
- **Widow**: Single line at top of page → pull up to previous page
- **Orphan**: Single line at bottom of page → push down to next page
- Minimum 3 lines required on each page

**Common Issues:**
- Chapters not starting on new pages
- Single lines stranded at page boundaries
- Headings appearing alone at bottom of pages

**Screenshot Examples:**
- `page_breaks_good.png` - Shows proper chapter breaks
- `widow_orphan_fixed.png` - Shows corrected line distribution
- `widow_orphan_issue.png` - Shows problematic single lines

### Margins

Must be exactly 0.75" (or configured value) on all sides.

**What to Check:**
- [ ] Top margin: exactly configured value (default 0.75")
- [ ] Bottom margin: exactly configured value (default 0.75")
- [ ] Left margin: exactly configured value (default 0.75")
- [ ] Right margin: exactly configured value (default 0.75")
- [ ] Consistent throughout entire document
- [ ] Text starts exactly at margin edge (no extra spacing)

**Measurement Method:**
1. Use PDF ruler tool (View → Show Ruler in Acrobat)
2. Measure from page edge to text/content
3. Verify measurements in inches or millimeters
4. Check multiple pages for consistency

**Common Issues:**
- Margins too narrow (< 0.75" may fail KDP)
- Margins too wide (> 0.75" reduces content area)
- Inconsistent margins between pages
- Extra spacing/padding affecting margins

**Screenshot Examples:**
- `margins_measured.png` - Shows ruler measuring 0.75" margins
- `margins_inconsistent.png` - Shows varying margin sizes
- `margins_too_narrow.png` - Shows margins under 0.75"

### Typography

Ensures readable, professional appearance.

**What to Check:**
- [ ] Font rendering clear and professional
- [ ] Line spacing consistent (1.4 line-height recommended)
- [ ] Text properly justified (no awkward spacing)
- [ ] No hyphenation issues or awkward breaks
- [ ] Consistent font sizing throughout

**Typography Standards:**
- Line height: 1.4 (140% of font size)
- Font: Serif for body text (Source Serif 4 recommended)
- Justification: Full justification with proper spacing
- Hyphenation: Minimal, only when necessary

**Common Issues:**
- Font rendering problems
- Inconsistent line spacing
- Poor text justification
- Excessive hyphenation

## KDP Preview Upload Protocol

### Upload Process
1. **Log in**: Access your KDP account
2. **Navigate**: Go to "KDP Preview" tool
3. **Upload**: Select and upload generated PDF
4. **Wait**: Allow KDP validation to complete
5. **Review**: Check validation messages and warnings

### KDP Validation Checks
KDP checks for:
- **File Format**: Valid PDF structure
- **Margins**: Must meet minimum requirements
- **Fonts**: Embedded and readable
- **Page Breaks**: Proper flow and formatting
- **Content**: No prohibited content
- **Metadata**: Title, author, ISBN if applicable

### Common KDP Rejection Reasons
- **Margins too small**: Under 0.75" minimum
- **Missing fonts**: Fonts not embedded properly
- **Page formatting issues**: Improper breaks or spacing
- **File corruption**: Invalid PDF structure
- **Content issues**: Prohibited material

### Device Testing
Test PDFs on different devices:
- **Phone**: Small screen readability
- **Tablet**: Medium screen formatting
- **E-reader**: Dedicated reading device
- **Desktop**: Full preview experience

## Documentation Template

### How to Fill Test Results

Use this format in `docs/poc_results.md`:

```markdown
### Test X: [filename] - [configuration]
**Date**: YYYY-MM-DD
**Input**: test_data/[filename]
**Output**: output/test_results/[filename]
**Configuration**: [details]

#### Pre-Upload Validation
- File Size: X KB/MB
- Page Count: X pages
- Validation Status: Pass/Warning/Fail
- Issues Found: [list]

#### KDP Preview Results
- Upload Status: Success/Failed
- KDP Validation: Pass/Issues
- Formatting Quality: Excellent/Good/Needs Work
- Screenshots: [references]

**Overall Assessment**: [summary]
**Action Items**: [if any]
```

### Screenshot Naming Conventions

Store screenshots in `output/test_results/screenshots/`:

- `sample_short_dropcap_correct.png`
- `sample_medium_indentation_issue.png`
- `sample_nonfiction_margins_before.png`
- `sample_nonfiction_margins_after.png`
- `kdp_validation_pass.png`
- `kdp_validation_warnings.png`

### Where to Store Files

- **Test PDFs**: `output/test_results/`
- **Screenshots**: `output/test_results/screenshots/`
- **Validation Reports**: `output/test_results/` (auto-generated)
- **Test Results**: `docs/poc_results.md`

## Troubleshooting

### Common Formatting Issues

**Drop Caps Overlapping Text:**
- CSS issue: Check `line-height` and `margin-right` properties
- Fix: Adjust drop cap CSS in `poc/styles.css`
- Test: Regenerate and re-inspect

**Incorrect Paragraph Indentation:**
- Selector issue: Check CSS specificity for paragraph rules
- Fix: Update indentation selectors in styles
- Test: Verify with ruler tool in PDF viewer

**Page Break Problems:**
- CSS issue: Check `page-break-before/after` rules
- Fix: Adjust page break CSS properties
- Test: Inspect page flow manually

**Margin Inconsistencies:**
- CSS issue: Check `@page` margin rules
- Fix: Update page margin CSS
- Test: Measure with PDF ruler tool

### When to Adjust CSS vs Content

**Adjust CSS when:**
- Issue affects all instances (indentation, margins)
- Issue is styling-related (fonts, spacing)
- Issue is consistent across document

**Adjust Content when:**
- Issue is content-specific (manual page break needed)
- Issue requires content restructuring
- Issue is semantic (heading levels)

### Reporting Bugs

**For CSS/Styling Issues:**
1. Document the issue with screenshots
2. Note affected files and configurations
3. Describe expected vs actual behavior
4. Provide PDF ruler measurements

**For Validation Issues:**
1. Include validation report output
2. Note KDP Preview error messages
3. Provide device testing results
4. Document reproduction steps

### Performance Issues

**Slow PDF Generation:**
- Check file size and complexity
- Verify font loading
- Review CSS efficiency

**Web UI Loading Issues:**
- Check browser console for errors
- Verify server health endpoint
- Review network connectivity

**Memory Usage:**
- Monitor system resources during generation
- Check for memory leaks in long sessions
- Consider file size limits

