// Renders the tool's JSON and text output. Strings are sorted raw, then cleaned.
import { clean, cleanText } from './errors.mjs';

export const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
export const byPair = (x, y) => cmp(x.from, y.from) || cmp(x.to, y.to);

// One entry per key, with the distinct non-empty titles of the relationships it stands for, sorted raw.
function mergeTitles(list, keyOf) {
  const byKey = new Map();
  for (const item of list) {
    const key = keyOf(item);
    if (!byKey.has(key)) byKey.set(key, { item, titles: new Set() });
    if (typeof item.title === 'string' && item.title !== '') byKey.get(key).titles.add(item.title);
  }
  return [...byKey.values()].map(({ item, titles }) => ({ ...item, titles: [...titles].sort(cmp) }));
}

const pairKey = (pair) => `${pair.from}\u0000${pair.to}`;
const linkKey = (link) => `${pairKey(link)}\u0000${link.kind}`;
const byLink = (x, y) => byPair(x, y) || cmp(x.kind, y.kind);

const cleanPair = (pair) => ({ from: clean(pair.from), to: clean(pair.to) });

// Keys whose values (and everything under them) are ids: cut like every id. Every other string is record text.
const ID_KEYS = new Set(['id', 'superseded_by', 'binds', 'owner', 'bound', 'decisions', 'elements', 'holes', 'contracts', 'capabilities',
  'gap', 'element', 'run', 'group']);

function cleanRecord(value, isId = false) {
  if (typeof value === 'string') return isId ? clean(value) : cleanText(value);
  if (Array.isArray(value)) return value.map((item) => cleanRecord(item, isId));
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, cleanRecord(item, isId || ID_KEYS.has(key))]));
  }
  return value;
}

const byId = (x, y) => cmp(x.id, y.id);

export function exportJson(model, records) {
  return {
    format: 4,
    elements: [...model.elements].sort((a, b) => cmp(a.id, b.id)).map((element) => ({
      id: clean(element.id),
      kind: clean(element.kind),
      tags: element.tags.map(clean),
      code: element.code.map(clean),
      rules: element.rules.map(clean),
      title: cleanText(element.title),
      description: element.description === null ? null : cleanText(element.description),
    })),
    allowed: mergeTitles(model.relationships, pairKey).sort(byPair)
      .map((entry) => ({ ...cleanPair(entry), titles: entry.titles.map(cleanText) })),
    runtime: mergeTitles(model.runtime, linkKey).sort(byLink)
      .map((link) => ({ ...cleanPair(link), kind: clean(link.kind), titles: link.titles.map(cleanText) })),
    groups: [...records.groups].sort((x, y) => cmp(x.kind, y.kind) || cmp(x.group, y.group))
      .map((entry) => ({ kind: entry.kind, group: clean(entry.group), title: cleanText(entry.title) })),
    decisions: [...records.decisions].sort(byId).map((record) => cleanRecord(record)),
    holes: [...records.holes].sort(byId).map((record) => cleanRecord(record)),
    contracts: [...records.contracts].sort(byId).map((record) => cleanRecord(record)),
    changes: [...records.changes].sort(byId).map((record) => cleanRecord(record)),
    coverage: records.coverage === null ? null : cleanRecord(records.coverage),
    areas: model.areas.map((area) => ({
      name: clean(area.name),
      title: cleanText(area.title),
      description: area.description === null ? null : cleanText(area.description),
      elements: area.elements.map(clean),
    })),
    capabilities: model.capabilities.map((capability) => ({
      name: clean(capability.name),
      title: cleanText(capability.title),
      description: capability.description === null ? null : cleanText(capability.description),
      steps: capability.steps.map((step) => ({
        from: clean(step.from),
        to: clean(step.to),
        label: step.label === null ? null : cleanText(step.label),
        reply: step.reply,
        kinds: step.kinds.map(clean),
      })),
    })),
  };
}

export const EDGE_SAMPLE = 20;

export function checkJson(result, located) {
  const cleanPairs = (list) => [...list].sort(byPair).map(cleanPair);
  return {
    likec4: { version: clean(located.version), source: located.source },
    breaches: [...result.breaches].sort(byPair).map((breach) => {
      const edges = [...breach.edges].sort((x, y) => cmp(x[0], y[0]) || cmp(x[1], y[1]));
      return {
        from: clean(breach.from),
        to: clean(breach.to),
        edges: edges.slice(0, EDGE_SAMPLE).map((edge) => edge.map(clean)),
        more_edges: Math.max(0, edges.length - EDGE_SAMPLE),
        gap: breach.gap,
      };
    }),
    not_yet_reached: cleanPairs(result.notYetReached),
    unmapped: [...result.unmapped].sort(cmp).map(clean),
    hot_spots: [...result.hotSpots].sort((a, b) => cmp(a.element, b.element)).map((spot) => ({
      element: clean(spot.element),
      shards: [...spot.shards].sort(cmp).map(clean),
    })),
    gap: {
      known: cleanPairs(result.gap.known),
      new: cleanPairs(result.gap.new),
      stale: cleanPairs(result.gap.stale),
    },
  };
}

export function checkText(report) {
  const count = (breach) => breach.edges.length + breach.more_edges;
  const sections = [
    ['New breaches', report.breaches.filter((b) => b.gap === 'new').map((b) => `  ${b.from} -> ${b.to} (${count(b)} edges)`)],
    ['Stale gap entries', report.gap.stale.map((p) => `  ${p.from} -> ${p.to} (remove this entry)`)],
    ['Known breaches', report.breaches.filter((b) => b.gap === 'known').map((b) => `  ${b.from} -> ${b.to} (${count(b)} edges)`)],
    ['Not yet reached', report.not_yet_reached.map((p) => `  ${p.from} -> ${p.to}`)],
    ['Unmapped code', report.unmapped.map((module) => `  ${module}`)],
    ['Shared hot spots', report.hot_spots.map((spot) => `  ${spot.element}: ${spot.shards.join(', ')}`)],
  ];
  const lines = [];
  for (const [heading, items] of sections) {
    if (items.length === 0) continue;
    lines.push(heading, ...items, '');
  }
  lines.push(
    `${report.gap.new.length} new, ${report.gap.stale.length} stale, ${report.gap.known.length} known `
      + `(likec4 ${report.likec4.version} from ${report.likec4.source})`,
  );
  return `${lines.join('\n')}\n`;
}
