// The overview document: the system diagram, areas, capabilities, principles, contracts, changes, model health, and
// everything in no area.
import { cmp } from '../architecture-delta/report.mjs';
import { doc, heading, paragraph, list, table, diagram, docLink } from './tree.mjs';
import { ARROW_LIMIT, flowchart } from './mermaid.mjs';
import {
  OVERVIEW, IMPROVEMENTS, changeDoc, topLevel, areasByElement, areasOf, outsideAreas, recordTarget, titlesOf,
} from './facts.mjs';
import { decisionBlocks, contractBlocks, holeBlocks, elementLinks, areaLinks, capabilityLinks } from './records-doc.mjs';

export const OVERVIEW_TITLE = 'Architecture';

// Spec, Overview: relationships lifted to the top-level elements; one arrow per pair, solid when any lifted
// relationship is an import, otherwise dashed and labelled with the sorted kinds.
function systemDiagram(data) {
  const nodes = data.elements.filter((element) => !element.id.includes('.')).map((element) => ({ id: element.id, text: element.title }));
  if (nodes.length === 0) return paragraph('The model has no elements.');
  const pairs = new Map();
  const lift = (relationship, kind) => {
    const from = topLevel(relationship.from);
    const to = topLevel(relationship.to);
    if (from === to) return;
    const key = JSON.stringify([from, to]);
    if (!pairs.has(key)) pairs.set(key, { from, to, solid: false, kinds: new Set() });
    const pair = pairs.get(key);
    if (kind === null) pair.solid = true;
    else pair.kinds.add(kind);
  };
  for (const relationship of data.allowed) lift(relationship, null);
  for (const relationship of data.runtime) lift(relationship, relationship.kind);
  const arrows = [...pairs.values()]
    .sort((x, y) => cmp(x.from, y.from) || cmp(x.to, y.to))
    .map((pair) => ({ from: pair.from, to: pair.to, dashed: !pair.solid, text: pair.solid ? '' : [...pair.kinds].sort(cmp).join(', ') }));
  const text = flowchart(nodes, arrows);
  return text === null ? paragraph(`The system diagram has more than ${ARROW_LIMIT} arrows and is not drawn; the tables list every element.`)
    : diagram(text, { kind: 'flowchart', nodes, arrows, frame: null });
}

const orNone = (parts) => (parts.length > 0 ? parts : ['None']);

export function buildOverview(data, gap) {
  const byElement = areasByElement(data);
  const ctx = { doc: OVERVIEW, byElement, titles: titlesOf(data), decisions: new Map(data.decisions.map((d) => [d.id, d])), area: null };
  const outside = outsideAreas(data, byElement);
  const blocks = [heading(2, 'System'), systemDiagram(data)];

  blocks.push(heading(2, 'Areas'));
  blocks.push(data.areas.length === 0 ? paragraph('The model has no area views.')
    : table(['Area', 'Description', 'Elements'], data.areas.map((area) => [
      areaLinks([area.name], ctx), [area.description ?? ''], [String(area.elements.length)]])));

  blocks.push(heading(2, 'Capabilities'));
  blocks.push(data.capabilities.length === 0 ? paragraph('The model has no capability views.')
    : table(['Capability', 'Description', 'Areas'], data.capabilities.map((capability) => [
      capabilityLinks([capability.name], ctx), [capability.description ?? ''],
      orNone(areaLinks(areasOf(capability.steps.flatMap((step) => [step.from, step.to]), byElement), ctx))])));

  blocks.push(heading(2, 'Principles'));
  const principles = outside.principles;
  if (principles.length === 0) blocks.push(paragraph('No principles.'));
  for (const principle of principles) blocks.push(...decisionBlocks(principle, ctx));

  blocks.push(heading(2, 'Contracts'));
  blocks.push(data.contracts.length === 0 ? paragraph('No contracts.')
    : table(['Contract', 'Owner', 'Bound', 'Compatibility'], data.contracts.map((contract) => [
      [docLink(`${contract.id}: ${contract.name}`, recordTarget('contracts', contract, byElement))],
      elementLinks([contract.owner], ctx), elementLinks(contract.bound, ctx), [contract.compatibility ?? 'No rule stated']])));

  blocks.push(heading(2, 'Changes'));
  const changes = [...data.changes].sort((x, y) => cmp(y.date, x.date) || cmp(x.id, y.id));
  blocks.push(changes.length === 0 ? paragraph('No change records.') : list(changes.map((change) => [
    docLink(change.id, changeDoc(change.id)),
    ` (${change.date}): ${change.summary} `,
    change.approved === null ? '(not yet approved)' : `(approved by ${change.approved.by} on ${change.approved.date})`,
  ])));

  blocks.push(heading(2, 'Model health'));
  const see = [', see ', docLink('the improvement list', IMPROVEMENTS)];
  blocks.push(list([
    [`Known-gap entries: ${gap.length}`, ...see],
    [`Open questions: ${data.holes.length}`, ...see],
    [`Coverage: ${data.coverage === null ? 'No coverage file' : data.coverage.answer}`, ...see],
    [`Unmapped modules: ${data.coverage === null ? 0 : data.coverage.unmapped.length}`, ...see],
  ]));

  // Spec, Overview: the elements in no area, then every record (other than a principle) that has no area.
  blocks.push(heading(2, 'Not in any area'));
  const { elements: loose, decisions, contracts, holes } = outside;
  if (loose.length > 0) {
    blocks.push(table(['Element', 'Title', 'Description'], loose.map((element) => [[element.id], [element.title], [element.description ?? '']])));
  }
  for (const record of decisions) blocks.push(...decisionBlocks(record, ctx));
  for (const record of contracts) blocks.push(...contractBlocks(record, ctx));
  for (const record of holes) blocks.push(...holeBlocks(record, ctx));
  if (loose.length + decisions.length + contracts.length + holes.length === 0) {
    blocks.push(paragraph('Every element and record is in an area.'));
  }
  return doc(OVERVIEW_TITLE, blocks);
}
