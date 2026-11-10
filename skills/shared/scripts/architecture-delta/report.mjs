// Renders the tool's JSON and text output. Strings are sorted raw, then cleaned.
import { clean } from './errors.mjs';

export const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
export const byPair = (x, y) => cmp(x.from, y.from) || cmp(x.to, y.to);

export function uniquePairs(list) {
  const seen = new Set();
  return list.filter((pair) => {
    const key = `${pair.from}\u0000${pair.to}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

const cleanPair = (pair) => ({ from: clean(pair.from), to: clean(pair.to) });

export function exportJson(model) {
  return {
    format: 1,
    elements: [...model.elements].sort((a, b) => cmp(a.id, b.id)).map((element) => ({
      id: clean(element.id),
      kind: clean(element.kind),
      tags: element.tags.map(clean),
      code: element.code.map(clean),
      rules: element.rules.map(clean),
    })),
    allowed: uniquePairs(model.relationships).sort(byPair).map(cleanPair),
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
