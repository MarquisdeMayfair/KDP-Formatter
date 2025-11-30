# KDP Preview Testing Protocol

This document provides a comprehensive testing protocol for validating both PDF and EPUB outputs from the KDP Formatter POC with KDP Preview and Kindle Previewer, ensuring production-ready quality before moving to full implementation.

## Introduction

### Purpose
This protocol ensures that generated manuscripts meet KDP's quality standards and formatting requirements. Automated validation provides technical compliance, but manual KDP Preview testing is essential for verifying real-world publishing compatibility.

### Why Manual Testing Matters
- **KDP Preview** reveals formatting issues invisible to automated tools
- **Device simulation** shows how content appears on actual e-readers
- **Enhanced Typesetting** verification requires manual inspection
- **Print quality** assessment needs human judgment

### Testing Tools Overview
- **KDP Preview**: Browser-based testing for both PDF and EPUB uploads
- **Kindle Previewer 3**: Desktop application for EPUB device simulation
- **epubcheck**: Automated EPUB validation (integrated into POC)

## Prerequisites

### Account Setup
- [ ] Valid KDP account with publishing permissions
- [ ] Test manuscript prepared (avoid real book uploads)
- [ ] Browser compatibility verified (Chrome/Firefox recommended)

### Software Installation
- [ ] Kindle Previewer 3 installed (Windows/Mac only)
  - Download: https://kdp.amazon.com/en_US/help/topic/G202131170
- [ ] epubcheck installed for automated validation
- [ ] POC scripts tested and generating valid outputs

### Test Manuscript Preparation
- [ ] Diverse content types: fiction, non-fiction, academic
- [ ] Include front matter, back matter, footnotes
- [ ] Various chapter structures and heading levels
- [ ] Special characters, quotes, and formatting elements
- [ ] Different word counts (short/medium/long)

## PDF Testing Protocol

### Pre-Upload Preparation
1. **Generate PDF** using POC script
2. **Run validation** with integrated PDF validator
3. **Check file size** (< 500MB for KDP)
4. **Verify fonts** are embedded
5. **Confirm metadata** is present

### KDP Preview Upload Steps
1. Log into KDP (https://kdp.amazon.com)
2. Navigate to "Bookshelf" → "Create a New Title"
3. Select "Paperback" (or appropriate format)
4. Upload manuscript PDF when prompted
5. Wait for processing (may take several minutes)

### What to Check in KDP Preview

#### Upload Status
- [ ] File uploads successfully without errors
- [ ] Processing completes without warnings
- [ ] Preview generates correctly

#### Page Layout Verification
- [ ] **Margins**: Standard KDP margins (0.75" top/bottom, 0.75" inside, 0.5" outside)
- [ ] **Page size**: Correct trim size (6x9, 8.5x11, etc.)
- [ ] **Bleed**: Proper bleed setup if applicable
- [ ] **Gutter**: Adequate space for binding

#### Typography Assessment
- [ ] **Font embedding**: All fonts render correctly
- [ ] **Font size**: Appropriate for print (10-12pt body text)
- [ ] **Line spacing**: Consistent and readable
- [ ] **Kerning/tracking**: Proper character spacing

#### Chapter Formatting
- [ ] **Chapter breaks**: Proper page breaks between chapters
- [ ] **Chapter titles**: Consistent formatting and positioning
- [ ] **Running headers**: Present with title/author/page numbers
- [ ] **Page numbering**: Correct sequence and positioning

#### Content Flow
- [ ] **Paragraph indents**: First-line indents on body paragraphs
- [ ] **Text alignment**: Proper justification or left alignment
- [ ] **Widow/orphan control**: No single lines at page breaks
- [ ] **Hyphenation**: Appropriate word breaks

#### Print-Specific Issues
- [ ] **Image quality**: High-resolution images if present
- [ ] **Color accuracy**: Proper color reproduction
- [ ] **Paper simulation**: "Standard Color Paper" option selected

### PDF Pass/Fail Criteria

#### Pass Criteria
- All formatting elements render correctly
- No text cutoff or overflow issues
- Consistent typography throughout
- Professional appearance suitable for publishing

#### Fail Criteria
- Critical layout issues (text cutoff, wrong page size)
- Font rendering problems
- Major spacing or alignment issues
- File upload failures

## EPUB Testing Protocol

### Pre-Upload Preparation
1. **Generate EPUB** using POC script with `--epub` flag
2. **Run epubcheck** validation (integrated or manual)
3. **Test with Kindle Previewer** (required for device simulation)
4. **Verify file size** and structure
5. **Check metadata** and navigation

### Kindle Previewer 3 Testing Steps

#### Installation and Setup
1. Download and install Kindle Previewer 3
2. Launch application and accept terms
3. Select appropriate device profiles for testing

#### File Loading
1. Open EPUB file: File → Open Book → From Disk
2. Wait for processing and rendering
3. Check for any loading errors or warnings

#### Device Simulation Testing
Test on multiple device profiles:
- **Phone**: Small screens, portrait orientation
- **Tablet**: Medium screens, landscape/portrait
- **E-reader**: Dedicated reading devices (Kindle, etc.)

### Visual Inspection Checklist

#### Basic Display
- [ ] **Title page**: Correct title and author display
- [ ] **Table of contents**: Hierarchical navigation structure
- [ ] **Chapter navigation**: Proper section breaks and titles
- [ ] **Font rendering**: Source Serif 4 displays correctly

#### Content Layout
- [ ] **Text reflow**: Content adapts to different screen sizes
- [ ] **Paragraph spacing**: Consistent margins and line heights
- [ ] **Heading hierarchy**: Clear visual distinction between levels
- [ ] **Quote formatting**: Blockquotes and attributions display properly

#### Navigation Features
- [ ] **TOC navigation**: All links work correctly
- [ ] **Page turning**: Smooth transitions between sections
- [ ] **Progress indicator**: Reading progress shows accurately
- [ ] **Search function**: Text search works properly

### Functionality Testing

#### Footnotes/Endnotes
- [ ] **Endnote section**: Footnotes converted to endnotes
- [ ] **Backlinks**: Links from endnotes to reference locations
- [ ] **Navigation**: Easy access between content and notes
- [ ] **Formatting**: Endnotes clearly distinguished from main text

#### Interactive Elements
- [ ] **Bookmarks**: Can set and navigate to bookmarks
- [ ] **Highlights**: Text selection and highlighting works
- [ ] **Notes**: Can add personal notes if supported
- [ ] **Dictionary**: Word lookup functions properly

### Content Verification

#### Text Integrity
- [ ] **Complete content**: All original text preserved
- [ ] **Special characters**: Unicode symbols display correctly
- [ ] **Formatting preservation**: Italics, emphasis maintained
- [ ] **Paragraph structure**: Proper breaks and spacing

#### Enhanced Typesetting
- [ ] **ET activation**: Enhanced Typesetting enabled in KDP
- [ ] **Font consistency**: Professional typography maintained
- [ ] **Layout quality**: Refined spacing and alignment
- [ ] **Reading experience**: Smooth, book-like presentation

### KDP Preview Upload Steps (EPUB)

1. Log into KDP account
2. Create new title or edit existing
3. Select "Kindle" format (not Print)
4. Upload EPUB file in manuscript section
5. Enable "Enhanced Typesetting" if available
6. Wait for processing and preview generation

### KDP Preview EPUB Verification

#### Upload Success
- [ ] File uploads without errors
- [ ] Processing completes successfully
- [ ] Preview generates correctly
- [ ] Enhanced Typesetting activates

#### Content Display
- [ ] **Title metadata**: Correct title/author/ISBN display
- [ ] **Cover integration**: Proper cover display (if applicable)
- [ ] **TOC functionality**: Table of contents works in preview
- [ ] **Sample pages**: Content displays correctly in sample

#### Formatting Quality
- [ ] **Font rendering**: Source Serif 4 displays consistently
- [ ] **Text flow**: Proper reflow and spacing
- [ ] **Chapter breaks**: Clear section divisions
- [ ] **Navigation**: TOC and internal links work

## Comparative Testing

### PDF vs EPUB Comparison
Perform side-by-side testing to document differences:

#### Content Parity
- [ ] **Text accuracy**: Both formats contain identical content
- [ ] **Structure preservation**: Chapters, headings, quotes match
- [ ] **Metadata consistency**: Title, author, ISBN identical

#### Format-Specific Advantages
- **PDF Strengths**:
  - Pixel-perfect control
  - Print-ready formatting
  - Consistent across devices
- **EPUB Strengths**:
  - Reflowable text
  - Device adaptation
  - Enhanced navigation features

#### Performance Metrics
- **File sizes**: Compare PDF vs EPUB sizes
- **Generation time**: Document processing differences
- **Validation complexity**: PDF vs EPUB validation effort

## Issue Documentation

### How to Document Issues
1. **Screenshot capture**: Take screenshots of problems
2. **Issue categorization**: Classify as blocker/major/minor
3. **Reproduction steps**: Document how to reproduce
4. **Environment details**: Note testing device/browser

### Screenshot Naming Convention
- `pdf_preview_margin_issue.png`
- `epub_kindle_font_rendering.png`
- `toc_navigation_broken.png`

### Issue Severity Classification
- **Blocker**: Prevents publishing (upload failures, major layout issues)
- **Major**: Significant quality issues (font problems, navigation failures)
- **Minor**: Cosmetic issues (spacing inconsistencies, small alignment problems)

### Results Recording Location
- Primary documentation: `docs/poc_results.md`
- Issue tracking: GitHub issues or dedicated bug tracking
- Screenshots: `docs/screenshots/` directory

## Test Cases

### Minimum Test Set (Required)
1. **Short fiction** (< 10k words): Basic chapter structure
2. **Medium non-fiction** (20-50k words): Complex formatting
3. **Academic text** (with footnotes, references)
4. **Mixed content** (front/back matter, multiple heading levels)

### Comprehensive Test Set (Recommended)
1. **Children's book**: Large fonts, simple structure
2. **Poetry collection**: Unusual formatting requirements
3. **Technical manual**: Tables, code blocks, complex hierarchy
4. **Multilingual content**: Unicode and special characters

## Acceptance Criteria

### POC Validation Success
- [ ] All test files generate without errors
- [ ] Automated validation passes for both formats
- [ ] KDP Preview accepts uploads without critical errors
- [ ] Kindle Previewer displays content correctly
- [ ] No blocker-level issues identified

### Production Readiness Thresholds
- **PDF**: < 5% failure rate across test cases
- **EPUB**: < 10% failure rate (due to format complexity)
- **KDP Preview**: All uploads successful
- **Kindle Previewer**: Content readable on all device profiles

## Troubleshooting

### Common KDP Preview Issues

#### Upload Failures
- **File size**: Ensure under format limits (PDF: 500MB, EPUB: variable)
- **Corrupt files**: Regenerate if upload consistently fails
- **Metadata issues**: Check title/author/ISBN requirements
- **Browser problems**: Try different browser or incognito mode

#### Display Problems
- **Font rendering**: Check font embedding in source files
- **Layout issues**: Verify CSS compatibility with KDP requirements
- **Image problems**: Ensure images meet resolution requirements
- **Encoding issues**: Check UTF-8 encoding for special characters

### Kindle Previewer Issues

#### Installation Problems
- **Java requirements**: Ensure correct Java version installed
- **Permissions**: Run as administrator on Windows
- **Antivirus interference**: Temporarily disable during installation

#### File Loading Issues
- **EPUB validity**: Run epubcheck to verify file integrity
- **Size limits**: Check for oversized individual files
- **Corrupt EPUB**: Regenerate if Previewer refuses to load

### When to Regenerate Files
- **Source changes**: Any modifications to POC code
- **Font updates**: Font embedding or licensing changes
- **CSS modifications**: Styling changes affecting layout
- **Validation failures**: Address root causes before re-uploading

## Appendix

### KDP Resources
- **KDP Help Center**: https://kdp.amazon.com/en_US/help
- **Publishing Guidelines**: https://kdp.amazon.com/en_US/help/topic/G200672170
- **Enhanced Typesetting**: https://kdp.amazon.com/en_US/help/topic/G202101680

### Kindle Previewer Resources
- **Download Page**: https://kdp.amazon.com/en_US/help/topic/G202131170
- **User Guide**: Included with installation
- **Troubleshooting**: KDP community forums

### epubcheck Resources
- **Official Site**: https://www.w3.org/publishing/epubcheck/
- **GitHub Repository**: https://github.com/w3c/epubcheck
- **Usage Guide**: Command-line documentation

### KDP Publishing Guidelines References
- **PDF Requirements**: https://kdp.amazon.com/en_US/help/topic/G201953020
- **EPUB Requirements**: https://kdp.amazon.com/en_US/help/topic/G202101640
- **Enhanced Typesetting**: https://kdp.amazon.com/en_US/help/topic/G202101680

---

This protocol ensures comprehensive validation of both PDF and EPUB outputs, providing confidence in production readiness. Regular updates to this document should reflect changes in KDP requirements and testing procedures.

