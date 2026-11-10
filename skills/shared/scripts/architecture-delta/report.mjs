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
