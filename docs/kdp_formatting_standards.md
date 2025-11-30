# KDP Formatting Standards Reference

This document provides comprehensive formatting standards for Amazon Kindle Direct Publishing (KDP) print-on-demand paperbacks.

## Page Setup

### Page Size
- **Standard**: 6" × 9" (most common for novels and non-fiction)
- **Alternative**: 8.5" × 11" (letter size, for workbooks/manuals)
- **Other sizes**: 5" × 8", 5.25" × 8", 5.5" × 8.5", 6" × 9", 6.14" × 9.21", 6.69" × 9.61", 7" × 10", 7.44" × 9.69", 7.5" × 9.25", 8" × 10", 8.25" × 6", 8.25" × 8.25", 8.5" × 8.5", 8.5" × 11"

### Margins
- **Minimum**: 0.5 inches on all sides
- **Standard**: 0.75 inches (recommended for most books)
- **Maximum**: 1.5 inches
- **Gutter**: Additional 0.125" - 0.25" for binding side (inside margin)

### Page Count
- **Minimum**: 24 pages for KDP paperback
- **Maximum**: 828 pages (varies by paper type and ink)

## Typography

### Body Text
- **Font Size**: 10-12pt (11pt recommended)
- **Font Family**: Professional serif fonts (Bookerly, Garamond, Baskerville, Crimson Text, Libre Baskerville)
- **Line Spacing**: 1.15 - 1.5 (1.4 recommended)
- **Text Alignment**: Justified (preferred) or left-aligned
- **Hyphenation**: Enabled with `hyphens: auto`

## Paragraph Formatting Standards

### Indentation Rules

KDP follows traditional book formatting conventions for paragraph indentation:

1. **First paragraph after chapter title**: NO indentation
   - The chapter title provides visual separation
   - Indentation would create awkward spacing

2. **First paragraph after any heading** (H1, H2, H3): NO indentation
   - Same principle as chapter titles
   - Headings provide sufficient visual break

3. **All subsequent paragraphs**: 0.2-0.25 inch first-line indentation
   - Standard indentation for professional books
   - Creates clear paragraph separation without spacing

4. **Front matter and back matter**: NO indentation
   - Copyright pages, dedications, etc. are typically centered
   - No indentation needed for these sections

### Spacing Rules

1. **Between paragraphs**: NO spacing
   - Traditional books use indentation only, not spacing
   - Spacing between paragraphs is a web/digital convention
   - KDP print books should follow print conventions

2. **Line height**: 1.4-1.5 times font size
   - Provides comfortable reading without excessive space
   - Standard for 11pt body text

### Why These Rules Matter

- **Professional appearance**: Matches reader expectations for print books
- **Page count optimization**: No wasted space from paragraph spacing
- **KDP compliance**: Follows Amazon's formatting guidelines
- **Print quality**: Ensures consistent appearance across devices

## Paragraph Formatting Options

The KDP Formatter provides three paragraph formatting styles to accommodate different publishing needs:

### 1. KDP Standard (Recommended for Print)
- **Indentation**: 0.25" first-line indentation on all paragraphs except after headings
- **Spacing**: No spacing between paragraphs (traditional book formatting)
- **Use Case**: Standard print books, novels, traditional publishing
- **KDP Compliance**: ✅ Fully compliant
- **Example**:
  ```
  Chapter Title

  First paragraph has no indentation because it follows
  the chapter title. Subsequent paragraphs have proper
  0.25" first-line indentation to create clear separation
  without wasting vertical space on the page.
  ```

### 2. Modern (Enhanced Readability)
- **Indentation**: 0.25" first-line indentation on all paragraphs except after headings
- **Spacing**: 0.5em spacing between paragraphs for improved readability
- **Use Case**: Digital-first books, modern publishing, accessibility
- **KDP Compliance**: ⚠️ May not meet traditional KDP guidelines but accepted
- **Example**:
  ```
  Chapter Title

  First paragraph has no indentation because it follows
  the chapter title.

  Subsequent paragraphs have proper 0.25" first-line
  indentation AND spacing between paragraphs for easier
  reading on screens.
  ```

### 3. No Indentation (Block Style)
- **Indentation**: No indentation on any paragraphs
- **Spacing**: 0.5em spacing between paragraphs for clear separation
- **Use Case**: Digital books, academic papers, modern web-style formatting
- **KDP Compliance**: ⚠️ May not meet traditional KDP guidelines
- **Example**:
  ```
  Chapter Title

  First paragraph has no indentation and no spacing after
  chapter title.

  Subsequent paragraphs have no indentation but clear
  spacing between paragraphs for modern readability.
  This style is common in digital publishing.
  ```

### Headings
- **Chapter Titles**: 16-18pt, bold, centered
- **Section Headings (H2)**: 14pt, bold
- **Subsection Headings (H3)**: 12pt, bold
- **Spacing**: 1.5-2em above, 1-1.5em below

## Page Breaks and Flow Control

### Chapter Breaks
- **Rule**: Each chapter MUST start on a new page
- **CSS**: `page-break-before: always` on `.chapter` class
- **Recto/Verso**: Optionally start chapters on right-hand pages (recto)

### Orphan and Widow Control
- **Orphans**: Minimum 3 lines at bottom of page
- **Widows**: Minimum 3 lines at top of page
- **CSS**: `orphans: 3; widows: 3;` on body and paragraph elements
- **Purpose**: Prevents unprofessional single-line pages

### Heading Protection
- **Rule**: Headings should not be orphaned at bottom of pages
- **CSS**: `page-break-after: avoid` on all heading elements
- **Purpose**: Keeps headings with their following content

### Paragraph Breaks
- **Rule**: Avoid breaking paragraphs mid-content when possible
- **CSS**: `page-break-inside: avoid` on paragraph elements
- **Note**: May be overridden for very long paragraphs

## Font Requirements

### Embedding
- **Requirement**: ALL fonts must be embedded in PDF
- **Validation**: Use `pdffonts` tool to verify embedding
- **Subset**: Fonts can be subset to reduce file size

### Recommended Fonts
- **Serif**: Bookerly, Garamond, Baskerville, Crimson Text, Libre Baskerville, Georgia
- **Sans-Serif**: Arial, Helvetica (for headings/special elements only)
- **Avoid**: Decorative fonts, script fonts, Comic Sans

## Drop Cap Guidelines

Drop caps (large first letters) are optional decorative elements:

### When to Use Drop Caps
- Fiction books, especially literary fiction
- Chapter openings for visual interest
- Traditional or classic book styles

### When NOT to Use Drop Caps
- Non-fiction books (usually)
- Technical or academic books
- Books with frequent short chapters
- If they cause formatting issues

### Technical Requirements
- Font size: 2.5-3em (2.5-3 times normal text)
- Must not overlap with adjacent text
- Must align properly with paragraph margin
- Should span 2-3 lines of text
- Requires proper spacing (margin-right: 0.1em minimum)

### KDP Formatter Implementation
- Drop caps are DISABLED by default
- Enable via UI checkbox: "Use drop caps"
- Applied only to first paragraph of each chapter
- CSS class: `.chapter.use-drop-caps p:first-of-type:first-letter`

## Chapter Detection Patterns

The KDP Formatter automatically detects chapter beginnings using regex patterns. Proper chapter detection ensures correct first-paragraph indentation rules.

### Recognized Patterns

The system recognizes the following chapter heading formats:

- **Standard Chapters**: `Chapter 1`, `Chapter One`, `Chapter I`
- **Letters**: `Letter 1`, `Letter 2`, `Letter A` (fixes main issue with sample text)
- **Parts**: `Part 1`, `Part II`, `Part One`
- **Sections**: `Section 1`, `Section A`
- **Numbers**: `1.`, `I.`, `2.`, `II.`
- **Word Numbers**: `One.`, `Two.`, `Three.`

### Examples

**✅ Detected as Chapters:**
```
Chapter 1: The Beginning
Letter 2: My Thoughts
Part III: Advanced Topics
Section A: Introduction
1. Getting Started
I. Roman Numerals
```

**❌ Not Detected (use AI detection):**
```
The First Chapter    (no keyword)
My Letter to You     (no number/letter)
Beginning            (too generic)
```

### Formatting Guidelines

For reliable chapter detection:

1. **Use keywords**: Include "Chapter", "Letter", "Part", or "Section"
2. **Add numbers/letters**: Follow with numbers (1, 2, 3), Roman numerals (I, II, III), or letters (A, B, C)
3. **Consistent format**: Use the same pattern throughout your book
4. **Clear separation**: Put chapter titles on their own lines

### Troubleshooting

If chapters aren't detected:
- Check that the pattern matches the recognized formats above
- Try using AI detection mode for complex or non-standard formats
- Ensure chapter titles are on separate lines from body text
- Review the generated IDM JSON to verify chapter structure

### AI Detection Fallback

When regex detection fails, enable AI-powered structure detection:
- Uses GPT-4 to intelligently identify document structure
- Recognizes non-standard chapter formats
- More expensive but more accurate for complex documents
- Requires OpenAI API key

## File Requirements

### PDF Specifications
- **Version**: PDF 1.4 or later (PDF 1.7 recommended)
- **Color Space**: RGB or CMYK
- **Resolution**: 300 DPI minimum for images
- **File Size**: Maximum 500 MB
- **Compression**: Allowed, but maintain quality

### Metadata
- **Title**: Required
- **Author**: Required
- **ISBN**: Optional but recommended
- **Language**: Specify document language

## Validation Checklist

### Pre-Upload Checks
- [ ] Page size matches KDP requirements
- [ ] Margins are 0.5" - 1.5" on all sides
- [ ] All fonts are embedded
- [ ] Page count is 24 or more
- [ ] File size is under 500 MB
- [ ] PDF version is 1.4 or later

### Formatting Checks
- [ ] Paragraph indentation: 0.25" for body, 0" after headings (unless using "No Indentation" style)
- [ ] Paragraph spacing: None for KDP Standard (unless using "Modern" or "No Indentation" styles)
- [ ] Orphans/widows: Minimum 3 lines (orphans: 3, widows: 3 in CSS)
- [ ] Chapter breaks: Each chapter starts on new page
- [ ] Heading protection: No orphaned headings
- [ ] Drop caps (if used): No text overlap
- [ ] Text alignment: Consistent throughout
- [ ] Line spacing: Consistent and readable
- [ ] Chapter detection: All chapters properly identified (check for "Letter X", "Part X", etc.)

### Manual Verification (KDP Preview)
- [ ] Upload PDF to KDP Preview
- [ ] Check first 10 pages for formatting issues
- [ ] Verify chapter breaks are correct
- [ ] Check for text cutoff or overflow
- [ ] Verify drop caps render correctly (if used)
- [ ] Check page numbers and headers
- [ ] Review on different zoom levels

## Common Formatting Mistakes to Avoid

### ❌ Indenting first paragraphs after headings
**Wrong**: Every paragraph indented, including after chapter titles
**Right**: First paragraph after heading has no indent

### ❌ Adding spacing between paragraphs
**Wrong**: 1em margin-bottom on all paragraphs
**Right**: No spacing, indentation only (except first paragraph)

### ❌ Drop caps overlapping text
**Wrong**: font-size: 3em with line-height: 1.0
**Right**: font-size: 2.5em with line-height: 0.85 and proper margins

### ❌ Inconsistent margins
**Wrong**: Different margins on different pages
**Right**: Consistent 0.75in margins on all sides (or custom value)

### ❌ Single-line orphans/widows
**Wrong**: One line of paragraph at top/bottom of page
**Right**: Minimum 3 lines (orphans: 3; widows: 3;)

### Critical (Must Fix)
1. **Text Cutoff**: Content extending beyond margins
2. **Font Embedding**: Missing or non-embedded fonts
3. **Page Size**: Incorrect trim size
4. **Drop Cap Overlap**: Enlarged first letter overlapping text
5. **Minimum Page Count**: Fewer than 24 pages

### Major (Should Fix)
1. **Inconsistent Indentation**: Mixed indent styles
2. **Orphaned Headings**: Headings alone at bottom of pages
3. **Single-Line Pages**: Pages with only 1-2 lines (orphan/widow issues)
4. **Broken Chapter Breaks**: Chapters not starting on new pages
5. **Poor Line Spacing**: Too tight or too loose

### Minor (Nice to Fix)
1. **Inconsistent Spacing**: Varying paragraph spacing
2. **Hyphenation Issues**: Too many consecutive hyphens
3. **Widow/Orphan**: 2-line widows/orphans (3+ is standard)
4. **Alignment**: Mixed justified and left-aligned text

## Troubleshooting Common Issues

### PDF Upload Fails
**Error**: "pdfminer.six is required for PDF conversion"
**Solution**: Install the missing dependency
```bash
pip install pdfminer.six
```
**Prevention**: Always run `pip install -r requirements.txt` before starting the application.

### Chapters Not Detected
**Problem**: All content appears as "Main Content" chapter, no proper indentation.
**Cause**: Chapter headings don't match recognized patterns.
**Solutions**:
- Use standard formats: "Chapter 1", "Letter 2", "Part I", "Section A"
- Enable AI detection for non-standard formats
- Check that chapter titles are on separate lines

### All Paragraphs Indented
**Problem**: Every paragraph has indentation, including after headings.
**Cause**: Chapter detection failed, so first-paragraph rules don't apply.
**Solution**: Fix chapter detection (see above) or use "No Indentation" formatting style.

### Drop Cap Overlaps Text
**Problem**: Large first letter overlaps with paragraph text.
**Cause**: CSS line-height too low or font-size too large.
**Solutions**:
- Disable drop caps in the UI
- The formatter automatically uses safer drop cap settings
- Check CSS: line-height should be ≥ 1.0, font-size ≤ 2.3em

### Inconsistent Formatting
**Problem**: Mixed indentation styles or spacing.
**Cause**: Document structure not properly detected.
**Solutions**:
- Use consistent chapter heading formats
- Enable AI detection for complex documents
- Choose appropriate formatting style (KDP Standard recommended)

### Poor Readability
**Problem**: Text is hard to read due to tight spacing or small fonts.
**Solutions**:
- Use "Modern" or "No Indentation" formatting styles
- Increase margins (0.75" - 1.0" recommended)
- Check line-height (should be 1.4-1.5)

### File Size Too Large
**Problem**: PDF exceeds 500MB KDP limit.
**Solutions**:
- Reduce image resolution to 300 DPI
- Use font subsetting (automatic in formatter)
- Remove unnecessary elements from source document

### Validation Errors
**Problem**: PDF fails KDP validation checks.
**Solutions**:
- Run the formatting test to identify issues
- Use KDP Preview tool for final verification
- Check all fonts are embedded
- Ensure minimum page count (24 pages)

## Resources

### Official KDP Documentation
- [KDP Print Formatting Guide](https://kdp.amazon.com/en_US/help/topic/G201953020)
- [KDP Print Specifications](https://kdp.amazon.com/en_US/help/topic/G201834180)
- [KDP Preview Tool](https://kdp.amazon.com/en_US/help/topic/G202131170)

### Tools
- **KDP Preview**: Browser-based PDF preview
- **pdffonts**: Command-line font verification (Poppler)
- **pdfinfo**: PDF metadata inspection (Poppler)
- **pypdf**: Python PDF library for validation

### Best Practices
1. **Test Early**: Upload to KDP Preview early in the process
2. **Multiple Devices**: Test on different screen sizes and zoom levels
3. **Print Proof**: Order a physical proof copy before publishing
4. **Peer Review**: Have others review your formatted PDF
5. **Iterate**: Expect to make multiple revisions

---

**Last Updated**: 2025-01-07  
**Version**: 1.0  
**Maintained By**: KDP Formatter Project
