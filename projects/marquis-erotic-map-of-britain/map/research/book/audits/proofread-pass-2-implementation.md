# Proofread pass 2 — implementation record

**Implemented:** 27 August 2026  
**Editorial inputs:** `PROOFREADING-CONTINUATION-REPORT.md` and `PASTE-READY-REPLACEMENTS-SECTIONS-59-65-CODA.md`

## What changed

- Replaced the book version of §59 with the evidence-led Theresa Berkley account and qualified the web version in the same way.
- Applied the supplied tightening to §§60–63, including the Cleveland Street title and the fourteen/eighteen-shilling disagreement.
- Reordered the Chapter Ten close so that clubs are §64 and Hampstead Heath is §65.
- Replaced §64 with the current Windmill/Revuebar/Stringfellows account, including the 2026 reopening as Rhino at the Windmill.
- Added separate map/Gazetteer records for the Windmill and Walker's Court; retained Stringfellows as the third mapped venue.
- Routed the audited web versions for Topics 59, 64 and 65 into the gated London Taboo pages, superseding the stale static copy for those entries. Topic 64's shared web text is ingested once and applied to all three mapped venues.
- Hardened `build-taboo.mjs` so a later legacy-overlay rebuild preserves the two supplemental venues and the audited Berkley/Holywell corrections.
- Revised §65 to distinguish George Michael's 1998, 2006, 2009 and 2011 events and to state the legal position with greater precision.
- Replaced the Coda in full. The Marquis de Mayfair declaration is now a separate publisher's note after the literary ending.
- Shortened the Chapter Seven opener so it no longer repeats the Gretna Green entry's mechanism and current wedding statistics.
- Removed the generic restatement from the end of §50 so the Profumo entry closes on Christine Keeler.
- Reduced the Introduction's repeated method examples and moved the full motionless-nude explanation to §64.
- Removed the Coda's low-confidence Marquis de Mayfair coordinate from the book and Gazetteer.
- Canonicalised duplicate Index entries, removed machine labels and mega-geographic entries, and added controlled terms for the final two sections.
- Corrected the Gwerful Mechain county field from an editorial note to `Powys`.

## Deliberate editorial decisions

- The pass-2 report's Brontë recommendation described the pre-pass-1 manuscript. Pass 1 had already solved that collision by opening §29 with Zoë Heger repairing the torn letters. That stronger, non-duplicative opening was retained.
- The publisher's note remains in the interior because the supplied replacement explicitly recommends transparency when a commercial sign-off is necessary. It is visually and rhetorically separate from the Coda.
- The clubs section maps all three principal venues rather than using Stringfellows as a proxy for Soho.

## Current-status verification

- Rhino at the Windmill's official site confirms current trading at 17–19 Great Windmill Street: <https://www.rhinowindmill.com/>
- Westminster's Licensing Sub-Committee granted the Windmill renewal and variation on 2 July 2026: <https://westminster.moderngov.co.uk/mgAi.aspx?ID=23735>
- Westminster granted the Penthouse Club sexual-entertainment venue licence at 1–4 Walker's Court on 27 February 2025: <https://westminster.moderngov.co.uk/mgAi.aspx?ID=21667>
- Historic England supports the West Heath and Sodomites' Walk history: <https://historicengland.org.uk/research/inclusive-heritage/lgbtq-heritage-project/meeting-and-socialising/places-for-sex/>
- The George Michael chronology was checked against contemporary reporting; the `quick and honest sex` wording belongs to 2009, not 2006.
- The full 1718 flagellation title was checked against the Folger catalogue: <https://catalog.folger.edu/record/748160>

## Build result

The source batches were ingested and the manuscript rebuilt successfully:

- 70/70 topics
- 78,546 interior words
- 75 plates
- 460 generated Index entries
- 108 Gazetteer locations

The final counts are regenerated in `manuscript/STATUS.md` on every build.

## Remaining non-blocking pipeline note

The ingest script still reports one older warning for Topic 14: one unlabelled web version is being matched across two locations heuristically. This warning predates proofread pass 2 and does not affect the Chapter Ten or Coda changes.
