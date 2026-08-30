// Fold book-research narrative over the base research records.
// Imported by BOTH src/App.jsx (client) and scripts/prerender.mjs (build), so the
// prerendered HTML and the hydrated app always agree. Base data stays the source
// of truth for facts; enrichment only ever adds prose.

export function mergeSources(base = [], extra = []) {
  const key = (s) => (s.url || s.publisher || '').replace(/\/+$/, '').toLowerCase();
  const seen = new Set(base.map(key));
  return [...base, ...extra.filter((s) => key(s) && !seen.has(key(s)))];
}

export function enrichLocations(locations, enrichment = {}, corrections = {}) {
  return locations.map((base) => {
    // Factual corrections first — they patch the record itself.
    const fix = corrections[base.id];
    const l = fix ? { ...base, ...stripMeta(fix) } : base;

    const e = enrichment[l.id];
    if (!e) return l;
    return {
      ...l,
      narrative: e.background,
      hot_spot_stories: e.stories?.length ? e.stories : l.hot_spot_stories,
      sources: mergeSources(l.sources, e.extraSources),
    };
  });
}

/** Drop the bookkeeping keys (_from, _readme) so they never reach a record. */
const stripMeta = (patch) => Object.fromEntries(Object.entries(patch).filter(([k]) => !k.startsWith('_')));

export const storyTitle = (s) => (typeof s === 'string' ? s : s.title);
export const storyBody = (s) => (typeof s === 'string' ? '' : s.body || '');

const escapeHtml = (s) => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/**
 * The researcher writes prose in markdown, and the brief asks for italics on book
 * titles and foreign words. Escape first, then honour **bold** and *italic* only —
 * nothing else, so no batch can ever inject markup into the page.
 */
export function inlineHtml(text) {
  return escapeHtml(text)
    .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
    // A delimiter counts only when it does not sit between two alphanumerics —
    // so *Morning Post*'s and *bain*, both italicise, while 2*3*4 does not.
    // ...and, as in markdown proper, the delimiters must hug the text: no space
    // just inside them, so "5 * 3 * 2" stays arithmetic.
    .replace(/(?<![A-Za-z0-9*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![A-Za-z0-9*])/g, '<em>$1</em>')
    .replace(/(?<![A-Za-z0-9_])_(?!\s)([^_\n]+?)(?<!\s)_(?![A-Za-z0-9_])/g, '<em>$1</em>');
}

/** True if the text carries markdown we need to convert. */
export const hasInlineMd = (text) => /\*\*?[^*\n]+\*\*?|(^|\s)_[^_\n]+_/.test(String(text ?? ''));

/** Plain-text of the full narrative — for meta descriptions and schema.org articleBody. */
export const narrativeText = (l) => (l.narrative || (l.background ? [l.background] : [])).join(' ');
