# KDP Publisher Handoff — *The Erotic Map of Britain*

**Status:** Editorially complete; production can begin as soon as the 43 interior plates and cover components have been approved.

## Book identity

| Field | Value |
|---|---|
| Title | *The Erotic Map of Britain* |
| Subtitle | *A Tour of the Places Where Britain Misbehaved* |
| Author | The Marquis de Mayfair |
| Interior | Illustrated narrative history; adult historical subject matter, non-explicit artwork |
| Current manuscript | 70/70 topics, approximately 78,500 words, 10 chapters |
| Illustrations | 43 colour plates: 10 chapter frontispieces plus 33 alternating story plates, with front, back and spine cover components |

## Canonical inputs

Use these files and do not typeset from an earlier proof export:

1. `manuscript/MANUSCRIPT.md` — canonical book interior.
2. `manuscript/ARTWORK-GENERATION-PROMPTS.md` — visual system and every image prompt.
3. `manuscript/plates/plate-001.png` through `plate-043.png` — approved interior art, once supplied.
4. `manuscript/PROOFREADING-DRAFT.md` — reference only; it contains a marketing appendix and is not formatter input.
5. `manuscript/STATUS.md` — automated completeness check.

The manuscript is generated from `batches/` and `TOPIC-MAP.json`. Editorial corrections belong in the batch sources, followed by `node scripts/build-manuscript.mjs`; do not hand-edit `MANUSCRIPT.md`.

## Recommended KDP editions

Produce three editions from one controlled source:

| Edition | Recommended specification |
|---|---|
| Kindle | Reflowable EPUB, with responsive images and live contents navigation |
| Paperback | 7 × 10 in, standard colour, white paper, no-bleed interior, matte cover |
| Hardcover | 7 × 10 in, premium colour, white paper, no-bleed interior, matte cover |

The larger trim preserves the illustrated-map character without turning the book into an unwieldy atlas. Standard colour makes the paperback the accessible edition; premium colour gives the hardcover the intended gift-book finish. KDP currently supports premium-colour hardcover at 7 × 10 inches for 75–550 pages. If final typesetting exceeds 550 pages, reduce leading or image scale without compromising legibility, or revisit the hardcover format before ordering proofs.

## Formatter route

Extend the existing adapter at:

`/Users/nik/Downloads/Directorhelp/site/scripts/build_kdp_books.py`

It already uses the shared production toolkit at:

`/Users/nik/Downloads/KDP`

Add this title as a new configuration rather than sending the raw Markdown directly through a generic converter. The build should emit:

- print-ready paperback interior PDF;
- print-ready hardcover interior PDF if its colour/render settings differ;
- validated reflowable EPUB;
- cleaned source Markdown used for the build;
- machine-readable validation report and human QA checklist.

## Interior production rules

- Preserve the ten-chapter hierarchy, introduction, coda, Gazetteer and Index.
- Start each chapter on a recto page where practical.
- Use the supplied plate number at its manuscript marker; do not invent additional art.
- Place the 4:3 plates proportionally, never stretched. The approved master is 3600 × 2700 px RGB.
- Keep this edition no-bleed unless a deliberate full-page-bleed redesign is approved.
- Embed all fonts in print PDFs.
- Use single pages, not printer spreads.
- Keep body text, headings, folios and artwork captions inside KDP safe margins.
- Give tables enough width; wrap Gazetteer cells cleanly rather than shrinking type below readable size.
- Keep `\newpage` controls as structural intent, translating them into the formatter's page-break mechanism.
- No orphaned headings, blank trailing pages or accidental manuscript comments.

## EPUB rules

- Reflowable, not fixed-layout.
- Working navigation document and linked contents.
- Meaningful alt text derived from the plate subject and place, not the full generation prompt.
- Images resized for delivery while preserving approved masters separately.
- No hard-coded print page numbers in navigation or prose.
- Validate with EPUBCheck, then inspect in Kindle Previewer on phone, tablet and e-reader profiles.

## Cover workflow

The three generated cover images are components only. Do not let an image model render the title, subtitle, author, spine copy, imprint or barcode.

1. Finish and validate the print interior.
2. Record exact page count, trim, ink, paper and binding for each edition.
3. Download the matching template from the [KDP Cover Calculator](https://kdp.amazon.com/cover-templates?language=en_US).
4. Assemble typography and approved art on that exact template.
5. Preserve the barcode exclusion area and all bleed/safe-area guides.
6. Export a single cover PDF for each print edition; paperback and hardcover wraps will not share the same spine geometry.

## Required validation before upload

- Manuscript completeness remains 70/70 and every one of the 43 plate markers resolves to an approved image.
- PDF fonts are embedded and all images meet KDP's 300-DPI guidance at placed size.
- Page size is exactly 7 × 10 inches and every page shares the same orientation.
- No bleed objects cross trim because the recommended interior is no-bleed.
- Contents, chapter starts, Gazetteer and Index links/references are correct.
- EPUBCheck passes with no errors; Kindle Previewer shows no clipped images or broken navigation.
- Every page of each print PDF is rendered to images and visually inspected.
- KDP Print Previewer reports no unresolved errors.
- Order physical proofs of paperback and hardcover and check colour, gutter, fine rules, small type and cover alignment before publication.

KDP production references: [Print options](https://kdp.amazon.com/en_US/help/topic/G201834180), [colour ink options](https://kdp.amazon.com/en_US/help/topic/GX56BFPW4BKNPGFW), [paperback submission guidance](https://kdp.amazon.com/en_US/help/topic/G201857950), [image guidance](https://kdp.amazon.com/en_US/help/topic/G202169030), and [cover guidance](https://kdp.amazon.com/en_US/help/topic/G201953020).

## Publisher decisions still required

These do not block artwork or typesetting, but must be settled before KDP setup:

- publisher/imprint display name;
- free KDP ISBN versus owned ISBN for each print edition;
- final list price and territorial rights;
- publication date and preorder choice for Kindle;
- BISAC/category and keyword selections;
- final book description and author biography;
- whether the publisher note remains inside the final edition exactly as drafted.

## Release definition

The book is ready for the KDP publisher when the approved plate folder exists and the formatter produces passing PDF/EPUB outputs. Artwork approval is therefore the only missing production asset; cover-wrap dimensions deliberately remain pending until pagination is final.
