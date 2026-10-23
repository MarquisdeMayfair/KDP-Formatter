# General and DirectorHelp book configurations

The local upload UI now offers a book configuration and a source layout choice.
The existing DirectorHelp CLI remains available without changes to its format.

| Configuration | Source | Behaviour |
| --- | --- | --- |
| General, automatic | PDF | Preserve supplied page layout |
| General, automatic | TXT, DOCX, Markdown | Existing general text reflow |
| General, explicit reflow | PDF | Extract and reflow text; unsuitable for illustrated layouts |
| DirectorHelp | Canonical Markdown | Existing guide adapter, print styling and EPUB styling |

Preserve mode accepts PDF-only output. Page selections are one-based, inclusive,
and explicit; covers are never removed automatically. No resizing, invented
bleed, substituted fonts, rasterisation or new branding is applied. Annotations
are retained and flagged for review. Choose a fresh output directory each time.

```sh
python scripts/build_book.py --input /path/to/illustrated.pdf \
  --output-dir /path/to/private-review-draft --profile general \
  --mode preserve --first-page 2 --last-page 65 --trim 6x9 --bleed

python scripts/build_book.py --input /path/to/canonical-guide.md \
  --output-dir /path/to/guide-draft --profile directorhelp --format both
```

The first command checks for full-bleed dimensions but never manufactures bleed.
For a 6 x 9-inch trim, it expects 6.125 x 9.25-inch source pages. A mismatch still
produces a review draft and records failure; the CLI exits with status 1.

Outputs are `output.pdf` and/or `output.epub`, `build.json`, and (for print)
`validation.json`. These are local drafts, with no account access or upload.
PDF checks cover dimensions, rotation, size, annotations, font resources and
image placement PPI (using Poppler when available). They do not establish safe
areas, visible font usage, editorial accuracy, flattening, colour quality,
ink/paper-specific page limits or KDP acceptance. EPUB outputs need EPUBCheck
and device testing. The existing DirectorHelp release CLI retains its stronger
book-specific release validations; this draft builder does not replace them.

The UI retains the existing general text controls. Turn off AI/text styling
options for PDF preservation and DirectorHelp; those routes reject incompatible
settings. Preserved PDFs expose their own validation report rather than being
rechecked with prose indentation rules. The general route defaults to no AI.

Use the existing Python requirements and system dependencies. The new preserve
path itself needs pypdf plus Poppler for font/image diagnostics. No AI keys,
paid calls, deployment or production configuration changes are required.

KDP reference checked 23 October 2026:
https://kdp.amazon.com/en_US/help/topic/G201857950
Final KDP Previewer checks, physical proof and publication approval remain separate.
