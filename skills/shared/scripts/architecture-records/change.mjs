// The change object of one run (spec 2026-11-21, "`change`"): what the run added, changed and removed, from the
// `export` of the before model and of the current model. Pure: reads and writes nothing.
import { cmp } from '../architecture-delta/report.mjs';

// A text of a value with object keys sorted, so key order never counts when two values are compared.
export function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return `{${Object.keys(value).sort(cmp).map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export const EMPTY_EXPORT = { elements: [], allowed: [], runtime: [], decisions: [], holes: [], contracts: [] };

// Added, changed and removed ids between two maps of id -> canonical text, each sorted in UTF-16 order.
function diff(before, after) {
  const sorted = (ids) => ids.sort(cmp);
  return {
    added: sorted([...after.keys()].filter((id) => !before.has(id))),
    changed: sorted([...after.keys()].filter((id) => before.has(id) && before.get(id) !== after.get(id))),
    removed: sorted([...before.keys()].filter((id) => !after.has(id))),
  };
}

// Each element's export object together with the `allowed` and `runtime` entries it is an end of.
function elementTexts(exported) {
  const links = new Map(exported.elements.map((element) => [element.id, []]));
  const add = (list, entry) => {
    for (const end of new Set([entry.from, entry.to])) links.get(end)?.push(canonical({ list, entry }));
  };
  for (const entry of exported.allowed) add('allowed', entry);
  for (const entry of exported.runtime) add('runtime', entry);
  return new Map(exported.elements.map((element) => [element.id,
    canonical({ element, links: links.get(element.id).sort(cmp) })]));
}

// Records by id, compared without `group`: a record moved to another file is not changed.
function recordTexts(records) {
  return new Map(records.map(({ group, ...record }) => [record.id, canonical(record)]));
}

function gapDiff(before, after) {
  const pairs = (entries) => new Map(entries.map((entry) => [`${entry.from}\u0000${entry.to}`, [entry.from, entry.to]]));
  const b = pairs(before);
  const a = pairs(after);
  const sorted = (list) => list.sort((x, y) => cmp(x[0], y[0]) || cmp(x[1], y[1]));
  return {
    added: sorted([...a].filter(([key]) => !b.has(key)).map(([, pair]) => pair)),
    removed: sorted([...b].filter(([key]) => !a.has(key)).map(([, pair]) => pair)),
  };
}

const lastLine = (output) => output.split('\n').filter((line) => line !== '').at(-1) ?? '';

// `before` and `after` are `export` objects; the gaps are known-gap entries; `check` is the delta check run's
// { output, exitCode }; `flags` holds name, date, run, askedBy, summary and rejected. Keys in the records table order.
export function buildChange({ before, after, beforeGap, afterGap, check, flags }) {
  return {
    id: `${flags.date}-${flags.name}`,
    date: flags.date,
    run: flags.run,
    asked_by: flags.askedBy,
    summary: flags.summary,
    rejected: [...flags.rejected],
    elements: diff(elementTexts(before), elementTexts(after)),
    decisions: diff(recordTexts(before.decisions), recordTexts(after.decisions)),
    holes: diff(recordTexts(before.holes), recordTexts(after.holes)),
    contracts: diff(recordTexts(before.contracts), recordTexts(after.contracts)),
    gap: gapDiff(beforeGap, afterGap),
    check: { exit: check.exitCode, summary: lastLine(check.output), output: check.output },
    approved: null,
  };
}
