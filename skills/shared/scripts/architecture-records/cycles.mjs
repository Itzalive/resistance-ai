// Proposes the relationships a baseline leaves out of each cycle (spec 2026-11-21, "`cycles`"). Pure: reads and writes
// nothing.
import { clean } from '../architecture-delta/errors.mjs';
import { cmp } from '../architecture-delta/report.mjs';
import { ancestorsOrSelf, moduleMapper } from '../architecture-delta/match.mjs';

export const SEARCH_LIMIT = 20;

const key = (from, to) => `${from}\u0000${to}`;
const byPair = (x, y) => cmp(x.from, y.from) || cmp(x.to, y.to);

// Lists compared item by item; a list that is a prefix of another comes first.
function cmpLists(x, y, cmpItem) {
  for (let i = 0; i < Math.min(x.length, y.length); i += 1) {
    const c = cmpItem(x[i], y[i]);
    if (c !== 0) return c;
  }
  return x.length - y.length;
}

// The sibling pair a relationship gives: the children of the nearest common ancestor of its ends (the top level when
// they have none) that hold the ends. Null when one end is inside the other.
function siblingPair(from, to) {
  const a = ancestorsOrSelf(from);
  const b = ancestorsOrSelf(to);
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i += 1;
  if (i === a.length || i === b.length) return null;
  return { parent: i === 0 ? null : a[i - 1], from: a[i], to: b[i] };
}

// Strongly connected groups of two or more siblings (Tarjan), each sorted.
function strongGroups(arcs) {
  const out = new Map();
  for (const arc of arcs) {
    if (!out.has(arc.from)) out.set(arc.from, []);
    if (!out.has(arc.to)) out.set(arc.to, []);
    out.get(arc.from).push(arc.to);
  }
  const index = new Map();
  const low = new Map();
  const stack = [];
  const onStack = new Set();
  const groups = [];
  let next = 0;
  const visit = (v) => {
    index.set(v, next);
    low.set(v, next);
    next += 1;
    stack.push(v);
    onStack.add(v);
    for (const w of out.get(v)) {
      if (!index.has(w)) {
        visit(w);
        low.set(v, Math.min(low.get(v), low.get(w)));
      } else if (onStack.has(w)) {
        low.set(v, Math.min(low.get(v), index.get(w)));
      }
    }
    if (low.get(v) === index.get(v)) {
      const group = [];
      let w;
      do {
        w = stack.pop();
        onStack.delete(w);
        group.push(w);
      } while (w !== v);
      if (group.length > 1) groups.push(group.sort(cmp));
    }
  };
  for (const v of [...out.keys()].sort(cmp)) if (!index.has(v)) visit(v);
  return groups;
}

// Whether the arcs not in `mask` leave the n nodes with no cycle (nodes and arcs as small integers, n <= 20).
function acyclicWithout(n, arcs, mask) {
  const into = new Array(n).fill(0);
  for (let i = 0; i < arcs.length; i += 1) if ((mask & (1 << i)) === 0) into[arcs[i][1]] |= 1 << arcs[i][0];
  let remaining = (1 << n) - 1;
  let progress = true;
  while (remaining !== 0 && progress) {
    progress = false;
    for (let v = 0; v < n; v += 1) {
      if ((remaining & (1 << v)) !== 0 && (into[v] & remaining) === 0) {
        remaining &= ~(1 << v);
        progress = true;
      }
    }
  }
  return remaining === 0;
}

// The best set of candidate pairs to leave out: fewest relationships, then fewest distinct module edges, then the
// first sorted list of pairs. `candidates` are sorted by pair; each has `rels` (relationships) and `edges` (a Set).
function bestLeaveOut(siblings, candidates, tick) {
  const position = new Map(siblings.map((id, i) => [id, i]));
  const arcs = candidates.map((c) => [position.get(c.from), position.get(c.to)]);
  let best = null;
  for (let mask = 0; mask < 2 ** candidates.length; mask += 1) {
    if ((mask & 4095) === 0) tick();
    let rels = 0;
    for (let i = 0; i < candidates.length; i += 1) if ((mask & (1 << i)) !== 0) rels += candidates[i].rels.length;
    if (best !== null && rels > best.rels) continue;
    if (!acyclicWithout(siblings.length, arcs, mask)) continue;
    const chosen = candidates.filter((_, i) => (mask & (1 << i)) !== 0);
    const edges = new Set();
    for (const c of chosen) for (const e of c.edges) edges.add(e);
    const found = { rels, edges: edges.size, chosen };
    const order = best === null ? -1
      : (found.rels - best.rels) || (found.edges - best.edges) || cmpLists(found.chosen, best.chosen, byPair);
    if (order < 0) best = found;
  }
  return best.chosen;
}

// `model` holds `elements` (id, code) and import `relationships` (from, to); `edges` are dependency-file edges.
export function findCycles(model, edges, separator, tick = () => {}) {
  const rels = new Map();
  for (const r of model.relationships) {
    if (!rels.has(key(r.from, r.to))) rels.set(key(r.from, r.to), { from: r.from, to: r.to, edges: new Set() });
  }
  // A dependency edge counts for every relationship whose source holds its source's element and whose target holds
  // its target's.
  const mapModule = moduleMapper(model.elements, separator);
  edges.forEach(([from, to], index) => {
    if (index > 0 && index % 10000 === 0) tick();
    const source = mapModule(from);
    const target = mapModule(to);
    if (source === null || target === null) return;
    for (const a of ancestorsOrSelf(source)) for (const b of ancestorsOrSelf(target)) rels.get(key(a, b))?.edges.add(index);
  });
  // The candidate pairs of each level: parent -> sibling pair -> the relationships that give it.
  const levels = new Map();
  for (const rel of rels.values()) {
    const pair = siblingPair(rel.from, rel.to);
    if (pair === null) continue;
    const level = JSON.stringify(pair.parent);
    if (!levels.has(level)) levels.set(level, { parent: pair.parent, arcs: new Map() });
    const arcs = levels.get(level).arcs;
    if (!arcs.has(key(pair.from, pair.to))) arcs.set(key(pair.from, pair.to), { from: pair.from, to: pair.to, rels: [], edges: new Set() });
    const arc = arcs.get(key(pair.from, pair.to));
    arc.rels.push(rel);
    for (const e of rel.edges) arc.edges.add(e);
  }
  const groups = [];
  for (const { parent, arcs } of levels.values()) {
    for (const siblings of strongGroups([...arcs.values()])) {
      tick();
      const inside = new Set(siblings);
      const candidates = [...arcs.values()].filter((a) => inside.has(a.from) && inside.has(a.to)).sort(byPair);
      const tooLarge = candidates.length > SEARCH_LIMIT;
      const chosen = tooLarge ? [] : bestLeaveOut(siblings, candidates, tick);
      const leaveOut = chosen.flatMap((c) => c.rels).sort(byPair)
        .map((r) => ({ from: clean(r.from), to: clean(r.to), module_edges: r.edges.size }));
      groups.push({ parent, siblings, leave_out: leaveOut, too_large: tooLarge ? candidates.length : null });
    }
  }
  const depth = (parent) => (parent === null ? 0 : parent.split('.').length);
  groups.sort((x, y) => depth(x.parent) - depth(y.parent) || cmp(x.parent ?? '', y.parent ?? '')
    || cmpLists(x.siblings, y.siblings, cmp));
  return {
    groups: groups.map((g) => ({ ...g, parent: g.parent === null ? null : clean(g.parent), siblings: g.siblings.map(clean) })),
    summary: {
      relationships: groups.reduce((n, g) => n + g.leave_out.length, 0),
      groups: groups.length,
      too_large: groups.filter((g) => g.too_large !== null).length,
    },
  };
}

export function cyclesText(result) {
  const lines = [];
  for (const group of result.groups) {
    lines.push(`group ${group.parent ?? 'top level'}: ${group.siblings.join(', ')}`);
    if (group.too_large !== null) lines.push(`too large: ${group.too_large} candidate pairs`);
    for (const r of group.leave_out) lines.push(`leave out ${r.from} -> ${r.to} (${r.module_edges} module edges)`);
  }
  const s = result.summary;
  lines.push(`${s.relationships} relationships to leave out in ${s.groups} groups, ${s.too_large} too large`);
  return `${lines.join('\n')}\n`;
}
