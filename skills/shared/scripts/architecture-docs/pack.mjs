// The AI pack (spec, AI pack): the area and capability slices and the index file, in pack text. `base` is a
// `packContext` of the export; each slice adds the ids it holds in full.
import { areaRecords, capabilityRecords } from './facts.mjs';
import { packFile, multiLine } from './pack-text.mjs';
import { withHeld, elementBlock, decisionBlock, contractBlock, holeBlock, gapLine, stepLine } from './pack-blocks.mjs';

const idsOf = (records) => records.map((record) => record.id);
// Spec, Pack layout: a section with no content is left out.
const section = (title, blocks) => (blocks.length === 0 ? [] : [`## ${title}`, ...blocks]);
const lineBlock = (lines) => (lines.length === 0 ? [] : [lines.join('\n')]);
const intro = (view) => (view.description === null ? [] : [multiLine(view.description)]);

export function areaSlice(data, gap, area, base) {
  const records = areaRecords(data, gap, area);
  const ctx = withHeld(base, {
    elements: area.elements, decisions: idsOf(records.decisions), contracts: idsOf(records.contracts), holes: idsOf(records.holes),
  });
  return packFile(`${area.name}: ${area.title}`, [
    ...intro(area),
    ...section('Elements', area.elements.map((id) => elementBlock(id, ctx))),
    ...section('Decisions', records.decisions.map((record) => decisionBlock(record.id, ctx))),
    ...section('Contracts', records.contracts.map((record) => contractBlock(record.id, ctx))),
    ...section('Open questions', records.holes.map((record) => holeBlock(record.id, ctx))),
    ...section('Known gap', lineBlock(records.gap.map((entry) => gapLine(entry, ctx)))),
  ]);
}

export function capabilitySlice(data, capability, base) {
  const records = capabilityRecords(data, capability);
  const ctx = withHeld(base, {
    elements: records.elements, decisions: idsOf(records.decisions), contracts: idsOf(records.contracts), capabilities: [capability.name],
  });
  return packFile(`${capability.name}: ${capability.title}`, [
    ...intro(capability),
    ...section('Steps', lineBlock(capability.steps.map((step, at) => stepLine(step, at + 1, ctx)))),
    ...section('Elements', records.elements.map((id) => elementBlock(id, ctx))),
    ...section('Decisions', records.decisions.map((record) => decisionBlock(record.id, ctx))),
    ...section('Contracts', records.contracts.map((record) => contractBlock(record.id, ctx))),
  ]);
}
