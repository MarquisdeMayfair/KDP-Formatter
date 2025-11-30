# Font Assets for KDP Formatter POC

This directory contains font files for KDP-compatible PDF generation. The POC uses these fonts to ensure proper embedding and rendering in print-on-demand services.

## Recommended Fonts

For optimal KDP compatibility, we recommend using fonts that are:
- Embeddable in PDFs
- Professional and readable in print
- Available in regular, italic, and bold variants

### Primary Font: Bookerly

Bookerly is Amazon's proprietary font designed specifically for reading on Kindle devices. While not officially available for download, you can use similar alternatives.

**Alternatives to Bookerly:**
- **Libre Baskerville** (free, open-source)
- **Crimson Text** (free, open-source)
- **Garamond** (if legally available)
- **Times New Roman** (fallback, widely available)

### Secondary Font: Sans-serif for headers

For headers and UI elements, use a clean sans-serif font:
- **Open Sans** (free)
- **Roboto** (free)
- **Arial** (fallback)

## Font Installation

1. Download your chosen fonts (TTF or OTF format)
2. Place them in this `fonts/` directory
3. Update `poc/styles.css` to reference the correct font filenames
4. The CSS uses `@font-face` declarations to embed fonts in the PDF

## Font File Naming Convention

```
fonts/
├── Bookerly-Regular.ttf      # Main text font
├── Bookerly-Italic.ttf       # Italic variant
├── Bookerly-Bold.ttf         # Bold variant
├── OpenSans-Regular.ttf      # Header font
├── OpenSans-Bold.ttf         # Bold header font
```

## Font Licensing

⚠️ **Important:** Ensure you have proper licensing for any fonts you use, especially if distributing the generated PDFs commercially.

- Free fonts: Check licenses (typically SIL Open Font License)
- Commercial fonts: Purchase appropriate licenses
- System fonts: Generally safe for personal use, but check redistribution rights

## Font Embedding

The POC automatically embeds fonts in generated PDFs using WeasyPrint. This ensures:
- Fonts display correctly on all devices
- PDFs are self-contained
- KDP printing services can access the fonts

## Troubleshooting

**Fonts not embedding?**
- Verify font file paths in CSS
- Check font file permissions
- Ensure fonts are valid TTF/OTF files

**Text looks wrong?**
- Check font-family fallback order in CSS
- Verify font supports required character sets
- Test with different font weights/styles

**KDP rejects PDF?**
- Ensure all fonts are embedded
- Check PDF version compatibility
- Validate font licensing
