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
  const rel = path.posix.relative(path.posix.dirname(from), to);
  return rel === '' ? path.posix.basename(to) : rel;
}
