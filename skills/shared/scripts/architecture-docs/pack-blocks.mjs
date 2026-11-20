// The pack's blocks (spec, AI pack): the element block, record blocks, known-gap lines and step lines. Every id not
// held in the slice being written is followed by its pack file in brackets: the first area's slice, or README.md for
// a fact outside any area; a capability's pack file is its own slice. `ctx` comes from `packContext`.
import { cmp } from '../architecture-delta/report.mjs';
import { areasByElement, areasOf, isCrossCutting, recordElements } from './facts.mjs';
import { oneLine, multiLine } from './pack-text.mjs';

export const PACK_INDEX = 'README.md';
export const packArea = (name) => `areas/${name}.md`;
export const packCapability = (name) => `capabilities/${name}.md`;

const KINDS = ['elements', 'decisions', 'contracts', 'holes', 'capabilities'];
// `held`: the ids a slice holds in full, as lists per kind (a missing kind holds none).
const heldSets = (held) => Object.fromEntries(KINDS.map((kind) => [kind, new Set(held[kind] ?? [])]));

export function packContext(data, held = {}) {
  return {
    data,
    byElement: areasByElement(data),
    elements: new Map(data.elements.map((element) => [element.id, element])),
    records: {
      decisions: new Map(data.decisions.map((record) => [record.id, record])),
      contracts: new Map(data.contracts.map((record) => [record.id, record])),
      holes: new Map(data.holes.map((record) => [record.id, record])),
    },
    held: heldSets(held),
  };
}

// The same context for another slice: the maps are kept, only the held sets change.
export const withHeld = (ctx, held) => ({ ...ctx, held: heldSets(held) });

// An id that names nothing in the model fails the build (exit 2, `internal`): the records and the known-gap file are
// checked on load, so it can only be a fault in the tool.
function packFileOf(kind, id, ctx) {
  if (kind === 'capabilities') return packCapability(id);
  const record = kind === 'elements' ? null : ctx.records[kind].get(id);
  if (kind === 'elements' ? !ctx.byElement.has(id) : record === undefined) throw new Error(`${id} is not in the model`);
  const areas = kind === 'elements' ? ctx.byElement.get(id) : areasOf(recordElements(kind, record), ctx.byElement);
  return areas.length > 0 ? packArea(areas[0]) : PACK_INDEX;
}

// Spec, AI pack: the suffix follows the id and the parenthetical that belongs to it.
export function ref(kind, id, ctx, note = '') {
  return ctx.held[kind].has(id) ? `${id}${note}` : `${id}${note} [${packFileOf(kind, id, ctx)}]`;
}

const refs = (kind, ids, ctx) => ids.map((id) => ref(kind, id, ctx)).join(', ');

function runtimeLines(id, ctx) {
  const byOther = (x, y) => cmp(x.other, y.other) || cmp(x.link.kind, y.link.kind);
  const outgoing = ctx.data.runtime.filter((link) => link.from === id).map((link) => ({ arrow: '->', other: link.to, link })).sort(byOther);
  const incoming = ctx.data.runtime.filter((link) => link.to === id).map((link) => ({ arrow: '<-', other: link.from, link })).sort(byOther);
  return [...outgoing, ...incoming].map(({ arrow, other, link }) => {
    const detail = [link.kind, ...link.titles.map((title) => `"${oneLine(title)}"`)].join(', ');
    return `runtime: ${arrow} ${ref('elements', other, ctx, ` (${detail})`)}`;
  });
}

// Spec, AI pack, element block: a line or a `·` part with nothing to show is left out.
export function elementBlock(id, ctx) {
  const element = ctx.elements.get(id);
  const head = [`kind ${element.kind}`];
  if (element.tags.length > 0) head.push(`tags ${element.tags.map((tag) => `#${tag}`).join(' ')}`);
  if (element.code.length > 0) head.push(`code ${element.code.join(', ')}`);
  if (element.rules.length > 0) head.push(`rules ${element.rules.join(', ')}`);
  const lines = [`### ${id}: ${oneLine(element.title)}`, head.join(' · ')];
  if (element.description !== null) lines.push(multiLine(element.description));
  const uses = [...new Set(ctx.data.allowed.filter((entry) => entry.from === id).map((entry) => entry.to))].sort(cmp);
  const usedBy = [...new Set(ctx.data.allowed.filter((entry) => entry.to === id).map((entry) => entry.from))].sort(cmp);
  if (uses.length > 0) lines.push(`uses: ${refs('elements', uses, ctx)}`);
  if (usedBy.length > 0) lines.push(`used by: ${refs('elements', usedBy, ctx)}`);
  lines.push(...runtimeLines(id, ctx));
  const boundBy = ctx.data.decisions.filter((decision) => decision.binds.includes(id))
    .map((decision) => ref('decisions', decision.id, ctx, isCrossCutting(decision) ? ' (cross-cutting)' : ''));
  if (boundBy.length > 0) lines.push(`bound by: ${boundBy.join(', ')}`);
  return lines.join('\n');
}
