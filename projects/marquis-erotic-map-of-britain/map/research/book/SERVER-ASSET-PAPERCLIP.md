# Server Asset Paperclip — *The Erotic Map of Britain*

**Updated:** 30 August 2026  
**Server repository:** `MarquisdeMayfair/KDP-Formatter`  
**Server directory:** `projects/marquis-erotic-map-of-britain/`  
**Browser:** <https://github.com/MarquisdeMayfair/KDP-Formatter/tree/main/projects/marquis-erotic-map-of-britain>

This paperclip is the recovery map for the complete book package. The server bundle mirrors the original `map/` paths so the manuscript can be read immediately or regenerated from the research sources.

## Canonical files

| Purpose | Path inside the server directory |
|---|---|
| Canonical manuscript for typesetting | `map/research/book/manuscript/MANUSCRIPT.md` |
| Proofreading copy with marketing appendix | `map/research/book/manuscript/PROOFREADING-DRAFT.md` |
| KDP production handoff | `map/research/book/KDP-PUBLISHER-HANDOFF.md` |
| Artwork system and 43 final prompts | `map/research/book/manuscript/ARTWORK-GENERATION-PROMPTS.md` |
| Plate list and placements | `map/research/book/manuscript/PLATES.md` |
| Automated completeness report | `map/research/book/manuscript/STATUS.md` |
| Artwork inventory and generation record | `map/research/book/manuscript/plates/ASSET-MANIFEST.md` |
| Research topic authority | `map/research/book/TOPIC-MAP.json` |
| Research batches | `map/research/book/batches/batch-01.md` through `batch-14.md` |
| Editorial audit record | `map/research/book/audits/` |

`MANUSCRIPT.md` is generated. Editorial corrections belong in the relevant batch source, front matter or foreword, followed by a rebuild; do not make durable edits only in the generated manuscript.

## Artwork locations

| Asset class | Server path |
|---|---|
| KDP print masters, 3600 × 2700 RGB with 300-DPI metadata | `map/research/book/manuscript/plates/plate-NNN.png` |
| Untouched 1448 × 1086 generator originals | `map/research/book/manuscript/plates/source/` |
| Responsive 1440 × 1080 WebP files | `map/public/images/book-plates/` |
| Approved images removed by the alternating-story reduction | `map/research/book/manuscript/plates/approved-alternates/` |
| Style-development and rejected proofs | `map/research/book/manuscript/plates/style-options/` |

Active production plates currently present:

- `plate-001` — Chapter 1 frontispiece, *Crowns and Bedchambers*
- `plate-002` — Topic 1, *A Machine for Making and Unmaking Wives*
- `plate-003` — Topic 3, *The Properest Long Man She Ever Saw*
- `plate-006` — Chapter 2 frontispiece, *The Scandal Sheets*
- `plate-009` — Chapter 3 frontispiece, *Rakes, Monks and Pleasure Gardens*

The approved illustration programme contains 43 plates: ten chapter frontispieces plus Topics 1, 3, 5 … 65. Thirty-eight production plates remain to be generated.

## Verified editorial state

- Topics: **70/70**
- Book words: **78,546**
- Chapters: **10**
- Planned plates: **43**
- Active completed plates: **5**
- Preserved approved alternates: **2**

## Rebuild on another computer

From the root of `projects/marquis-erotic-map-of-britain/`:

```bash
node map/scripts/build-manuscript.mjs
```

The server package includes the script, parser and exact location-data dependencies required by that command. No `npm install` is needed for the manuscript build.

## Home-laptop access

For a new checkout:

```bash
git clone https://github.com/MarquisdeMayfair/KDP-Formatter.git
cd KDP-Formatter/projects/marquis-erotic-map-of-britain
```

For an existing checkout:

```bash
cd KDP-Formatter
git pull origin main
cd projects/marquis-erotic-map-of-britain
```

After pulling, verify the bundle from its project root:

```bash
shasum -a 256 -c SHA256SUMS.txt
```

## Resolution caveat

The image generator supplied 1448 × 1086 originals. The KDP masters were proportionally resampled to 3600 × 2700; resizing does not create additional source detail. Keep the current plates at or below **4.75 inches / 120.7 mm wide** in print unless a true super-resolution pass is completed and approved. Inspect every plate in the final PDF and physical KDP proof.

## Recovery rule

The KDP-Formatter server directory is the portable publisher copy. The quiz repository remains the editorial/web source of truth while work continues. When either copy changes, update this paperclip, regenerate `SHA256SUMS.txt`, and push both repositories in the same working session.
