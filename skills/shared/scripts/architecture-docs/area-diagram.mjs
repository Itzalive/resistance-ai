// The drawing rules (spec, What each document holds, Drawing rules): framed elements and their neighbours, import,
// runtime and known-gap arrows, implied arrows hidden. `base` comes from `documentBase`.
import { cmp } from '../architecture-delta/report.mjs';
import { ARROW_LIMIT, flowchart } from './mermaid.mjs';

const STYLES = ['import', 'runtime', 'gap'];

// An element and every element it is inside: `a.b.c`, `a.b`, `a`.
function selfAndAbove(id) {
  const parts = id.split('.');
  return parts.map((_, at) => parts.slice(0, parts.length - at).join('.'));
}

// Within one style, an arrow X -> Y is implied by an arrow X' -> Y' with X' at or inside X, Y' at or inside Y, and the
// two arrows not the same. Only pairs that are arrows are looked up. An implying arrow is deeper than the arrow it
// implies and implies everything that arrow does, so arrows are visited deepest first and an implied one is skipped.
function hideImplied(arrows) {
  const depth = (arrow) => arrow.from.split('.').length + arrow.to.split('.').length;
  const targets = new Map();
  for (const arrow of arrows) {
    if (!targets.has(arrow.from)) targets.set(arrow.from, new Map());
    targets.get(arrow.from).set(arrow.to, arrow);
  }
  const implied = new Set();
  for (const arrow of [...arrows].sort((x, y) => depth(y) - depth(x))) {
    if (implied.has(arrow)) continue;
    const above = selfAndAbove(arrow.to);
    for (const from of selfAndAbove(arrow.from)) {
      const tos = targets.get(from);
      if (tos === undefined) continue;
      for (const to of above) {
        const other = tos.get(to);
        if (other !== undefined && other !== arrow) implied.add(other);
      }
    }
  }
  return arrows.filter((arrow) => !implied.has(arrow));
}

// The nodes, arrows and frame of a diagram whose framed elements are `framedIds`: { nodes, arrows, frame }.
export function drawing(framedIds, frameText, gap, base) {
  const framed = new Set(framedIds);
  const pairs = Object.fromEntries(STYLES.map((style) => [style, new Map()]));
  const add = (style, from, to, kind = null, titles = []) => {
    if (!framed.has(from) && !framed.has(to)) return;
    const key = JSON.stringify([from, to]);
    if (!pairs[style].has(key)) pairs[style].set(key, { from, to, kinds: new Set(), titles: new Set() });
    const pair = pairs[style].get(key);
    if (kind !== null) pair.kinds.add(kind);
    for (const title of titles) pair.titles.add(title);
  };
  for (const id of framed) {
    const links = base.links.get(id);
    for (const entry of [...links.from, ...links.to]) add('import', entry.from, entry.to);
    for (const link of [...links.out, ...links.in]) add('runtime', link.from, link.to, link.kind, link.titles);
  }
  for (const entry of gap) add('gap', entry.from, entry.to);

  const text = {
    import: () => '',
    runtime: (pair) => [...[...pair.kinds].sort(cmp), ...[...pair.titles].sort(cmp).map((title) => `"${title}"`)].join(', '),
    gap: () => 'known gap',
  };
  const arrows = STYLES.flatMap((style) => {
    const drawn = style === 'gap' ? [...pairs[style].values()] : hideImplied([...pairs[style].values()]);
    return drawn.map((pair) => ({
      from: pair.from, to: pair.to, style, dashed: style === 'runtime', red: style === 'gap', text: text[style](pair),
    }));
  }).sort((x, y) => cmp(x.from, y.from) || cmp(x.to, y.to) || STYLES.indexOf(x.style) - STYLES.indexOf(y.style));

  // Spec, Drawing rules: a neighbour is drawn only when one of its arrows is.
  const neighbours = new Set(arrows.flatMap((arrow) => [arrow.from, arrow.to]).filter((id) => !framed.has(id)));
  const nodeText = (id) => {
    const title = base.titles.elements.get(id) ?? id;
    if (framed.has(id)) return title;
    const areas = base.byElement.get(id) ?? [];
    return `${title} (${areas.length > 0 ? areas[0] : 'no area'})`;
  };
  const nodes = [...framed, ...neighbours].sort(cmp).map((id) => ({ id, text: nodeText(id) }));
  return { nodes, arrows, frame: { text: frameText, ids: [...framed].sort(cmp) } };
}

// The diagram text, or null when it has more than ARROW_LIMIT arrows.
export function drawingText(picture) {
  return flowchart(picture.nodes, picture.arrows, picture.frame);
}

export const TOO_MANY_ARROWS = `The diagram has more than ${ARROW_LIMIT} arrows and is not drawn; the tables list everything.`;
