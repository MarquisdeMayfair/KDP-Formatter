# DirectorHelp book release SOP

This is the fail-closed release path for DirectorHelp reference books. The
canonical Markdown is the source of truth. A website PDF may be used only to
recover missing source; it must never determine chapters from font size,
sentence shape or pagination.

## 1. Prepare the source

- Keep YAML front matter at the top if metadata is required.
- Mark each part with `# PART ...` followed by a `# Part title`.
- Mark every chapter as `## N. Chapter title`, numbered consecutively.
- Use H3 or lower only within a chapter.
- Keep tables, lists, block quotations, footnotes, warning blocks and source
  links in Markdown.
- Put build notes under `## Build notes`; the adapter removes that section and
  everything below it.

The adapter also removes ad directives, web-only calls to action and repeated
disclosures. Review the generated audit model before release to confirm that
no editorial content was removed.

## 2. Build both editions

Run one build from the clean Markdown source:

```bash
python scripts/build_directorhelp_book.py \
  --input /absolute/path/book.md \
  --output-dir output/pdf/book-slug \
  --slug book-slug \
  --cover /absolute/path/cover.png \
  --trim 6x9 \
  --edition "2026/27 Edition 1"
```

Use `--trim 7x10` for a larger reference volume. Do not substitute separate
print and ebook source documents.

## 3. Automated hard gates

The command must exit successfully and write a validation report with overall
status `pass`. A partial output is not a release candidate.

- PDF page count is 24-828 and even.
- Every page has the configured trim size.
- `pdfinfo` parses the file.
- `pdffonts` reports every font as embedded.
- Text remains inside the configured safe area.
- Every interior image is at least 300 DPI.
- All explicit parts and consecutively numbered chapters are present.
- Build notes, ad directives and removed web disclosures are absent.
- EPUB container, metadata, XHTML and navigation parse successfully.
- EPUBCheck returns zero errors and zero warnings.

Record the exact commands and reports with the release artefacts.

## 4. Visual PDF gate

Render every page to PNG and inspect every rendered page, not a sample:

```bash
mkdir -p tmp/pdfs/book-slug
pdftoppm -png -r 150 output/pdf/book-slug/book-slug-print-6x9.pdf \
  tmp/pdfs/book-slug/page
```

Check title and copyright pages, generated contents, recto/verso blanks,
chapter openings, tables, checklists, quotations, footnotes, page numbers,
widows/orphans and the final page. Any overlap, clipping, corrupted symbol or
unreadable table is a blocking defect.

## 5. Kindle Previewer gate

Open the EPUB in the current Kindle Previewer desktop application.

- Test phone, tablet and e-reader profiles.
- Change font size and line spacing to confirm genuine reflow.
- Open every table of contents entry.
- Test source links and every footnote backlink.
- Inspect tables, warning blocks, quotations and checklists at small and large
  text sizes.
- Treat every conversion warning or navigation defect as a release blocker.

Save the Kindle Previewer conversion log or screenshots with the release.

## 6. KDP gates

Upload the print PDF and EPUB as unpublished drafts.

- In Print Previewer, inspect every page again and resolve every warning.
- Confirm trim, no-bleed setting, ink/paper choice and final page count.
- Generate the paperback wrap only after the final page count and paper stock
  are fixed; do not put spine text on a book below KDP's supported spine-text
  threshold.
- In Kindle preview, test navigation, cover, metadata and Enhanced Typesetting.
- Order and approve a physical proof before publication.

Do not publish if Amazon changes pagination, reports a warning, clips content,
or renders the ebook differently enough to harm readability.

## 7. Release record

Archive together:

- canonical Markdown commit and source hash
- print PDF, EPUB and approved front cover
- validation JSON and audit model
- EPUBCheck output
- Kindle Previewer evidence
- KDP preview evidence
- proof-copy approval and publication identifiers

Changing content, fonts, trim, margins, cover, ISBN or metadata invalidates the
previous evidence and requires a complete rebuild and rerun of this SOP.
