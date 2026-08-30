// Parser for the researcher's batch markdown (see research/book/RESEARCHER-BRIEF.md §5).
// One source of truth for both pipelines: ingest-research.mjs (site) and
// build-manuscript.mjs (book). Tolerant by design — the researcher is an LLM and
// will drift on whitespace, dash characters and heading capitalisation.

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const DASH = '[—–-]'; // em, en, hyphen — the researcher mixes all three

/** Split a batch file into topic blocks keyed by topic number. */
export function parseBatch(md) {
  const topics = [];
  // "## 3 — The Properest Long Man She Ever Saw"
  const re = new RegExp(`^##[ \\t]+(\\d+)[ \\t]*${DASH}[ \\t]*(.+)$`, 'gm');
  const marks = [];
  let m;
  while ((m = re.exec(md))) marks.push({ n: Number(m[1]), title: m[2].trim(), start: m.index, bodyAt: re.lastIndex });

  marks.forEach((mark, i) => {
    const end = i + 1 < marks.length ? marks[i + 1].start : md.length;
    const body = md.slice(mark.bodyAt, end);
    topics.push({ n: mark.n, title: mark.title, ...parseTopicBody(body) });
  });
  return topics;
}

/** Pull the "*Location · Town, County · Dates*" standfirst that follows the H2. */
function parseStandfirst(body) {
  const m = body.match(/^\s*\*([^*\n]+)\*\s*$/m);
  return m ? m[1].trim() : '';
}

function sectionsOf(body) {
  // Split on "### HEADING" and keep heading + content together.
  const out = [];
  const re = /^###[ \t]+(.+)$/gm;
  const marks = [];
  let m;
  while ((m = re.exec(body))) marks.push({ heading: m[1].trim(), start: m.index, bodyAt: re.lastIndex });
  marks.forEach((mark, i) => {
    const end = i + 1 < marks.length ? marks[i + 1].start : body.length;
    out.push({ heading: mark.heading, text: body.slice(mark.bodyAt, end).trim() });
  });
  return out;
}

function parseTopicBody(body) {
  const standfirst = parseStandfirst(body);
  const secs = sectionsOf(body);
  const result = { standfirst, book: '', web: [], stories: [], sources: [], factNotes: [] };

  for (const { heading, text } of secs) {
    const h = heading.toUpperCase();

    if (/^BOOK VERSION/.test(h)) {
      result.book = text;
    } else if (/^WEB VERSION/.test(h)) {
      // Three shapes seen in the wild, all accepted:
      //   "### WEB VERSION — wemyss-castle-mary-darnley"   (the brief's format)
      //   "### WEB VERSION (~350 words)"                    (single location)
      //   "### WEB VERSION" then "**osborne-house...**" sub-labels in the body
      const idm = heading.match(new RegExp(`${DASH}\\s*([a-z0-9][a-z0-9-]{3,})\\s*$`, 'i'));
      const split = splitByBoldIds(text);
      if (split.length) result.web.push(...split);
      else result.web.push({ id: idm ? idm[1].toLowerCase() : null, text });
    } else if (/^MORE STORIES/.test(h)) {
      result.stories = parseStories(text);
    } else if (/^SOURCES/.test(h)) {
      result.sources = parseSources(text);
    } else if (/^FACT NOTES/.test(h)) {
      result.factNotes = text.split('\n').map((l) => l.replace(/^[-*]\s*/, '').trim()).filter(Boolean);
    }
  }
  return result;
}

/**
 * A web-version block may carry several locations, each introduced by its id in
 * bold on its own line: "**osborne-house-victoria-albert**". Returns [] when the
 * block has no such labels, so the caller can fall back to the heading.
 */
function splitByBoldIds(text) {
  const re = /^\*\*([a-z0-9][a-z0-9-]{3,})\*\*\s*$/gm;
  const marks = [];
  let m;
  while ((m = re.exec(text))) marks.push({ id: m[1].toLowerCase(), start: m.index, bodyAt: re.lastIndex });
  if (!marks.length) return [];
  return marks.map((mark, i) => ({
    id: mark.id,
    text: text.slice(mark.bodyAt, i + 1 < marks.length ? marks[i + 1].start : text.length).trim(),
  }));
}

/** "**Title.** Body copy…" → { title, body } */
function parseStories(text) {
  const out = [];
  const re = /^\*\*(.+?)\*\*\s*([\s\S]*?)(?=\n\s*\n\*\*|$)/gm;
  let m;
  while ((m = re.exec(text))) {
    const title = m[1].replace(/[.:\s]+$/, '').trim();
    const bodyText = m[2].replace(/\s+/g, ' ').trim();
    if (title && bodyText) out.push({ title, body: bodyText });
  }
  return out;
}

/** "- Publisher — URL — note" → { publisher, url, note, paywalled } */
function parseSources(text) {
  return text.split('\n')
    .map((l) => l.replace(/^[-*]\s*/, '').trim())
    .filter(Boolean)
    .map((line) => {
      const url = (line.match(/https?:\/\/\S+/) || [''])[0].replace(/[)\].,]+$/, '');
      const parts = line.split(new RegExp(`\\s+${DASH}\\s+`));
      const publisher = (parts[0] || line).trim();
      const note = parts.filter((p) => !/^https?:\/\//.test(p.trim())).slice(1).join(' — ').trim();
      return { publisher, url, note, paywalled: /paywall/i.test(line) };
    })
    .filter((s) => s.publisher);
}

/** Read every batch-NN.md in a directory, in numeric order. */
export function loadBatches(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => /^batch-\d+\.md$/.test(f))
    .sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]))
    .flatMap((f) => parseBatch(readFileSync(join(dir, f), 'utf8')).map((t) => ({ ...t, sourceFile: f })));
}

/** Split prose into paragraphs, dropping any stray markdown headings. */
export const paragraphs = (text) =>
  text.split(/\n\s*\n/).map((p) => p.replace(/\s+/g, ' ').trim()).filter((p) => p && !p.startsWith('#'));
