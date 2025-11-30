# Test Data for KDP Formatter POC

This directory contains sample manuscripts for testing the KDP Formatter POC. These files demonstrate various input formats and help validate the conversion and rendering pipeline.

## Test File Inventory

| File | Format | Word Count | Chapters | Special Features | Status |
|------|--------|------------|----------|------------------|--------|
| `sample_short.txt` | TXT | ~350 | 5 letters | Epistolary format, foreword | ✅ Available |
| `sample_medium.txt` | TXT | ~2561 | Multiple | Longer content | ✅ Available |
| `sample_nonfiction.txt` | TXT | ~301 | TBD | Non-fiction structure | ✅ Available |
| `sample_medium.docx` | DOCX | ~8,000 | 3-5 chapters | Headings, italics, bold formatting | 📝 Needs creation (see steps below) |
| `sample_long.pdf` | PDF | ~35,000 | Multiple | Public domain literature, text extraction | 📝 Needs creation (see steps below) |

## Creating Comprehensive Test Cases

What makes a good test file for KDP Formatter validation:

- **Variety**: Include different genres (fiction, non-fiction, academic)
- **Edge Cases**: Test unusual chapter numbering, mixed formatting, special characters
- **Size Range**: Small (< 1k words), medium (5-20k), large (50k+)
- **Formatting**: Plain text, rich formatting, images, tables, footnotes
- **Licensing**: Use public domain or original content only

After creating test files and running POC tests, document results in `/docs/poc_results.md` following the templates provided there.

## Available Test Files

### `sample_short.txt`
- **Format**: Plain text
- **Content**: Short story excerpt (~500 words)
- **Purpose**: Basic functionality test, quick validation
- **Use Case**: Test text conversion, basic rendering, and validation

### `sample_medium.docx`
- **Format**: Microsoft Word document
- **Content**: Medium-length manuscript with formatting (~8,000 words)
- **Purpose**: Test DOCX conversion via Pandoc, validate rich text formatting
- **Status**: Needs creation - follow steps in "Creating Test Files" section

### `sample_long.pdf`
- **Format**: PDF document
- **Content**: Long-form public domain literature (~35,000 words)
- **Purpose**: Test PDF text extraction, performance with large documents
- **Status**: Needs creation - follow steps in "Creating Test Files" section

## Creating Test Files

### For sample_short.txt:
```bash
# Create a simple text file with chapter structure
cat > sample_short.txt << 'EOF'
Chapter 1: The Beginning

It was a dark and stormy night when the adventure began. The protagonist, a young explorer named Alex, stood at the edge of the mysterious forest. Legends spoke of hidden treasures and ancient secrets buried deep within.

"This is it," Alex whispered to themselves. "The moment I've been waiting for."

With a deep breath, Alex stepped forward into the unknown.

Chapter 2: The Discovery

Deeper in the forest, Alex discovered something extraordinary. An ancient stone structure, covered in vines and moss, stood before them. Strange symbols were carved into the surface, glowing faintly in the moonlight.

"What could this mean?" Alex wondered aloud.

As they approached, the symbols began to make sense. It was a map, pointing to a location not far from where they stood.
EOF
```

### For sample_medium.docx:
```bash
# Create a Word document template with headings and italics
# 1. Open Microsoft Word or LibreOffice Writer
# 2. Create document structure:
#    - Title page with book title and author
#    - Chapter 1 heading (Heading 1 style)
#    - 2-3 pages of content with *italics* and **bold** formatting
#    - Chapter 2 heading
#    - Additional content with mixed formatting
#    - Include some blockquotes or special paragraphs
# 3. Target word count: 5,000-15,000 words
# 4. Save as sample_medium.docx
```

### For sample_long.pdf:
```bash
# Download public domain text from Project Gutenberg and convert to PDF
# 1. Visit https://www.gutenberg.org/
# 2. Search for a long public domain book (e.g., "Pride and Prejudice" by Jane Austen)
# 3. Download the plain text version (.txt)
# 4. Convert to PDF using Pandoc:
pandoc -f plain -t pdf --pdf-engine=pdflatex \
       -V geometry:margin=1in -V fontsize=12pt \
       -o sample_long.pdf downloaded_book.txt

# Alternative: Use a word processor
# 1. Open the downloaded text in LibreOffice or Word
# 2. Format with proper page breaks and headers
# 3. Export as PDF
# Target: 30,000+ words for comprehensive testing
```

## Testing Workflow

1. **Run POC on individual files:**
   ```bash
   python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf
   ```

2. **Run all available tests:**
   ```bash
   bash poc/run_tests.sh
   ```

3. **Validate outputs:**
   - Check generated PDF visually
   - Review IDM JSON structure
   - Examine validation reports

## Expected Outputs

For each input file, the POC should generate:
- `{filename}_print.pdf` - KDP-formatted PDF
- `{filename}_print_idm.json` - Internal document model
- `{filename}_print_report.txt` - Validation report

## File Size Guidelines

- **Short**: < 1,000 words (quick testing)
- **Medium**: 5,000 - 20,000 words (normal testing)
- **Long**: > 50,000 words (performance/stress testing)

## Contributing Test Files

When adding new test files:
1. Use descriptive filenames
2. Include diverse content types
3. Test edge cases (special characters, long paragraphs, etc.)
4. Update this README with file descriptions
5. Ensure files don't contain copyrighted material

## Troubleshooting

**Conversion fails?**
- Check file format and encoding
- Verify required dependencies are installed
- Review error messages in verbose mode

**PDF looks wrong?**
- Check CSS styling
- Verify font embedding
- Test with different input formats

**Validation errors?**
- Review validation report details
- Check Poppler tools installation
- Verify PDF structure
