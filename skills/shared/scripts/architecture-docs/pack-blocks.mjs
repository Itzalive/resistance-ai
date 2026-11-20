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

const has = (record, key) => Object.hasOwn(record, key);
const texts = (items) => items.map(oneLine).join('; ');
const field = (key, value) => `${key}: ${value}`;
// A multi-line field: the key goes on its first line, and the multi-line rule guards every line after it.
const multiField = (key, text) => multiLine(field(key, text));

// Spec, AI pack, record blocks: the fields in the order the area document prints them; an empty list is left out.
export function decisionBlock(id, ctx) {
  const decision = ctx.records.decisions.get(id);
  const lines = [`### ${id}`, multiLine(decision.decision)];
  lines.push(decision.reason === null ? field('reason', 'not known') : multiField('reason', decision.reason));
  if (decision.rejected.length > 0) lines.push(field('rejected', texts(decision.rejected)));
  if (has(decision, 'obligations')) lines.push(field('obligations', texts(decision.obligations)));
  if (has(decision, 'owner')) lines.push(field('owner', ref('elements', decision.owner, ctx)));
  if (has(decision, 'compatibility')) lines.push(field('compatibility', oneLine(decision.compatibility)));
  if ((decision.capabilities ?? []).length > 0) lines.push(field('capabilities', refs('capabilities', decision.capabilities, ctx)));
  lines.push(field('status', decision.status));
  if (decision.status === 'superseded') lines.push(field('superseded_by', ref('decisions', decision.superseded_by, ctx)));
  lines.push(field('evidence', oneLine(decision.evidence)));
  if (decision.sources.length > 0) lines.push(field('sources', texts(decision.sources)));
  if (has(decision, 'note')) lines.push(multiField('note', decision.note));
  if (decision.binds.length > 0) lines.push(field('binds', refs('elements', decision.binds, ctx)));
  return lines.join('\n');
}

export function contractBlock(id, ctx) {
  const contract = ctx.records.contracts.get(id);
  const lines = [
    `### ${id}: ${oneLine(contract.name)}`,
    field('owner', ref('elements', contract.owner, ctx)),
    field('bound', refs('elements', contract.bound, ctx)),
    field('obligations', texts(contract.obligations)),
    field('compatibility', contract.compatibility === null ? 'no rule stated' : oneLine(contract.compatibility)),
  ];
  if ((contract.notes ?? []).length > 0) lines.push(field('notes', texts(contract.notes)));
  if ((contract.decisions ?? []).length > 0) lines.push(field('decisions', refs('decisions', contract.decisions, ctx)));
  if ((contract.capabilities ?? []).length > 0) lines.push(field('capabilities', refs('capabilities', contract.capabilities, ctx)));
  return lines.join('\n');
}

export function holeBlock(id, ctx) {
  const hole = ctx.records.holes.get(id);
  const lines = [`### ${id}`, multiLine(hole.what)];
  if (hole.binds.length > 0) lines.push(field('binds', refs('elements', hole.binds, ctx)));
  lines.push(field('evidence', oneLine(hole.evidence)));
  if (has(hole, 'note')) lines.push(multiField('note', hole.note));
  return lines.join('\n');
}

// Spec, AI pack, known-gap lines.
export function gapLine(entry, ctx) {
  const closeBy = entry.close_by === null ? '' : ` (close by ${oneLine(entry.close_by)})`;
  return `- ${ref('elements', entry.from, ctx)} -> ${ref('elements', entry.to, ctx)}: ${oneLine(entry.reason)}${closeBy}`;
}

// Spec, AI pack, step lines: `<n>. <from> -> <to>[ (reply)][: <label>] (<kinds>)`.
export function stepLine(step, number, ctx) {
  const reply = step.reply ? ' (reply)' : '';
  const label = step.label === null ? '' : `: ${oneLine(step.label)}`;
  return `${number}. ${ref('elements', step.from, ctx)} -> ${ref('elements', step.to, ctx)}${reply}${label} (${step.kinds.join(', ')})`;
}
