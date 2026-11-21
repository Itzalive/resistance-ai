// The AI pack (spec, AI pack): the area and capability slices and the index file, in pack text. `base` is a
// `packContext` of the export; each slice adds the ids it holds in full.
import { cmp } from '../architecture-delta/report.mjs';
import { areaCapabilities, areaRecords, capabilityRecords, outsideAreas } from './facts.mjs';
import { packFile, multiLine, oneLine } from './pack-text.mjs';
import {
  PACK_INDEX, packArea, packCapability, packContext, withHeld, elementBlock, decisionBlock, contractBlock, holeBlock,
  gapLine, stepLine, ref,
} from './pack-blocks.mjs';

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
    ...section('Capabilities', lineBlock(areaCapabilities(data, area)
      .map((capability) => `- ${ref('capabilities', capability.name, ctx, `: ${oneLine(capability.title)}`)}`))),
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

const LAYOUT = 'This pack holds the architecture model in slices for agents. areas/<name>.md holds one area: its elements, '
  + 'decisions, contracts, open questions and known-gap entries, and the capabilities that pass through it. '
  + 'capabilities/<name>.md holds one capability: its steps, '
  + 'the elements they touch, and the decisions and contracts that name it. This file holds the index and the facts '
  + 'outside any area. A pack file in brackets after an id names the file that holds that id in full. model.json holds '
  + 'the whole export.';

const INDEX_KINDS = [
  ['elements', 'Elements'], ['decisions', 'Decisions'], ['contracts', 'Contracts'], ['holes', 'Open questions'], ['capabilities', 'Capabilities'],
];

// Spec, AI pack, Index: every pack file that holds each id in full.
function holders(data, gap, outside) {
  const held = Object.fromEntries(INDEX_KINDS.map(([kind]) => [kind, new Map()]));
  const add = (kind, ids, file) => {
    for (const id of ids) {
      if (!held[kind].has(id)) held[kind].set(id, new Set());
      held[kind].get(id).add(file);
    }
  };
  for (const area of data.areas) {
    const records = areaRecords(data, gap, area);
    add('elements', area.elements, packArea(area.name));
    add('decisions', idsOf(records.decisions), packArea(area.name));
    add('contracts', idsOf(records.contracts), packArea(area.name));
    add('holes', idsOf(records.holes), packArea(area.name));
  }
  for (const capability of data.capabilities) {
    const records = capabilityRecords(data, capability);
    add('elements', records.elements, packCapability(capability.name));
    add('decisions', idsOf(records.decisions), packCapability(capability.name));
    add('contracts', idsOf(records.contracts), packCapability(capability.name));
    add('capabilities', [capability.name], packCapability(capability.name));
  }
  add('elements', idsOf(outside.elements), PACK_INDEX);
  add('decisions', [...idsOf(outside.principles), ...idsOf(outside.decisions)], PACK_INDEX);
  add('contracts', idsOf(outside.contracts), PACK_INDEX);
  add('holes', idsOf(outside.holes), PACK_INDEX);
  return held;
}

function indexSection(data, gap, outside) {
  const held = holders(data, gap, outside);
  const ids = {
    elements: idsOf(data.elements), decisions: idsOf(data.decisions), contracts: idsOf(data.contracts),
    holes: idsOf(data.holes), capabilities: data.capabilities.map((capability) => capability.name),
  };
  const parts = INDEX_KINDS.flatMap(([kind, title]) => {
    const lines = [...ids[kind]].sort(cmp).map((id) => `${id}: ${[...(held[kind].get(id) ?? [])].sort(cmp).join(', ')}`);
    return lines.length === 0 ? [] : [`### ${title}`, lines.join('\n')];
  });
  return parts.length === 0 ? [] : ['## Index', ...parts];
}

// Spec, Pack layout: pack/README.md.
export function packIndex(data, gap, base) {
  const outside = outsideAreas(data, base.byElement);
  const ctx = withHeld(base, {
    elements: idsOf(outside.elements),
    decisions: [...idsOf(outside.principles), ...idsOf(outside.decisions)],
    contracts: idsOf(outside.contracts),
    holes: idsOf(outside.holes),
  });
  return packFile('Architecture pack', [
    LAYOUT,
    ...indexSection(data, gap, outside),
    ...section('Principles', outside.principles.map((record) => decisionBlock(record.id, ctx))),
    ...section('Elements in no area', outside.elements.map((element) => elementBlock(element.id, ctx))),
    ...section('Decisions in no area', outside.decisions.map((record) => decisionBlock(record.id, ctx))),
    ...section('Contracts in no area', outside.contracts.map((record) => contractBlock(record.id, ctx))),
    ...section('Open questions in no area', outside.holes.map((record) => holeBlock(record.id, ctx))),
  ]);
}

// The pack files of one build (pack/model.json is written by build.mjs), as { path with '/': text }; `tick` runs
// after each file (the --timeout deadline).
export function buildPack(data, gap, tick = () => {}) {
  const base = packContext(data);
  const files = {};
  files['pack/README.md'] = packIndex(data, gap, base);
  tick();
  for (const area of data.areas) {
    files[`pack/${packArea(area.name)}`] = areaSlice(data, gap, area, base);
    tick();
  }
  for (const capability of data.capabilities) {
    files[`pack/${packCapability(capability.name)}`] = capabilitySlice(data, capability, base);
    tick();
  }
  return files;
}
