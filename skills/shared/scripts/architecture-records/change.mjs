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

// Each element's export object; its relationships are listed on their own (#43).
function elementTexts(exported) {
  return new Map(exported.elements.map((element) => [element.id, canonical(element)]));
}

// Spec, `change`, Relationships: each `allowed` entry (kind null) and `runtime` entry, matched by from, to and kind;
// changed when the titles differ, given as they are now.
function relationshipDiff(before, after) {
  const key = (rel) => `${rel.from}\u0000${rel.to}\u0000${rel.kind ?? ''}\u0000${rel.kind === null ? 0 : 1}`;
  const rels = (exported) => new Map([
    ...exported.allowed.map((entry) => ({ from: entry.from, to: entry.to, kind: null, titles: [...entry.titles] })),
    ...exported.runtime.map((entry) => ({ from: entry.from, to: entry.to, kind: entry.kind, titles: [...entry.titles] })),
  ].map((rel) => [key(rel), rel]));
  const b = rels(before);
  const a = rels(after);
  const order = (x, y) => cmp(x.from, y.from) || cmp(x.to, y.to)
    || (x.kind === null ? (y.kind === null ? 0 : -1) : (y.kind === null ? 1 : cmp(x.kind, y.kind)));
  return {
    added: [...a].filter(([k]) => !b.has(k)).map(([, rel]) => rel).sort(order),
    changed: [...a].filter(([k, rel]) => b.has(k) && canonical(b.get(k).titles) !== canonical(rel.titles))
      .map(([, rel]) => rel).sort(order),
    removed: [...b].filter(([k]) => !a.has(k)).map(([, rel]) => rel).sort(order),
  };
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
    relationships: relationshipDiff(before, after),
    gap: gapDiff(beforeGap, afterGap),
    check: { exit: check.exitCode, summary: lastLine(check.output), output: check.output },
    approved: null,
  };
}
