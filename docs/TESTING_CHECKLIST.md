# KDP Formatter Testing Checklist

## Pre-Testing Setup
- [ ] Localhost web UI running (http://localhost:8001)
- [ ] Test files ready in `test_data/`
- [ ] Output directory created: `output/test_results/`
- [ ] PDF viewer installed (Adobe Acrobat or Preview.app)
- [ ] KDP Preview account accessible
- [ ] Documentation template open: `docs/poc_results.md`

## Automated Testing (CLI)
- [ ] Run `bash scripts/run_comprehensive_tests.sh`
- [ ] Verify all PDFs generated successfully
- [ ] Review validation reports for each PDF
- [ ] Check for any errors or warnings
- [ ] Document AI costs (if applicable)

## Manual Testing (Web UI)
- [ ] Test file upload (drag & drop)
- [ ] Test each configuration option:
  - [ ] Page size: 6x9
  - [ ] Page size: 8.5x11
  - [ ] Margins: 0.5", 0.75", 1.0"
  - [ ] Drop caps: enabled
  - [ ] Drop caps: disabled
  - [ ] AI detection: enabled
  - [ ] AI detection: disabled
  - [ ] EPUB generation: enabled
  - [ ] EPUB generation: disabled
- [ ] Verify PDF preview loads correctly
- [ ] Test zoom and navigation controls
- [ ] Download and inspect generated files

## Visual Inspection (Each PDF)
- [ ] **Drop Caps** (if enabled):
  - [ ] No overlap with adjacent text
  - [ ] Proper spacing (0.15em margin)
  - [ ] Aligned within margins
- [ ] **Paragraph Indentation**:
  - [ ] First paragraph after chapter: NO indent
  - [ ] First paragraph after headings: NO indent
  - [ ] Subsequent paragraphs: 0.25" indent
  - [ ] Multi-line paragraphs aligned correctly
- [ ] **Page Breaks**:
  - [ ] Each chapter starts on new page
  - [ ] No single-line orphans (min 3 lines)
  - [ ] No single-line widows (min 3 lines)
  - [ ] Headings not separated from content
- [ ] **Margins**:
  - [ ] Top margin: 0.75" (or configured)
  - [ ] Bottom margin: 0.75" (or configured)
  - [ ] Left margin: 0.75" (or configured)
  - [ ] Right margin: 0.75" (or configured)
  - [ ] Consistent throughout document
- [ ] **Typography**:
  - [ ] Fonts render clearly
  - [ ] Line spacing consistent (1.4)
  - [ ] Text justified properly
  - [ ] No awkward hyphenation

## KDP Preview Upload
- [ ] Upload PDF to KDP Preview
- [ ] Wait for KDP validation to complete
- [ ] Review KDP validation messages
- [ ] Check for any KDP-specific warnings
- [ ] Test PDF in KDP Previewer tool
- [ ] Verify formatting on different devices (phone, tablet, e-reader)

## Documentation
- [ ] Fill in test results in `docs/poc_results.md`
- [ ] Add screenshots to `output/test_results/screenshots/`
- [ ] Document any issues found
- [ ] Record KDP Preview feedback
- [ ] Update summary statistics
- [ ] Note any action items or improvements needed

## Final Assessment
- [ ] All tests completed successfully
- [ ] No critical formatting issues
- [ ] KDP Preview validation passed
- [ ] Documentation complete
- [ ] Ready for deployment

---

**Notes:**
- Mark each item as you complete it
- Document any issues immediately
- Take screenshots of problems for reference
- If any critical issues found, stop and fix before proceeding

