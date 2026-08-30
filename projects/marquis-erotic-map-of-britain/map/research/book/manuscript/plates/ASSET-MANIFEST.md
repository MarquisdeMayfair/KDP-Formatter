# Artwork Asset Manifest — Reduced 43-Plate Programme

**Generated:** 28 August 2026  
**Status:** Five active production plates, including the first three chapter frontispieces, and two preserved approved alternates. Full-resolution binaries and generator originals are mirrored in `MarquisdeMayfair/KDP-Formatter/projects/marquis-erotic-map-of-britain/` for publisher and home-laptop access.

The approved programme is now **43 images**, not 75: ten chapter frontispieces plus one illustration for every other story, covering Topics 1, 3, 5 … 65. Even-numbered story artwork is not required.

## Placement contract

### Book

- Production file: `plate-NNN.png`
- Canvas: **3600 × 2700 px**, 4:3 landscape
- Colour: **RGB**
- Resolution metadata: **300 DPI**
- Interior treatment: no bleed; centred plate with quiet surrounding margin
- Maximum recommended placed width: **4.75 in / 120.7 mm**

The image generator supplied 1448 × 1086 px originals. The production PNGs have been proportionally resampled to the required 3600 × 2700 canvas, but resampling does not invent source detail. A 4.75-inch maximum placement preserves approximately 305 PPI of original detail. Do not enlarge these plates to the full 7-inch trim width unless a genuine super-resolution pass is completed and visually approved.

### Web

- Delivery file: `map/public/images/book-plates/plate-NNN.webp`
- Canvas: **1440 × 1080 px**, 4:3 landscape
- Encoding: WebP, quality 84
- Suggested markup: declare `width="1440" height="1080"`, use `loading="lazy"` below the fold and supply descriptive alt text from the plate subject

## Active production assets

| Plate | Subject | Book master | Web derivative | QA |
|---|---|---|---|---|
| 001 | Crowns and Bedchambers | `plate-001.png` | `plate-001.webp` | Pass — approved C-style source promoted |
| 002 | A Machine for Making and Unmaking Wives | `plate-002.png` | `plate-002.webp` | Pass — adult court figures, Hampton Court setting, sealed-paper jeopardy |
| 003 | The Properest Long Man She Ever Saw | `plate-003.png` | `plate-003.webp` | Pass — Mary/Darnley first-glance composition, lute and Wemyss coastal setting |
| 006 | The Scandal Sheets | `plate-006.png` | `plate-006.webp` | Pass — late-Georgian private liaison confronted by the machinery of public exposure |
| 009 | Rakes, Monks and Pleasure Gardens | `plate-009.png` | `plate-009.webp` | Pass — masked adult couple at a lantern-lit pleasure garden, public fête opening onto a private walk |

Production Plates 004 and 005 are now Topics 5 and 7 respectively and have not yet been generated.

The first three chapter frontispieces are complete: Plates 001, 006 and 009.

## Frontispiece generation record

The immutable medium, palette, safety and output clauses are those in `../ARTWORK-GENERATION-PROMPTS.md`. Plates 006 and 009 also used Plate 001's source image as a **style reference only**, with explicit instructions not to copy its people, room, crown, papers or staging.

### Plate 006 — The Scandal Sheets

> A plausible late-Georgian British private drawing room at night. A consensual adult couple in rumpled but non-explicit period dress have just realised their private liaison is being exposed. Between them and the doorway, a hard-eyed adult scandal-sheet engraver or publisher holds freshly printed sheets as evidence; a distant pressman silhouette and street crowd imply the machinery of public disgrace. The emotional action is discovery, jeopardy and consequence, not assault or voyeuristic humiliation. Any paper is image-only with no readable lettering. Compose in 4:3 landscape with intimate foreground figures and a deep doorway axis, candlelight fighting cold exterior light.

### Plate 009 — Rakes, Monks and Pleasure Gardens

> An eighteenth-century British pleasure garden at night, with a lantern-lit supper pavilion, shadowed walks, trees and glimpses of masquerade beyond. An unmistakably adult masked couple in period dress pause at the threshold between the public fête and a dark private walk; their hands and close gaze show mutual desire and choice. A compact gathering of adult rakes, musicians and elegantly dressed revellers creates the sense of pleasure being organised, sold and watched. Compose in 4:3 landscape with theatrical depth from bright pavilion to dark walk; nocturnal, seductive, conspiratorial and faintly dangerous.

## Preserved approved alternates

These images passed visual QA but their even-numbered stories are no longer scheduled for illustration. They are retained under `plates/approved-alternates/` and may be used for marketing or reinstated later without regeneration.

| Topic | Subject | Files | QA |
|---|---|---|---|
| 002 | Seventeen Letters and a Seven-Year No | `topic-002-seventeen-letters-{source,print,web}` | Pass after edit — accidental “B” monogram removed; seal is the only passion-red punctuation |
| 004 | Pretty, Witty, and Freehold | `topic-004-pretty-witty-{source,print,web}` | Pass — Charles/Nell exchange, observing court and Banqueting House ceiling |

## Source preservation

The untouched 1448 × 1086 generator outputs are retained under `plates/source/`. Never overwrite them when preparing new print or web exports.

## Final publisher check

Before KDP export, inspect these images in the typeset PDF at 100% and in a physical proof. Look particularly for fine-line breakup, muddy oxblood areas, gutter proximity and any unwanted sharpening halos introduced during PDF production.
