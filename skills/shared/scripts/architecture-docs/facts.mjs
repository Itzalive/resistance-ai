// Facts the documents share, from the format 4 export: which areas hold each element and record, where each id is
// written in full, and relative links between documents (paths from the output folder, with '/').
import path from 'node:path';
import { cmp } from '../architecture-delta/report.mjs';

export const OVERVIEW = 'README.md';
export const IMPROVEMENTS = 'improvements.md';
export const areaDoc = (name) => `areas/${name}.md`;
export const capabilityDoc = (name) => `capabilities/${name}.md`;
export const changeDoc = (id) => `changes/${id}.md`;

// Spec, Terms: element ids are dotted paths; a top-level element has no dot.
export const topLevel = (id) => id.split('.')[0];

// Spec, Areas: an element's areas are the area views it is an element of, sorted by name.
export function areasByElement(data) {
  const byElement = new Map(data.elements.map((element) => [element.id, []]));
  for (const area of data.areas) for (const id of area.elements) byElement.get(id)?.push(area.name);
  for (const names of byElement.values()) names.sort(cmp);
  return byElement;
}

const has = (record, key) => Object.hasOwn(record, key);
export const isCrossCutting = (decision) => has(decision, 'obligations');
export const isPrinciple = (decision) => isCrossCutting(decision) && decision.binds.length === 0 && !has(decision, 'owner');

// Spec, Shared rules: a record's areas are the areas of the elements it binds (a contract's owner and bound elements).
export function recordElements(kind, record) {
  return kind === 'contracts' ? [record.owner, ...record.bound] : record.binds;
}

export function areasOf(ids, byElement) {
  return [...new Set(ids.flatMap((id) => byElement.get(id) ?? []))].sort(cmp);
}

// Where an id is written in full: its first area's document, or the overview.
export function elementTarget(id, byElement) {
  const areas = byElement.get(id) ?? [];
  return areas.length > 0 ? areaDoc(areas[0]) : OVERVIEW;
}

// A principle binds no element, so it has no area and is written in the overview.
export function recordTarget(kind, record, byElement) {
  const areas = areasOf(recordElements(kind, record), byElement);
  return areas.length > 0 ? areaDoc(areas[0]) : OVERVIEW;
}

// Spec, Shared rules: ids are shown as written, titles beside them.
export function titlesOf(data) {
  return {
    elements: new Map(data.elements.map((element) => [element.id, element.title])),
    areas: new Map(data.areas.map((area) => [area.name, area.title])),
    capabilities: new Map(data.capabilities.map((capability) => [capability.name, capability.title])),
  };
}

export function relative(from, to) {
  if (to.startsWith('/') || path.posix.normalize(to).startsWith('..')) throw new Error(`link target ${to} leaves the output folder`);
  return path.posix.relative(path.posix.dirname(from), to);
}

// Spec, Area: an area's records: the decisions binding an area element (cross-cutting first, then by id), the
// contracts whose owner or bound elements are in the area, the open questions binding area elements, and the
// known-gap entries with an end in the area, sorted by pair.
export function areaRecords(data, gap, area) {
  const inArea = new Set(area.elements);
  const touches = (ids) => ids.some((id) => inArea.has(id));
  const decisions = data.decisions.filter((decision) => touches(decision.binds))
    .sort((x, y) => Number(isCrossCutting(y)) - Number(isCrossCutting(x)) || cmp(x.id, y.id));
  return {
    decisions,
    contracts: data.contracts.filter((contract) => touches(recordElements('contracts', contract))),
    holes: data.holes.filter((hole) => touches(hole.binds)),
    gap: gap.filter((entry) => inArea.has(entry.from) || inArea.has(entry.to))
      .sort((x, y) => cmp(x.from, y.from) || cmp(x.to, y.to)),
  };
}

// Spec, Capability and AI pack: the elements a capability's steps touch (sorted), and the decisions and contracts
// whose `capabilities` name it.
export function capabilityRecords(data, capability) {
  const names = (record) => (record.capabilities ?? []).includes(capability.name);
  return {
    elements: [...new Set(capability.steps.flatMap((step) => [step.from, step.to]))].sort(cmp),
    decisions: data.decisions.filter(names),
    contracts: data.contracts.filter(names),
  };
}

// Spec, Overview and AI pack: the facts outside any area: the elements in no area, the principles, and the decisions
// (other than principles), contracts and open questions that have no area.
export function outsideAreas(data, byElement) {
  const noArea = (kind, record) => areasOf(recordElements(kind, record), byElement).length === 0;
  return {
    elements: data.elements.filter((element) => byElement.get(element.id).length === 0),
    principles: data.decisions.filter(isPrinciple),
    decisions: data.decisions.filter((decision) => !isPrinciple(decision) && noArea('decisions', decision)),
    contracts: data.contracts.filter((contract) => noArea('contracts', contract)),
    holes: data.holes.filter((hole) => noArea('holes', hole)),
  };
}

// Each element's allowed, runtime and binding-decision entries, grouped once so a document does not rescan the export:
// `from` and `to` (allowed entries from and to it), `out` and `in` (runtime links from and to it), `boundBy` (decisions
// whose `binds` hold it, in export order).
export function linkIndex(data) {
  const empty = () => ({ from: [], to: [], out: [], in: [], boundBy: [] });
  const index = new Map(data.elements.map((element) => [element.id, empty()]));
  const at = (id) => index.get(id) ?? empty();
  for (const entry of data.allowed) { at(entry.from).from.push(entry); at(entry.to).to.push(entry); }
  for (const link of data.runtime) { at(link.from).out.push(link); at(link.to).in.push(link); }
  for (const decision of data.decisions) for (const id of new Set(decision.binds)) at(id).boundBy.push(decision);
  return index;
}

// Spec, Area and AI pack: the capabilities with a step whose end is an area element, in name order.
export function areaCapabilities(data, area) {
  const inArea = new Set(area.elements);
  return data.capabilities.filter((capability) => capability.steps.some((step) => inArea.has(step.from) || inArea.has(step.to)))
    .sort((x, y) => cmp(x.name, y.name));
}

// What every area, capability and change document reads, built once per build: `byElement` (areasByElement), `links`
// (linkIndex), `titles` (titlesOf), `elements`, `decisions`, `contracts` and `holes` (Maps by id).
export function documentBase(data) {
  return {
    byElement: areasByElement(data),
    links: linkIndex(data),
    titles: titlesOf(data),
    elements: new Map(data.elements.map((element) => [element.id, element])),
    decisions: new Map(data.decisions.map((decision) => [decision.id, decision])),
    contracts: new Map(data.contracts.map((contract) => [contract.id, contract])),
    holes: new Map(data.holes.map((hole) => [hole.id, hole])),
  };
}
