#!/usr/bin/env node
// Assemble the book manuscript from the researcher's batches.
//
//   research/book/batches/batch-NN.md  ->  research/book/manuscript/MANUSCRIPT.md
//                                      ->  research/book/manuscript/PROOFREADING-DRAFT.md
//                                      ->  research/book/manuscript/PLATES.md
//                                      ->  research/book/manuscript/ARTWORK-GENERATION-PROMPTS.md
//                                      ->  research/book/manuscript/STATUS.md
//
// Re-run after every new batch. Everything regenerates from source, so the
// manuscript is disposable — edit the batches, never MANUSCRIPT.md.

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadBatches, paragraphs } from './lib/parse-research.mjs';
import { enrichLocations } from '../src/data/enrich.js';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const BOOK = join(ROOT, 'research/book');
const OUT = join(BOOK, 'manuscript');
mkdirSync(OUT, { recursive: true });

const readJson = (p, fb) => { try { return JSON.parse(readFileSync(join(ROOT, p), 'utf8')); } catch { return fb; } };
const map = JSON.parse(readFileSync(join(BOOK, 'TOPIC-MAP.json'), 'utf8'));
const topics = loadBatches(join(BOOK, 'batches'));
const byNumber = Object.fromEntries(topics.map((t) => [t.n, t]));

const ALL = [
  ...enrichLocations(readJson('src/data/locations.json', []), {}, readJson('src/data/corrections.json', {})),
  ...readJson('src/data/londonTaboo.json', []),
];
const loc = Object.fromEntries(ALL.map((l) => [l.slug || l.id, l]));

const words = (s) => (s ? s.trim().split(/\s+/).filter(Boolean).length : 0);
const dd = (n) => (n >= 0 ? 'N' : 'S');
const ee = (n) => (n >= 0 ? 'E' : 'W');
const coord = (l) => `${Math.abs(l.lat).toFixed(5)}° ${dd(l.lat)}, ${Math.abs(l.lng).toFixed(5)}° ${ee(l.lng)}`;

// ---------------------------------------------------------------- art house style
// One coherent print system, with extra cinematic realism only where the
// subject is erotically charged. This decision was approved after comparing
// three style proofs: documentary ink, cinema realism and oxblood woodcut.
const PALETTE = 'midnight navy #0B1424, oxblood #6E1F2A, antique gold #C5A15A, warm parchment #E8DDC7, ivory #F5F0E6, charcoal #252420, with restrained verdigris #557A73 accents';
const PASSION_RED = '#D7192D';
const WOODCUT_STYLE = `Handmade wood engraving crossed with expressive contemporary linocut and drypoint. Bold charcoal-black cut marks, rough fields, scratched highlights, imperfect registration and tactile ink on warm fibrous paper. Use oxblood as the main second ink, with sparing antique-gold and verdigris hand-tinted accents. The result must look authored by a printmaker, not like polished digital fantasy art. House palette: ${PALETTE}.`;
const HYBRID_STYLE = `Cinematic historical realism translated through the same handmade woodcut system: believable adult faces, natural hands, lived-in period fabrics, human proximity and prestige-drama lighting, finished with expressive charcoal drypoint, oxblood linocut overprint, scratched highlights and tactile paper grain. Preserve photographic depth and emotional immediacy without glossy advertising polish or AI-perfect symmetry. House palette: ${PALETTE}.`;
const TAIL = 'No text, lettering, captions, signature, watermark, logos or decorative pseudo-writing. Any people are unmistakably adults and the scene is consensual. Keep intimacy non-explicit and strategically covered; never eroticise coercion, distress or a victim. Architecture, clothing and objects must be accurate to the stated period. Natural faces, hands and anatomy; no duplicated limbs or ornamental AI clutter. Keep the human action inside the central safe area for flexible print cropping.';
const PLATE_SPEC = '3600 × 2700 px · 4:3 landscape · RGB · 300-DPI print placement · no bleed · central safe composition';

// These subjects carry the strongest charge in the prose. They receive the
// cinematic B+C treatment; all other entries use the pure oxblood woodcut.
const HYBRID_TOPICS = new Set([
  8, 9, 11, 13, 14, 15, 17, 27, 31, 32, 41, 43, 45, 46, 48,
  50, 51, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65,
]);
// A selective-colour noir punctuation used on only a handful of C plates.
// The accent is tied to a real story object and must occupy <=5% of the frame.
const RED_PUNCTUATION = new Map([
  [2, "the broken wax seal on Henry VIII's letter"],
  [30, 'the sealing wax and narrow ribbon on the Worcester bond'],
  [33, "one Burns-red rose, echoing 'My Love is Like a Red Red Rose'"],
  [34, "the sealing wax on Elizabeth Barrett's private letter"],
  [37, "one narrow ribbon on the Austen-era letter or bonnet"],
  [38, 'one small blood-red Gothic fabric or bookmark detail'],
  [40, 'the love potion glowing inside its glass vessel'],
  [49, 'one wedding ribbon or sealing-wax detail at Gretna Green'],
  [52, 'one fresh red flower left beneath the Shaftesbury Memorial'],
]);
const styleFor = (direction) => direction === 'cinematic woodcut hybrid' ? HYBRID_STYLE : WOODCUT_STYLE;
// Editorial pacing: every chapter opens with art, then alternate stories are
// illustrated across the whole book (Topics 1, 3, 5 ... 65).
const SHOULD_ILLUSTRATE_TOPIC = (n) => n % 2 === 1;

const plates = [];
function plate({ kind, subject, location, note, prompt, chapter, direction = 'oxblood woodcut', topic = null, redAccent = null }) {
  const n = plates.length + 1;
  plates.push({ n, kind, subject, location, note, prompt, chapter, direction, topic, redAccent });
  return n;
}

function platePrompt(l, sectionTitle, direction, redAccent = null) {
  const when = l.date ? ` The scene is set in the period: ${l.date}.` : '';
  const where = [l.site, l.town, l.county, l.nation].filter(Boolean).join(', ');
  const hook = l.hook ? ` Narrative cue: ${l.hook}` : '';
  const charged = direction === 'cinematic woodcut hybrid'
    ? 'Put adult human desire, touch, body language or jeopardy at the centre where the documented story supports it. Use faces, hands, closeness, curtains, clothing and aftermath to create charge without explicit anatomy or a depicted sex act.'
    : 'Put people, ritual or consequential human action at the centre; the architecture is evidence and setting, never the whole subject.';
  const punctuation = redAccent
    ? ` Selective-colour punctuation: render only ${redAccent} in fiercely saturated passion red ${PASSION_RED}. Keep that red to roughly 3–5% of the frame; everything else remains in the normal C palette. The accent must pull the eye to the story, never become a wash, background colour, decorative splash, blood or gore.`
    : '';
  return `${styleFor(direction)} Reconstruct a human-centred scene for "${sectionTitle}" at ${l.name} — ${where}.${when}${hook} ${charged}${punctuation} Use a decisive 4:3 composition with the location recognisable but secondary to the story. No modern intrusions. ${TAIL}`;
}

// ---------------------------------------------------------------- front matter
const FRONT = join(OUT, 'front-matter.md');
const defaultFront = `<!-- Hand-edited. build-manuscript.mjs will never overwrite this file. -->

# ${map.book.title}
## ${map.book.subtitle}

*${map.book.author}*

---

## A note on what is true

This book makes a promise it intends to keep: it tells you when it does not know.

Britain's erotic history has been retold for so long, by so many people with an
interest in improving it, that a great deal of what "everyone knows" turns out to
be Victorian invention, tourist-board embroidery, or a single unreliable memoir
repeated until it hardened into fact. Where that has happened, this book says so —
in the text, not in a footnote you will never read.

So: documented history, literary fiction and folklore are labelled apart, every
time. Where a story rests on one hostile source, you will be told. Where the record
simply goes quiet, you will be told that too. The debunking is not a spoilsport's
footnote; it is frequently the best part.

Corrections are welcome and are made, never defended:
**marquis@marquisdemayfair.com**

---

## A note on the maps

Every place in this book has been given coordinates, checked and graded for
confidence on a five-point scale. They appear at the head of each section and in
full in the Gazetteer. Many of these places are private homes, working farms or
consecrated ground. Being on a map is not an invitation. Please behave.
`;
if (!existsSync(FRONT)) writeFileSync(FRONT, defaultFront);

// Hand-edited authorial matter lives beside the generated manuscript but is
// read into every build. Marketing copy is appended only to the proofreading
// file, never to the book interior.
const FOREWORD = join(OUT, 'foreword.md');
const MARKETING = join(BOOK, 'marketing/COVER-AND-WEB-COPY.md');
const foreword = existsSync(FOREWORD)
  ? readFileSync(FOREWORD, 'utf8').replace(/^<!--[\s\S]*?-->\s*/, '').trim()
  : '';
const forewordWordCount = words(foreword.replace(/^#{1,6}[^\n]*$/gm, ''));
const marketing = existsSync(MARKETING) ? readFileSync(MARKETING, 'utf8').trim() : '';

// ---------------------------------------------------------------- assemble
const written = (n) => Boolean(byNumber[n]?.book);
const chapters = map.chapters.map((c) => ({ ...c, done: c.topics.filter(written), pending: c.topics.filter((t) => !written(t)) }));
const live = chapters.filter((c) => c.done.length);

const connectiveByKind = (kind) => Object.entries(map.topics)
  .filter(([, spec]) => spec.kind === kind)
  .map(([n, spec]) => ({ n: Number(n), spec, topic: byNumber[Number(n)] }))
  .filter(({ topic }) => topic?.book);

// Opener topics use "#### Chapter 5 — Love in the Library" headings inside
// BOOK VERSION. This keeps the 70-topic contract intact while placing each
// connective passage at the start of the chapter it introduces.
const openersByChapter = new Map();
for (const { spec, topic } of connectiveByKind('chapter-openers')) {
  // The absolute-end branch must not use `\s*$` with multiline mode: that can
  // match the blank line immediately below a heading and capture an empty
  // opener. `(?![\s\S])` is true only at the actual end of the topic string.
  const re = /^####[ \t]+Chapter[ \t]+(\d+)\b[^\n]*\n([\s\S]*?)(?=^####[ \t]+Chapter[ \t]+\d+\b|(?![\s\S]))/gmi;
  let m;
  while ((m = re.exec(topic.book))) {
    const chapter = Number(m[1]);
    if (spec.covers?.includes(chapter)) openersByChapter.set(chapter, m[2].trim());
  }
}

const introduction = connectiveByKind('introduction')[0]?.topic;
const codaEntry = connectiveByKind('coda')[0];

let wordTotal = 0;
const indexEntries = new Map(); // term -> Set of "Ch.N" refs

const INDEX_ALIASES = new Map([
  ["Anne Lister", "Lister, Anne"],
  ["Anne Lister ('Gentleman Jack')", "Lister, Anne"],
  ["Anne Lister (visitor)", "Lister, Anne"],
  ["Anne Lister (1822 visitor)", "Lister, Anne"],
  ["Henry Spencer Ashbee", "Ashbee, Henry Spencer"],
  ["Henry Spencer Ashbee (Pisanus Fraxi)", "Ashbee, Henry Spencer"],
  ["Lady Eleanor Butler", "Butler, Lady Eleanor"],
  ["Lady Eleanor Butler (1739–1829)", "Butler, Lady Eleanor"],
  ["Lord Alfred Douglas", "Douglas, Lord Alfred"],
  ["Lord Alfred Douglas (met via Oxford circles)", "Douglas, Lord Alfred"],
  ["Samuel Taylor Coleridge", "Coleridge, Samuel Taylor"],
  ["Samuel Taylor Coleridge (visitor, 1799)", "Coleridge, Samuel Taylor"],
  ["Sarah Ponsonby", "Ponsonby, Sarah"],
  ["Sarah Ponsonby (1755–1831)", "Ponsonby, Sarah"],
  ["Theresa Berkley (d.1836)", "Berkley, Theresa (attributed flagellation-house keeper)"],
  ["Theresa Berkley (attributed; standard account d.1836)", "Berkley, Theresa (attributed flagellation-house keeper)"],
  ["Powys (Montgomeryshire) — NOT North Wales", "Powys"],
  ["Cumbria (Cumberland)", "Cumbria"],
  ["Cumbria (Westmorland)", "Cumbria"],
  ["Keswick (Catbells/Derwentwater)", "Keswick"],
  ["The Windmill Theatre / Rhino at the Windmill", "Windmill Theatre"],
  ["Raymond Revuebar and the Walker's Court clubs", "Raymond Revuebar"],
  ["Stringfellows & the modern club scene", "Stringfellows"],
  ["George Michael", "Michael, George"],
  ["Laura Henderson", "Henderson, Laura"],
  ["Vivian Van Damm", "Van Damm, Vivian"],
  ["Paul Raymond", "Raymond, Paul"],
  ["Peter Stringfellow", "Stringfellow, Peter"],
  ["Rictor Norton (historian)", "Norton, Rictor"],
]);
const INDEX_SKIP = new Set([
  "London",
  "Greater London",
  "anonymous makers",
  "generations of eloping couples",
  "generations of sailors and settlers",
]);
const INDEX_EXPANSIONS = new Map([
  ["patrons incl. Dusty Springfield, Maggi Hambling, Sandi Toksvig", ["Springfield, Dusty", "Hambling, Maggi", "Toksvig, Sandi"]],
]);
const MANUAL_INDEX = new Map([
  [64, ["Windmill Theatre", "Rhino at the Windmill", "Raymond Revuebar", "Stringfellows", "Penthouse Club, Walker's Court"]],
  [65, ["Sodomites' Walk", "Brown, William", "Michael, George"]],
]);

function indexAdd(term, ref) {
  const raw = term?.trim();
  if (!raw || INDEX_SKIP.has(raw)) return;
  if (INDEX_EXPANSIONS.has(raw)) {
    for (const expanded of INDEX_EXPANSIONS.get(raw)) indexAdd(expanded, ref);
    return;
  }
  const t = INDEX_ALIASES.get(raw) || raw;
  if (!t || t.length < 3) return;
  if (!indexEntries.has(t)) indexEntries.set(t, new Set());
  indexEntries.get(t).add(ref);
}

const body = [];

if (foreword) {
  body.push(`\n\n\\newpage\n\n${foreword}\n`);
  wordTotal += forewordWordCount;
}

if (introduction) {
  body.push(`\n\n\\newpage\n\n# Introduction\n`);
  body.push('\n' + paragraphs(introduction.book).join('\n\n') + '\n');
  wordTotal += words(introduction.book);
}

for (const c of live) {
  const opener = openersByChapter.get(c.n);
  body.push(`\n\n\\newpage\n\n# Chapter ${c.n} · ${c.title}\n`);
  body.push(`*${c.standfirst}*\n`);
  if (c.adult && !opener) body.push(`> **A note before this chapter.** What follows concerns the sex trades, prosecution and\n> policing. It is written for adults, without prurience and without squeamishness. Readers\n> who would rather not may skip to the Gazetteer without losing the thread of the book.\n`);

  const cp = plate({
    kind: 'chapter frontispiece',
    subject: c.title,
    location: null, // deliberately not a specific place — an emblem for the chapter
    note: c.standfirst,
    chapter: c.n,
    direction: c.adult ? 'cinematic woodcut hybrid' : 'oxblood woodcut',
    prompt: `${styleFor(c.adult ? 'cinematic woodcut hybrid' : 'oxblood woodcut')} A human-centred chapter frontispiece for "${c.title}" — ${c.standfirst}. Show one tense, observed historical moment through adult figures, gesture and consequence rather than a still life of symbols. Strong 4:3 composition, no decorative border. ${TAIL}`,
  });
  body.push(`\n> \`[PLATE ${cp} — chapter frontispiece]\`\n`);

  if (opener) {
    body.push('\n' + paragraphs(opener).join('\n\n') + '\n');
    wordTotal += words(opener);
  }

  for (const n of c.topics) {
    const t = byNumber[n];
    const spec = map.topics[String(n)];
    if (!t?.book) { body.push(`\n\n## ${n}. *[not yet written — batch ${spec?.batch ?? '?'}]*\n`); continue; }

    const ls = (spec?.locations || []).map((id) => loc[id]).filter(Boolean);
    body.push(`\n\n## ${n}. ${t.title}\n`);
    if (t.standfirst) body.push(`*${t.standfirst}*\n`);

    if (ls.length) {
      body.push('\n' + ls.map((l) => `> **${l.name}** — ${[l.town, l.county, l.nation].filter(Boolean).join(', ')}\n> ${coord(l)} · confidence ${l.coordinate_confidence}/5`).join('\n>\n') + '\n');
    }

    // One story plate for every other topic, anchored to the lead location.
    if (ls[0] && SHOULD_ILLUSTRATE_TOPIC(n)) {
      const direction = HYBRID_TOPICS.has(n) ? 'cinematic woodcut hybrid' : 'oxblood woodcut';
      const redAccent = direction === 'oxblood woodcut' ? RED_PUNCTUATION.get(n) || null : null;
      const p = plate({ kind: 'section plate', subject: t.title, location: ls[0], note: t.standfirst, chapter: c.n, topic: n, direction, redAccent, prompt: platePrompt(ls[0], t.title, direction, redAccent) });
      body.push(`\n> \`[PLATE ${p} — ${ls[0].name} · ${coord(ls[0])}]\`\n`);
    }

    const ps = paragraphs(t.book);
    body.push('\n' + ps.join('\n\n') + '\n');
    wordTotal += words(t.book);

    // Index: people and places named in the record, plus towns/counties.
    const ref = `Ch.${c.n}§${n}`;
    for (const l of ls) {
      indexAdd(l.name.replace(/\s*\(.*?\)\s*$/, ''), ref);
      indexAdd(l.town, ref);
      indexAdd(l.county, ref);
      for (const p of l.people || []) indexAdd(p.replace(/\s*\(fictional\)\s*/i, ''), ref);
    }
    // Catch people named in prose who belong to other records (the cross-threads).
    for (const l of ALL) for (const p of l.people || []) {
      const clean = p.replace(/\s*\(fictional\)\s*/i, '').trim();
      if (clean.length > 6 && clean.includes(' ') && t.book.includes(clean)) indexAdd(clean, ref);
    }
    for (const term of MANUAL_INDEX.get(n) || []) indexAdd(term, ref);
  }
}

if (codaEntry) {
  const { spec, topic } = codaEntry;
  const ls = (spec.locations || []).map((id) => loc[id]).filter(Boolean);
  body.push(`\n\n\\newpage\n\n# Coda\n`);
  if (ls.length) {
    body.push('\n' + ls.map((l) => `> **${l.name}** — ${[l.town, l.county, l.nation].filter(Boolean).join(', ')}\n> ${coord(l)} · confidence ${l.coordinate_confidence}/5`).join('\n>\n') + '\n');
  }
  body.push('\n' + paragraphs(topic.book).join('\n\n') + '\n');
  wordTotal += words(topic.book);
}

// ---------------------------------------------------------------- contents
const contents = ['\n\n\\newpage\n\n# Contents\n'];
if (foreword) contents.push('\n**Foreword · Britain, in Private**');
if (introduction) contents.push('\n**Introduction**');
for (const c of chapters) {
  const state = c.done.length === c.topics.length ? '' : c.done.length ? ` *(${c.done.length}/${c.topics.length} drafted)*` : ' *(to come)*';
  contents.push(`\n**Chapter ${c.n} · ${c.title}**${state}  \n*${c.standfirst}*\n`);
  for (const n of c.topics) {
    const t = byNumber[n];
    contents.push(t?.book ? `${n}. ${t.title}  ` : `${n}. *[batch ${map.topics[String(n)]?.batch ?? '?'} — to come]*  `);
  }
}
if (codaEntry) contents.push('\n**Coda**');
contents.push('\n\n**Gazetteer** — every place, with coordinates  \n**Index**\n');

// ---------------------------------------------------------------- gazetteer
const gaz = ['\n\n\\newpage\n\n# Gazetteer\n', '\nEvery place in this book, north to south, with its coordinates and how confident we are in them. Confidence 5 means a surveyed or listed position; 1 means an informed estimate for a site whose exact location is lost or, in some cases, linear.\n'];
const covered = [
  ...live.flatMap((c) => c.topics).filter(written).flatMap((n) => map.topics[String(n)]?.locations || []),
  ...(codaEntry?.spec.locations || []),
];
const gazRows = [...new Set(covered)].map((id) => loc[id]).filter(Boolean).sort((a, b) => b.lat - a.lat);
gaz.push('\n| Place | County | Coordinates | Conf. |\n|---|---|---|---|');
for (const l of gazRows) gaz.push(`| ${l.name} | ${l.county}, ${l.nation} | ${coord(l)} | ${l.coordinate_confidence}/5 |`);

// ---------------------------------------------------------------- index
const idx = ['\n\n\\newpage\n\n# Index\n', '\n*References are to chapter and section number, not page — pagination follows typesetting.*\n'];
const grouped = new Map();
for (const [term, refs] of [...indexEntries].sort((a, b) => a[0].localeCompare(b[0], 'en'))) {
  const letter = term[0].toUpperCase();
  if (!grouped.has(letter)) grouped.set(letter, []);
  grouped.get(letter).push(`**${term}** — ${[...refs].join(', ')}`);
}
for (const [letter, items] of grouped) idx.push(`\n### ${letter}\n\n${items.join('  \n')}\n`);

// ---------------------------------------------------------------- write
const manuscript = [
  readFileSync(FRONT, 'utf8'),
  contents.join('\n'),
  body.join('\n'),
  gaz.join('\n'),
  idx.join('\n'),
].join('\n');
writeFileSync(join(OUT, 'MANUSCRIPT.md'), manuscript);

const proofreading = marketing
  ? `${manuscript}\n\n\\newpage\n\n---\n\n# Proofreading appendix — cover and website copy\n\n${marketing}\n`
  : manuscript;
writeFileSync(join(OUT, 'PROOFREADING-DRAFT.md'), proofreading);

// ---------------------------------------------------------------- plates brief
const platesDoc = [
  `# Plate Brief — ${map.book.title}`,
  `\n${plates.length} plates. Every prompt is self-contained: paste it whole into the image model.`,
  `\nThe book uses two controlled directions: **oxblood woodcut** throughout, with a **cinematic woodcut hybrid** for the most erotically charged subjects. The hybrid changes the human realism and lighting, not the palette or print surface.`,
  `\nA small number of C plates use one sharply saturated **passion-red punctuation** (${PASSION_RED}) on a story-specific object. It occupies no more than 3–5% of the image and is never used as a wash, decoration, blood or gore.`,
  `\n**Oxblood woodcut**\n\n> ${WOODCUT_STYLE}`,
  `\n**Cinematic woodcut hybrid**\n\n> ${HYBRID_STYLE}`,
  `\n**Tail, on every prompt:**\n\n> ${TAIL}`,
  `\n---\n`,
];
for (const p of plates) {
  platesDoc.push(`\n## Plate ${p.n} — ${p.subject}`);
  platesDoc.push(`*${p.kind} · Chapter ${p.chapter} · ${p.direction}*  `);
  if (p.redAccent) platesDoc.push(`**Selective passion red:** ${p.redAccent} (${PASSION_RED}; maximum 3–5% of frame)  `);
  if (p.location) {
    platesDoc.push(`**Place:** ${p.location.name}, ${[p.location.town, p.location.county, p.location.nation].filter(Boolean).join(', ')}  `);
    platesDoc.push(`**Coordinates:** ${coord(p.location)} (confidence ${p.location.coordinate_confidence}/5)  `);
    platesDoc.push(`**Period:** ${p.location.date}  `);
    platesDoc.push(`**Reference imagery:** search the coordinates on any aerial/street view for massing and setting before generating.  `);
  }
  platesDoc.push(`\n**Prompt**\n\n> ${p.prompt}\n`);
  platesDoc.push(`**Output:** \`plates/plate-${String(p.n).padStart(3, '0')}.png\` · ${PLATE_SPEC}\n`);
}
writeFileSync(join(OUT, 'PLATES.md'), platesDoc.join('\n'));

// A production-facing, standalone prompt pack. Unlike PLATES.md, this begins
// with the immutable design system and also specifies the three cover assets.
// The final cover wrap must be assembled only after typesetting fixes the spine.
const artPrompts = [
  `# Artwork Generation Prompts — ${map.book.title}`,
  `\nThis is the single source of truth for all generated artwork. The programme contains ${plates.length} interior plates: ten chapter frontispieces plus one illustration for every other story (Topics 1, 3, 5 … 65). Create the cover components only after the interior has been typeset. Do not generate a finished wraparound cover until the final KDP page count is known.`,
  `\n## Approved visual system`,
  `\n**Decision:** Option C is the book's visual backbone. The more erotically charged entries use a controlled combination of Option B's cinematic realism and Option C's oxblood woodcut surface. Empty architecture, symbolic still lifes, faux-Victorian borders and generic parchment illustration are rejected.`,
  `\n### Direction C — oxblood woodcut`,
  `\n> ${WOODCUT_STYLE}`,
  `\n### Direction B+C — cinematic woodcut hybrid`,
  `\n> ${HYBRID_STYLE}`,
  `\n**Palette:**`,
  `\n- Midnight navy — \`#0B1424\``,
  `- Oxblood — \`#6E1F2A\``,
  `- Antique gold — \`#C5A15A\``,
  `- Warm parchment — \`#E8DDC7\``,
  `- Ivory — \`#F5F0E6\``,
  `- Charcoal — \`#252420\``,
  `- Verdigris accent — \`#557A73\``,
  `- Selective passion-red punctuation — \`${PASSION_RED}\` (assigned C plates only; never more than 3–5% of the frame)`,
  `\n**Story rule:** Every plate must show people, ritual, desire, jeopardy or a visible human consequence. Architecture anchors the place but does not become the subject. Charged plates use adult faces, hands, closeness, curtains, clothing, private rooms and aftermath to create commercial heat while remaining consensual, non-explicit and suitable for KDP.`,
  `\n**Selective-red rule:** On specifically assigned C plates, one story object may break the house palette in saturated passion red ${PASSION_RED}. Treat it like a selective-colour noir punctuation mark: small, intentional and dramatically brighter than the surrounding oxblood. Never add red to an unassigned plate; never use it as blood, gore, a general colour grade or empty decoration.`,
  `\n**Consistency rules:** The same oxblood, charcoal and fibrous-paper print surface runs through both directions. Use period-accurate architecture, landscape and clothing. No modern objects unless the prompt explicitly calls for a present-day scene. Adults only; never eroticise coercion, distress or victims. No text, logos, watermarks, pseudo-writing, malformed hands or decorative AI clutter.`,
  `\n**Interior production spec:** ${PLATE_SPEC}. Save exactly as \`plates/plate-NNN.png\`. Preserve a quiet outer margin and keep faces, hands and important architecture away from trim edges and the gutter.`,
  `\n**Quality check for every image:** correct period and location; palette compliance; no accidental text; no malformed faces or hands; no visible contemporary objects; no important detail in the crop zone.`,
  `\n---`,
  `\n## Interior plates`,
];
for (const p of plates) {
  artPrompts.push(`\n### Plate ${String(p.n).padStart(3, '0')} — ${p.subject}`);
  artPrompts.push(`\n**File:** \`plates/plate-${String(p.n).padStart(3, '0')}.png\`  `);
  artPrompts.push(`**Use:** ${p.kind}, Chapter ${p.chapter}  `);
  artPrompts.push(`**Direction:** ${p.direction}  `);
  if (p.redAccent) artPrompts.push(`**Selective passion red:** ${p.redAccent} (${PASSION_RED}; maximum 3–5% of frame)  `);
  if (p.location) {
    artPrompts.push(`**Place:** ${p.location.name}, ${[p.location.town, p.location.county, p.location.nation].filter(Boolean).join(', ')}  `);
    artPrompts.push(`**Period:** ${p.location.date}  `);
  }
  artPrompts.push(`\n> ${p.prompt}\n`);
}
const coverBase = `${WOODCUT_STYLE} Designed as a bold, commercially intriguing illustrated trade-history cover for adults, with generous calm space reserved for typography to be added later by the cover designer. ${TAIL}`;
artPrompts.push(
  `\n---`,
  `\n## Cover components`,
  `\nThese are art components, not the final cover. Supply them without type. The cover designer must add the title, subtitle, author, imprint and barcode after the final page count and KDP Cover Calculator template are available.`,
  `\n### Cover A — Front-cover hero illustration`,
  `\n**File:** \`cover/front-cover-art-master.png\`  `,
  `**Master:** 4200 × 5400 px · portrait · RGB · 300 DPI · extendable background on all sides`,
  `\n> ${coverBase} An imaginative map of Britain made from layered moonlit landscape, London rooftops, old stone, theatre curtains and a winding antique-gold route. Suggest secrecy, history, desire and travel through symbols rather than explicit figures: a discreet half-open doorway, a fan, a key, a chalk hillside and a distant lantern. Strong central silhouette, midnight-navy field, oxblood focal accents, warm parchment glow and delicate verdigris details. Leave the upper third and lower quarter visually quiet for title and author typography. No literal map labels and no words.\n`,
  `\n### Cover B — Back-cover continuation`,
  `\n**File:** \`cover/back-cover-art-master.png\`  `,
  `**Master:** 4200 × 5400 px · portrait · RGB · 300 DPI · extendable background on all sides`,
  `\n> ${coverBase} A quieter continuation of the front-cover world: midnight-navy and warm-parchment British landscape dissolving into subtle antique map lines, theatre-curtain folds and small gold route marks. Keep the central two-thirds low-detail and high-contrast enough for legible blurb text. Reserve a completely calm pale or navy rectangle in the lower-right area for the retailer barcode. No figures, no labels and no words.\n`,
  `\n### Cover C — Spine ornament`,
  `\n**File:** \`cover/spine-ornament-master.png\`  `,
  `**Master:** 1200 × 5400 px · portrait · transparent or midnight-navy background · RGB · 300 DPI`,
  `\n> ${coverBase} A narrow vertical ornamental device only: a fine antique-gold route line winding between a tiny key, crescent moon, theatrical star and chalk-hill motif, with restrained oxblood and verdigris details. Symmetrical visual weight, generous clear space for separately typeset spine title. No text and no border that depends on an exact spine width.\n`,
  `\n## Final-cover assembly gate`,
  `\nDo not assemble or upload the wrap until the formatter supplies the final interior PDF page count. Then download the exact KDP 7 × 10 inch cover template for the chosen binding and paper, place these components into it, add typography and barcode clearance, export a single print-ready PDF, and inspect every bleed and safe-area boundary.`,
);
writeFileSync(join(OUT, 'ARTWORK-GENERATION-PROMPTS.md'), artPrompts.join('\n') + '\n');

// ---------------------------------------------------------------- status
const doneCount = topics.filter((t) => t.book).length;
const totalTopics = Object.keys(map.topics).length;
const status = [
  `# Manuscript status`,
  `\nGenerated from ${topics.length} parsed topics across \`research/book/batches/\`.\n`,
  `| | |\n|---|---|`,
  `| Topics drafted | **${doneCount} / ${totalTopics}** |`,
  `| Book words | **${wordTotal.toLocaleString()}** |`,
  `| Target | 50,000+ |`,
  `| Progress to target | **${Math.round((wordTotal / 50000) * 100)}%** |`,
  `| Plates specified | ${plates.length} |`,
  `| Index entries | ${indexEntries.size} |`,
  `| Locations in gazetteer | ${gazRows.length} |`,
  `\n## By chapter\n`,
  `| Ch. | Title | Drafted | Words |\n|---|---|---|---|`,
  ...chapters.map((c) => {
    const w = c.topics.filter(written).reduce((a, n) => a + words(byNumber[n].book), 0);
    return `| ${c.n} | ${c.title} | ${c.done.length}/${c.topics.length} | ${w.toLocaleString()} |`;
  }),
  `\n## Connective matter\n`,
  `| Section | Drafted | Words |\n|---|---|---|`,
  `| Foreword | ${foreword ? 'yes' : 'no'} | ${forewordWordCount.toLocaleString()} |`,
  `| Introduction | ${introduction ? 'yes' : 'no'} | ${words(introduction?.book).toLocaleString()} |`,
  `| Chapter openers | ${openersByChapter.size}/10 | ${[...openersByChapter.values()].reduce((a, s) => a + words(s), 0).toLocaleString()} |`,
  `| Coda | ${codaEntry ? 'yes' : 'no'} | ${words(codaEntry?.topic.book).toLocaleString()} |`,
  `\n## Next batch to commission\n`,
];
const nextBatch = Math.min(...Object.entries(map.topics).filter(([n]) => !written(Number(n))).map(([, s]) => s.batch));
const nextTopics = Object.entries(map.topics).filter(([n, s]) => s.batch === nextBatch && !written(Number(n))).map(([n]) => n);
status.push(Number.isFinite(nextBatch) ? `**Batch ${nextBatch}** — topics ${nextTopics.join(', ')}. See \`BOOK-TOPIC-LIST.md\`.` : 'All batches received.');
writeFileSync(join(OUT, 'STATUS.md'), status.join('\n') + '\n');

console.log(`build-manuscript: ${doneCount}/${totalTopics} topics · ${wordTotal.toLocaleString()} words · ${plates.length} plates · ${indexEntries.size} index entries`);
console.log(`  -> manuscript/MANUSCRIPT.md, PROOFREADING-DRAFT.md, PLATES.md, ARTWORK-GENERATION-PROMPTS.md, STATUS.md`);
