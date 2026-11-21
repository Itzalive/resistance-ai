// A capability document (spec, What each document holds, Capability): title and description, the sequence diagram,
// the steps, the decisions and contracts that name the capability, and the areas involved.
import { doc, heading, paragraph, list, table, diagram, orSay } from './tree.mjs';
import { STEP_LIMIT, sequence } from './mermaid.mjs';
import { areasOf, capabilityDoc, capabilityRecords } from './facts.mjs';
import { decisionBlocks, contractBlocks, elementLinks, areaLinks } from './records-doc.mjs';

export const TOO_MANY_STEPS = `The capability has more than ${STEP_LIMIT} steps, so its sequence diagram is not drawn; the steps table lists every step.`;

// Spec, Capability: participants in order of first appearance, labelled with their titles.
function sequenceText(capability, ctx) {
  const seen = new Set(capability.steps.flatMap((step) => [step.from, step.to]));
  const participants = [...seen].map((id) => ({ id, text: ctx.titles.elements.get(id) ?? id }));
  return sequence(participants, capability.steps.map((step) => ({ from: step.from, to: step.to, reply: step.reply, text: step.label ?? '' })));
}

export function buildCapability(data, capability, base) {
  const ctx = { ...base, doc: capabilityDoc(capability.name), area: null };
  const records = capabilityRecords(data, capability);
  const blocks = [];
  if (capability.description !== null) blocks.push(paragraph(capability.description));

  blocks.push(heading(2, 'Sequence'));
  if (capability.steps.length === 0) blocks.push(paragraph('The capability has no steps.'));
  else {
    const text = sequenceText(capability, ctx);
    blocks.push(text === null ? paragraph(TOO_MANY_STEPS) : diagram(text));
  }

  blocks.push(heading(2, 'Steps'));
  blocks.push(...orSay(capability.steps.length === 0 ? [] : [table(['Step', 'From', 'To', 'Label', 'Call or reply', 'Kinds'],
    capability.steps.map((step, at) => [[String(at + 1)], elementLinks([step.from], ctx), elementLinks([step.to], ctx),
      [step.label ?? ''], [step.reply ? 'reply' : 'call'], [step.kinds.join(', ')]]))], 'No steps.'));

  blocks.push(heading(2, 'Decisions'));
  blocks.push(...orSay(records.decisions.flatMap((record) => decisionBlocks(record, ctx)), 'No decisions name this capability.'));
  blocks.push(heading(2, 'Contracts'));
  blocks.push(...orSay(records.contracts.flatMap((record) => contractBlocks(record, ctx)), 'No contracts name this capability.'));

  // Spec, Capability: the areas of every step's ends, and "Not in any area" for an end in none.
  blocks.push(heading(2, 'Areas involved'));
  const names = areasOf(records.elements, ctx.byElement);
  const items = names.map((name) => areaLinks([name], ctx));
  if (records.elements.some((id) => (ctx.byElement.get(id) ?? []).length === 0)) items.push(['Not in any area']);
  blocks.push(items.length === 0 ? paragraph('No areas.') : list(items));
  return doc(capability.title, blocks);
}
