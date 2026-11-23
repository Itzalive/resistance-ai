// The drawing rules (spec, What each document holds, Drawing rules): framed elements and their neighbours, import,
// runtime and known-gap arrows, implied arrows hidden. `base` comes from `documentBase`.
import { cmp } from '../architecture-delta/report.mjs';
import { MARKDOWN_TOO_MANY, SVG_ARROW_LIMIT, flowchart } from './mermaid.mjs';
import { diagram, paragraph, table } from './tree.mjs';

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

// Spec, Area diagrams (#44), Grouped neighbours: a neighbour's group is its outermost ancestor, or itself, that is an
// element, is not framed and holds no framed element.
function groupOf(id, framed, isElement) {
  const holdsFramed = (candidate) => framed.has(candidate) || [...framed].some((other) => other.startsWith(`${candidate}.`));
  return selfAndAbove(id).reverse().find((candidate) => isElement(candidate) && !holdsFramed(candidate)) ?? id;
}

// Spec, Area diagrams (#44), Implied imports inside the area: taken by from then to, an import between two framed
// elements is left out when its target is still reachable from its source along the other kept ones.
function reduceImports(pairs, framed) {
  const inside = pairs.filter((pair) => framed.has(pair.from) && framed.has(pair.to)).sort((x, y) => cmp(x.from, y.from) || cmp(x.to, y.to));
  const kept = new Set(inside);
  const reaches = (from, to, skip) => {
    const seen = new Set([from]);
    const queue = [from];
    while (queue.length > 0) {
      const at = queue.shift();
      for (const pair of kept) {
        if (pair === skip || pair.from !== at || seen.has(pair.to)) continue;
        if (pair.to === to) return true;
        seen.add(pair.to);
        queue.push(pair.to);
      }
    }
    return false;
  };
  for (const pair of inside) if (reaches(pair.from, pair.to, pair)) kept.delete(pair);
  return pairs.filter((pair) => !inside.includes(pair) || kept.has(pair));
}

// Spec, Area diagrams (#44): neighbours redrawn as their groups, arrows of one style between the same two nodes merged.
// Returns the merged pairs per style and how many drawn neighbours each group stands for.
function groupPairs(drawnByStyle, framed, isElement) {
  const members = new Map();
  const end = (id) => {
    if (framed.has(id)) return id;
    const group = groupOf(id, framed, isElement);
    if (!members.has(group)) members.set(group, new Set());
    members.get(group).add(id);
    return group;
  };
  const merged = Object.fromEntries(STYLES.map((style) => [style, new Map()]));
  for (const style of STYLES) {
    for (const pair of drawnByStyle[style]) {
      const from = end(pair.from);
      const to = end(pair.to);
      if (from === to) continue;
      const key = JSON.stringify([from, to]);
      if (!merged[style].has(key)) merged[style].set(key, { from, to, kinds: new Set(), titles: new Set() });
      for (const kind of pair.kinds) merged[style].get(key).kinds.add(kind);
      for (const title of pair.titles) merged[style].get(key).titles.add(title);
    }
  }
  // A group standing for one neighbour is that neighbour.
  const single = new Map([...members].filter(([, ids]) => ids.size === 1).map(([group, ids]) => [group, [...ids][0]]));
  const asSingle = (id) => single.get(id) ?? id;
  const result = Object.fromEntries(STYLES.map((style) => [style, [...merged[style].values()]
    .map((pair) => ({ ...pair, from: asSingle(pair.from), to: asSingle(pair.to) }))]));
  const sizes = new Map([...members].filter(([, ids]) => ids.size > 1).map(([group, ids]) => [group, ids.size]));
  return { pairs: result, sizes };
}

// The nodes, arrows and frame of a diagram whose framed elements are `framedIds`: { nodes, arrows, frame }. `marks` maps
// a framed id to `added` or `changed` (a change record's diagram); a marked node is labelled `<title> (<mark>)`.
// `options.area` applies the area-diagram rules of #44: grouped neighbours and implied imports left out, unless
// `options.keepImplied` (the matrix).
export function drawing(framedIds, frameText, gap, base, marks = new Map(), options = {}) {
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
  let drawnByStyle = Object.fromEntries(STYLES.map((style) => [style,
    style === 'gap' ? [...pairs[style].values()] : hideImplied([...pairs[style].values()])]));
  let sizes = new Map();
  if (options.area === true) {
    const isElement = (id) => base.titles.elements.has(id);
    ({ pairs: drawnByStyle, sizes } = groupPairs(drawnByStyle, framed, isElement));
    if (options.keepImplied !== true) drawnByStyle.import = reduceImports(drawnByStyle.import, framed);
  }
  const arrows = STYLES.flatMap((style) => drawnByStyle[style].map((pair) => ({
    from: pair.from, to: pair.to, style, dashed: style === 'runtime', red: style === 'gap', text: text[style](pair),
  }))).sort((x, y) => cmp(x.from, y.from) || cmp(x.to, y.to) || STYLES.indexOf(x.style) - STYLES.indexOf(y.style));

  // Spec, Drawing rules: a neighbour is drawn only when one of its arrows is.
  const neighbours = new Set(arrows.flatMap((arrow) => [arrow.from, arrow.to]).filter((id) => !framed.has(id)));
  const nodeText = (id) => {
    const title = base.titles.elements.get(id) ?? id;
    if (framed.has(id)) return marks.has(id) ? `${title} (${marks.get(id)})` : title;
    if (sizes.has(id)) return `${title} (${sizes.get(id)} elements)`;
    const areas = base.byElement.get(id) ?? [];
    return `${title} (${areas.length > 0 ? areas[0] : 'no area'})`;
  };
  const nodes = [...framed, ...neighbours].sort(cmp).map((id) => ({ id, text: nodeText(id) }));
  return { nodes, arrows, frame: { text: frameText, ids: [...framed].sort(cmp) } };
}

// The diagram text, or null when it has more than ARROW_LIMIT arrows.
function drawingText(picture) {
  return flowchart(picture.nodes, picture.arrows, picture.frame);
}

// The diagram block of a drawing, or null when it has more than SVG_ARROW_LIMIT arrows. Over ARROW_LIMIT arrows only
// the HTML page draws it; the Markdown document shows a note.
export function drawingBlock(picture) {
  if (picture.arrows.length > SVG_ARROW_LIMIT) return null;
  return diagram(drawingText(picture), { kind: 'flowchart', ...picture }, MARKDOWN_TOO_MANY);
}

// Spec, Area diagrams (#44), A matrix for a large area.
export const AREA_MATRIX_BOXES = 20;
const LETTERS = { import: 'u', runtime: 'r', gap: 'g' };

// The matrix paragraph and table of a picture: one row and one numbered column per box, framed boxes first.
export function matrixBlocks(picture) {
  const framed = new Set(picture.frame.ids);
  const boxes = [...picture.nodes.filter((node) => framed.has(node.id)), ...picture.nodes.filter((node) => !framed.has(node.id))];
  const cell = (from, to) => {
    if (from === to) return ['-'];
    const styles = new Set(picture.arrows.filter((arrow) => arrow.from === from && arrow.to === to).map((arrow) => arrow.style));
    return [STYLES.filter((style) => styles.has(style)).map((style) => LETTERS[style]).join(' ')];
  };
  const rows = boxes.map((row, at) => [[`${at + 1}. ${row.text}`], ...boxes.map((column) => cell(row.id, column.id))]);
  return [
    paragraph(`Too many boxes to draw (${boxes.length}); a row uses its column: u import, r runtime link, g known gap.`),
    table(['Box', ...boxes.map((_, at) => String(at + 1))], rows),
  ];
}

export const TOO_MANY_ARROWS = `The diagram has more than ${SVG_ARROW_LIMIT} arrows and is not drawn; the tables list everything.`;
