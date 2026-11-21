// Decisions, contracts and open questions printed in full, as document-tree blocks. `ctx`: { doc (the path of the
// document being built), byElement (areasByElement), titles (titlesOf), decisions (Map of id to decision), area (the
// area of an area document, or null) }.
import { heading, paragraph, list, docLink } from './tree.mjs';
import { areaDoc, areasOf, capabilityDoc, elementTarget, recordElements, recordTarget, relative } from './facts.mjs';

const has = (record, key) => Object.hasOwn(record, key);
const separated = (parts) => parts.flatMap((part, index) => (index === 0 ? [part] : [', ', part]));
// Spec, Shared rules: an id is shown as written, with its title beside it.
const titled = (groups) => groups.flatMap((group, index) => (index === 0 ? group : [', ', ...group]));
const withTitle = (id, href, title) => [docLink(id, href), ` (${title ?? id})`];

// Spec, Area and Change record: an element printed in full is a table row: id, title, description, code, rules, tags.
export const ELEMENT_HEADER = ['Element', 'Title', 'Description', 'Code', 'Rules', 'Tags'];
export const elementCells = (element) => [[element.title], [element.description ?? ''], [element.code.join(', ')],
  [element.rules.join(', ')], [element.tags.map((tag) => `#${tag}`).join(' ')]];

export const elementLinks = (ids, ctx) => titled(ids.map((id) =>
  withTitle(id, relative(ctx.doc, elementTarget(id, ctx.byElement)), ctx.titles.elements.get(id))));
export const areaLinks = (names, ctx) => titled(names.map((name) =>
  withTitle(name, relative(ctx.doc, areaDoc(name)), ctx.titles.areas.get(name))));
export const capabilityLinks = (names, ctx) => titled(names.map((name) =>
  withTitle(name, relative(ctx.doc, capabilityDoc(name)), ctx.titles.capabilities.get(name))));

function decisionLink(id, ctx) {
  const decision = ctx.decisions.get(id);
  return decision === undefined ? id : docLink(id, relative(ctx.doc, recordTarget('decisions', decision, ctx.byElement)));
}

// Spec, Area: the other areas the record is in ("Also binds" in an area document; "Areas" elsewhere).
function areasItem(kind, record, ctx, alsoLabel) {
  const names = areasOf(recordElements(kind, record), ctx.byElement).filter((name) => name !== ctx.area);
  if (names.length === 0) return [];
  return [[ctx.area === null ? 'Areas: ' : alsoLabel, ...areaLinks(names, ctx)]];
}

export function decisionBlocks(decision, ctx, level = 3) {
  const items = [['Reason: ', decision.reason ?? 'Reason not known']];
  if (decision.rejected.length > 0) items.push(['Rejected: ', decision.rejected.join('; ')]);
  if (has(decision, 'obligations')) items.push(['Obligations: ', decision.obligations.join('; ')]);
  if (has(decision, 'owner')) items.push(['Owner: ', ...elementLinks([decision.owner], ctx)]);
  if (has(decision, 'compatibility')) items.push(['Compatibility: ', decision.compatibility]);
  if ((decision.capabilities ?? []).length > 0) items.push(['Capabilities: ', ...capabilityLinks(decision.capabilities, ctx)]);
  items.push(decision.status === 'superseded'
    ? ['Status: superseded by ', decisionLink(decision.superseded_by, ctx)]
    : ['Status: ', decision.status]);
  items.push(['Evidence: ', decision.evidence]);
  if (decision.sources.length > 0) items.push(['Sources: ', decision.sources.join('; ')]);
  if (has(decision, 'note')) items.push(['Note: ', decision.note]);
  if (decision.binds.length > 0) items.push(['Binds: ', ...elementLinks(decision.binds, ctx)]);
  items.push(...areasItem('decisions', decision, ctx, 'Also binds: '));
  return [heading(level, decision.id), paragraph(decision.decision), list(items)];
}

export function contractBlocks(contract, ctx, level = 3) {
  const items = [
    ['Owner: ', ...elementLinks([contract.owner], ctx)],
    ['Bound: ', ...elementLinks(contract.bound, ctx)],
    ['Obligations: ', contract.obligations.join('; ')],
    ['Compatibility: ', contract.compatibility ?? 'No rule stated'],
  ];
  if ((contract.notes ?? []).length > 0) items.push(['Notes: ', contract.notes.join('; ')]);
  if ((contract.decisions ?? []).length > 0) items.push(['Decisions: ', ...separated(contract.decisions.map((id) => decisionLink(id, ctx)))]);
  if ((contract.capabilities ?? []).length > 0) items.push(['Capabilities: ', ...capabilityLinks(contract.capabilities, ctx)]);
  items.push(...areasItem('contracts', contract, ctx, 'Also in: '));
  return [heading(level, `${contract.id}: ${contract.name}`), list(items)];
}

export function holeBlocks(hole, ctx, level = 3) {
  const items = [];
  if (hole.binds.length > 0) items.push(['Binds: ', ...elementLinks(hole.binds, ctx)]);
  items.push(['Evidence: ', hole.evidence]);
  if (has(hole, 'note')) items.push(['Note: ', hole.note]);
  return [heading(level, hole.id), paragraph(hole.what), list(items)];
}
