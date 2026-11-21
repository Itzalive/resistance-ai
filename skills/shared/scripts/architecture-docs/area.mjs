// An area document (spec, What each document holds, Area): title and description, the diagram, the elements, their
// dependencies, and the area's decisions, contracts, open questions, known-gap entries and capabilities.
import { cmp } from '../architecture-delta/report.mjs';
import { doc, heading, paragraph, table, diagram, docLink, orSay } from './tree.mjs';
import { areaDoc, areaCapabilities, areaRecords, elementTarget, relative } from './facts.mjs';
import {
  ELEMENT_HEADER, decisionBlocks, contractBlocks, holeBlocks, elementCells, elementLinks, areaLinks, capabilityLinks,
} from './records-doc.mjs';
import { drawing, drawingText, TOO_MANY_ARROWS } from './area-diagram.mjs';

// An id is plain text in the document that holds it, a link elsewhere.
function idCell(id, ctx) {
  const target = elementTarget(id, ctx.byElement);
  return target === ctx.doc ? [id] : [docLink(id, relative(ctx.doc, target))];
}

const otherAreas = (id, ctx) => {
  const names = ctx.byElement.get(id) ?? [];
  return names.length > 0 ? areaLinks(names, ctx) : ['Not in any area'];
};

// Spec, Area, Dependencies: what each area element may use and what may use it, and its runtime links, each with the
// other end's areas. Rows: uses, used by, runtime to, runtime from, each sorted by the other end (runtime by kind next).
function dependencyRows(area, ctx) {
  const rows = [];
  for (const id of area.elements) {
    const links = ctx.links.get(id);
    const row = (relation, other, detail) => [idCell(id, ctx), [relation], elementLinks([other], ctx), [detail], otherAreas(other, ctx)];
    for (const other of [...new Set(links.from.map((entry) => entry.to))].sort(cmp)) rows.push(row('uses', other, ''));
    for (const other of [...new Set(links.to.map((entry) => entry.from))].sort(cmp)) rows.push(row('used by', other, ''));
    const detail = (link) => [link.kind, ...link.titles.map((title) => `"${title}"`)].join(', ');
    const byOther = (x, y) => cmp(x.other, y.other) || cmp(x.link.kind, y.link.kind);
    const outgoing = links.out.map((link) => ({ other: link.to, link })).sort(byOther);
    const incoming = links.in.map((link) => ({ other: link.from, link })).sort(byOther);
    for (const { other, link } of outgoing) rows.push(row('runtime to', other, detail(link)));
    for (const { other, link } of incoming) rows.push(row('runtime from', other, detail(link)));
  }
  return rows;
}

export function buildArea(data, gap, area, base) {
  const ctx = { ...base, doc: areaDoc(area.name), area: area.name };
  const records = areaRecords(data, gap, area);
  const blocks = [];
  if (area.description !== null) blocks.push(paragraph(area.description));

  blocks.push(heading(2, 'Diagram'));
  const text = drawingText(drawing(area.elements, area.title, gap, base));
  blocks.push(text === null ? paragraph(TOO_MANY_ARROWS) : diagram(text));

  blocks.push(heading(2, 'Elements'));
  blocks.push(...orSay(area.elements.length === 0 ? [] : [table(ELEMENT_HEADER,
    area.elements.map((id) => [idCell(id, ctx), ...elementCells(ctx.elements.get(id))]))], 'The area has no elements.'));

  blocks.push(heading(2, 'Dependencies'));
  const rows = dependencyRows(area, ctx);
  blocks.push(...orSay(rows.length === 0 ? [] : [table(['Element', 'Relation', 'Other end', 'Kind and titles', 'Its areas'], rows)],
    'No dependencies.'));

  blocks.push(heading(2, 'Decisions'));
  blocks.push(...orSay(records.decisions.flatMap((record) => decisionBlocks(record, ctx)), 'No decisions bind an element of this area.'));
  blocks.push(heading(2, 'Contracts'));
  blocks.push(...orSay(records.contracts.flatMap((record) => contractBlocks(record, ctx)), 'No contracts.'));
  blocks.push(heading(2, 'Open questions'));
  blocks.push(...orSay(records.holes.flatMap((record) => holeBlocks(record, ctx)), 'No open questions.'));

  blocks.push(heading(2, 'Known gap'));
  blocks.push(...orSay(records.gap.length === 0 ? [] : [table(['From', 'To', 'Reason', 'Close by'], records.gap.map((entry) => [
    elementLinks([entry.from], ctx), elementLinks([entry.to], ctx), [entry.reason], [entry.close_by ?? '']]))],
  'No known-gap entries.'));

  blocks.push(heading(2, 'Capabilities'));
  const capabilities = areaCapabilities(data, area);
  blocks.push(...orSay(capabilities.length === 0 ? [] : [table(['Capability', 'Description'], capabilities.map((capability) => [
    capabilityLinks([capability.name], ctx), [capability.description ?? '']]))], 'No capabilities pass through this area.'));
  return doc(area.title, blocks);
}
