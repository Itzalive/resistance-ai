// The improvement list (spec, What each document holds, Improvement list): facts only, nothing judged or ranked, in
// eight fixed groups, each a heading with its count and its items sorted by id, by pair or by module.
import { cmp } from '../architecture-delta/report.mjs';
import { doc, heading, paragraph, list, docLink } from './tree.mjs';
import { IMPROVEMENTS, areasOf, recordElements, recordTarget, relative } from './facts.mjs';
import { elementLinks, areaLinks } from './records-doc.mjs';

export const IMPROVEMENTS_TITLE = 'Improvement list';
const CYCLE = 'cycle in current code';
const NOT_BUILT = ['partly-built', 'planned'];

const byId = (x, y) => cmp(x.id, y.id);
const byPair = (x, y) => cmp(x.from, y.from) || cmp(x.to, y.to);
const parentOf = (id) => id.slice(0, id.lastIndexOf('.'));

// Spec (amended): an item names its id, pair or module, then its details after `: `, separated by `; `, then its areas,
// or "Not in any area"; `areas` is null for an unmapped module, which has no areas part.
function item(main, details, areas, ctx) {
  const parts = [...main];
  details.forEach((detail, at) => parts.push(at === 0 ? ': ' : '; ', ...detail));
  if (areas !== null) parts.push('. ', ...(areas.length > 0 ? ['Areas: ', ...areaLinks(areas, ctx)] : ['Not in any area']));
  return parts;
}

function gapItem(entry, withReason, ctx) {
  const details = [];
  if (withReason) details.push([entry.reason]);
  if (entry.close_by !== null) details.push([`close by ${entry.close_by}`]);
  const main = [...elementLinks([entry.from], ctx), ' -> ', ...elementLinks([entry.to], ctx)];
  return item(main, details, areasOf([entry.from, entry.to], ctx.byElement), ctx);
}

function recordItem(kind, record, details, ctx) {
  const main = [docLink(record.id, relative(ctx.doc, recordTarget(kind, record, ctx.byElement)))];
  return item(main, details, areasOf(recordElements(kind, record), ctx.byElement), ctx);
}

const elementItem = (element, ctx) => item(elementLinks([element.id], ctx), [], ctx.byElement.get(element.id) ?? [], ctx);

// Spec, group 8: no `code`, no child, kind not `external`, and not a coverage edge node.
function ownsNothing(data) {
  const parents = new Set(data.elements.filter((element) => element.id.includes('.')).map((element) => parentOf(element.id)));
  const edges = new Set((data.coverage?.edge_nodes ?? []).map((node) => node.element));
  return data.elements.filter((element) => element.code.length === 0 && !parents.has(element.id) && element.kind !== 'external'
    && !edges.has(element.id));
}

export function buildImprovements(data, gap, base) {
  const ctx = { ...base, doc: IMPROVEMENTS, area: null };
  const sortedGap = [...gap].sort(byPair);
  const decisions = [...data.decisions].sort(byId);
  const groups = [
    ['Cycles in current code', sortedGap.filter((entry) => entry.reason === CYCLE).map((entry) => gapItem(entry, false, ctx))],
    ['Other known breaches', sortedGap.filter((entry) => entry.reason !== CYCLE).map((entry) => gapItem(entry, true, ctx))],
    ['Open questions', [...data.holes].sort(byId).map((hole) =>
      recordItem('holes', hole, hole.binds.length > 0 ? [['binds ', ...elementLinks(hole.binds, ctx)]] : [], ctx))],
    ['Decisions not yet fully built', decisions.filter((decision) => NOT_BUILT.includes(decision.status))
      .map((decision) => recordItem('decisions', decision, [['status ', decision.status]], ctx))],
    ['Decisions with no known reason', decisions.filter((decision) => decision.reason === null)
      .map((decision) => recordItem('decisions', decision, [], ctx))],
    ['Unmapped code', [...(data.coverage?.unmapped ?? [])].sort((x, y) => cmp(x.module, y.module))
      .map((entry) => item([entry.module], [[entry.reason]], null, ctx))],
    ['Elements in no area', [...data.elements].sort(byId).filter((element) => (ctx.byElement.get(element.id) ?? []).length === 0)
      .map((element) => elementItem(element, ctx))],
    ['Elements that own nothing', ownsNothing(data).sort(byId).map((element) => elementItem(element, ctx))],
  ];
  const blocks = [paragraph('Facts from the architecture model and the known-gap file; nothing here is judged or ranked.')];
  for (const [name, entries] of groups) {
    blocks.push(heading(2, `${name} (${entries.length})`), entries.length === 0 ? paragraph('None.') : list(entries));
  }
  return doc(IMPROVEMENTS_TITLE, blocks);
}
