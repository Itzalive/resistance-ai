// A change record (spec, What each document holds, Change record): the change's summary, asker, run, date and
// approval; a diagram of the elements it added or changed (when the change file lists relationships, only what it
// changed, as one diagram or, above CHANGE_SPLIT_ARROWS arrows, a model diagram and a known-gap diagram); what changed;
// the choices not taken; its known-gap pairs;
// its check. A change file holds only ids, so a record is printed as it stands in the model now.
import { cmp } from '../architecture-delta/report.mjs';
import { doc, heading, paragraph, list, table, code, docLink, orSay } from './tree.mjs';
import { changeDoc, elementTarget, recordTarget, relative } from './facts.mjs';
import { ELEMENT_HEADER, decisionBlocks, contractBlocks, holeBlocks, elementCells, elementLinks } from './records-doc.mjs';
import { drawing, drawingBlock, TOO_MANY_ARROWS } from './area-diagram.mjs';

const GONE = ' (not in the current model)';
const PARTS = ['added', 'changed', 'removed'];
// The record kinds of a change file after its elements, in document order: the change file's key, the heading word,
// the Map of current records in `base`, and how a current record is printed in full.
const KINDS = [
  { key: 'decisions', word: 'Decisions', records: 'decisions', blocks: decisionBlocks },
  { key: 'contracts', word: 'Contracts', records: 'contracts', blocks: contractBlocks },
  { key: 'holes', word: 'Open questions', records: 'holes', blocks: holeBlocks },
];

const goneText = (id) => `${id}${GONE}`;

const elementRow = (id, ctx) => [[docLink(id, relative(ctx.doc, elementTarget(id, ctx.byElement)))], ...elementCells(ctx.elements.get(id))];

// Spec, What changed: each list as the change file gives it, under `<word> <part>`. Added and changed ids still in the
// model are printed in full by `inFull` (in the file's order), then the gone ones as plain text with their note;
// removed ids are plain text.
function changedBlocks(word, lists, current, inFull) {
  const blocks = [];
  for (const part of PARTS) {
    const ids = lists[part];
    if (ids.length === 0) continue;
    blocks.push(heading(3, `${word} ${part}`));
    if (part === 'removed') {
      blocks.push(list(ids.map((id) => [id])));
      continue;
    }
    const present = ids.filter((id) => current.has(id));
    const gone = ids.filter((id) => !current.has(id));
    if (present.length > 0) blocks.push(...inFull(present));
    if (gone.length > 0) blocks.push(list(gone.map((id) => [goneText(id)])));
  }
  return blocks;
}

// The elements as one table; each record as its blocks.
const elementBlocks = (change, ctx) => changedBlocks('Elements', change.elements, ctx.elements,
  (ids) => [table(ELEMENT_HEADER, ids.map((id) => elementRow(id, ctx)))]);
const recordBlocks = (change, kind, ctx) => changedBlocks(kind.word, change[kind.key], ctx[kind.records],
  (ids) => ids.flatMap((id) => kind.blocks(ctx[kind.records].get(id), ctx, 4)));

// Spec, Choices not taken: the change's `rejected` list, then the `rejected` options of each decision it added or
// changed that is still in the model, each decision once, added ones first.
function choiceItems(change, ctx) {
  const items = change.rejected.map((option) => [option]);
  for (const id of new Set([...change.decisions.added, ...change.decisions.changed])) {
    const decision = ctx.decisions.get(id);
    if (decision === undefined) continue;
    const link = docLink(id, relative(ctx.doc, recordTarget('decisions', decision, ctx.byElement)));
    for (const option of decision.rejected) items.push([link, ': ', option]);
  }
  return items;
}

// Spec, Known gap (amended): an end links to its document when it is a model element, and is otherwise plain text.
function gapItems(change, ctx) {
  const end = (id) => (ctx.elements.has(id) ? elementLinks([id], ctx) : [goneText(id)]);
  const pair = (label, [from, to]) => [label, ...end(from), ' -> ', ...end(to)];
  return [...change.gap.added.map((entry) => pair('Added: ', entry)), ...change.gap.removed.map((entry) => pair('Removed: ', entry))];
}

const kindText = (rel) => rel.kind ?? 'import';

// Spec, What changed (#43): each relationship as `<from> -> <to>: <kind or import>`, its ends linked like gap ends.
function relationshipBlocks(change, ctx) {
  if (change.relationships === undefined) return [];
  const end = (id) => (ctx.elements.has(id) ? elementLinks([id], ctx) : [goneText(id)]);
  return PARTS.filter((part) => change.relationships[part].length > 0).flatMap((part) => [
    heading(3, `Relationships ${part}`),
    list(change.relationships[part].map((rel) => [...end(rel.from), ' -> ', ...end(rel.to), `: ${kindText(rel)}`])),
  ]);
}

// Spec, Change record (#43): a diagram's nodes are its framed elements and the ends of its arrows, an end gone from the
// model labelled as gone.
function picture(arrows, ctx, marks, frame) {
  const title = (id) => ctx.titles.elements.get(id) ?? id;
  const nodeText = (id) => {
    if (marks.has(id)) return `${title(id)} (${marks.get(id)})`;
    if (!ctx.elements.has(id)) return goneText(id);
    const areas = ctx.byElement.get(id) ?? [];
    return `${title(id)} (${areas.length > 0 ? areas[0] : 'no area'})`;
  };
  const sorted = arrows.sort((x, y) => cmp(x.from, y.from) || cmp(x.to, y.to) || x.order - y.order)
    .map(({ order, ...rest }) => rest);
  const ids = new Set([...marks.keys(), ...sorted.flatMap((a) => [a.from, a.to])]);
  return { nodes: [...ids].sort(cmp).map((id) => ({ id, text: nodeText(id) })), arrows: sorted, frame };
}

const arrow = (from, to, order, dashed, red, text) => ({ from, to, order, dashed, red, text });

// Spec, Change record (#43): at most this many arrows in all, the change is one diagram; above it, two.
export const CHANGE_SPLIT_ARROWS = 15;

// Model changes: added and changed relationships in their style, removed ones dashed `removed`, except a removed import
// whose pair is an added gap pair (that pair is drawn once, as its gap arrow).
function modelArrows(change) {
  const key = (from, to) => JSON.stringify([from, to]);
  const gapAdded = new Set(change.gap.added.map(([from, to]) => key(from, to)));
  const runtimeText = (rel) => [rel.kind, ...[...rel.titles].sort(cmp).map((title) => `"${title}"`)].join(', ');
  return [
    ...[...change.relationships.added, ...change.relationships.changed].map((rel) => (rel.kind === null
      ? arrow(rel.from, rel.to, 0, false, false, '')
      : arrow(rel.from, rel.to, 1, true, false, runtimeText(rel)))),
    ...change.relationships.removed
      .filter((rel) => !(rel.kind === null && gapAdded.has(key(rel.from, rel.to))))
      .map((rel) => arrow(rel.from, rel.to, 3, true, false, rel.kind === null ? 'removed' : `removed, ${rel.kind}`)),
  ];
}

// Known-gap changes: added gap pairs red (labelled `known gap` when drawn among the model arrows), removed ones dashed
// `gap closed`.
function gapArrows(change, label) {
  return [
    ...change.gap.added.map(([from, to]) => arrow(from, to, 2, false, true, label)),
    ...change.gap.removed.map(([from, to]) => arrow(from, to, 4, true, false, 'gap closed')),
  ];
}

// A drawing's title over it; never a record card (html.mjs).
const drawingHeading = (text) => ({ ...heading(3, text), drawing: true });

// Spec, Change record (amended): the added and changed elements still in the model, framed and marked; an id in both
// lists is marked `added`. A change file that lists relationships draws only the change: one diagram up to
// CHANGE_SPLIT_ARROWS arrows, else a model diagram and a known-gap diagram, each only when it has something (#43).
function diagramBlocks(change, gap, ctx) {
  const marks = new Map();
  for (const id of change.elements.changed) if (ctx.elements.has(id)) marks.set(id, 'changed');
  for (const id of change.elements.added) if (ctx.elements.has(id)) marks.set(id, 'added');
  if (change.relationships !== undefined) {
    const frame = marks.size === 0 ? null : { text: change.id, ids: [...marks.keys()].sort(cmp) };
    const model = modelArrows(change);
    const empty = [paragraph('No element the change added or changed is in the current model, and it changed no relationship or gap pair.')];
    if (model.length + gapArrows(change, '').length <= CHANGE_SPLIT_ARROWS) {
      const whole = picture([...model, ...gapArrows(change, 'known gap')], ctx, marks, frame);
      return whole.nodes.length === 0 ? empty : [drawingBlock(whole) ?? paragraph(TOO_MANY_ARROWS)];
    }
    const parts = [['Model changes', picture(model, ctx, marks, frame)], ['Known-gap changes', picture(gapArrows(change, ''), ctx, new Map(), null)]]
      .filter(([, drawn]) => drawn.nodes.length > 0);
    return parts.flatMap(([word, drawn]) => [drawingHeading(word), drawingBlock(drawn) ?? paragraph(TOO_MANY_ARROWS)]);
  }
  if (marks.size === 0) return [paragraph('No element the change added or changed is in the current model.')];
  return [drawingBlock(drawing([...marks.keys()], change.id, gap, ctx, marks)) ?? paragraph(TOO_MANY_ARROWS)];
}

export function buildChange(data, gap, change, base) {
  const ctx = { ...base, doc: changeDoc(change.id), area: null };
  const approval = change.approved === null ? 'Not yet approved' : `Approved by ${change.approved.by} on ${change.approved.date}`;
  const blocks = [list([
    ['Summary: ', change.summary], ['Asked by: ', change.asked_by], ['Run: ', change.run], ['Date: ', change.date],
    ['Approval: ', approval],
  ])];

  blocks.push(heading(2, 'Diagram'), ...diagramBlocks(change, gap, ctx));

  blocks.push(heading(2, 'What changed'));
  blocks.push(...orSay([...elementBlocks(change, ctx), ...relationshipBlocks(change, ctx),
    ...KINDS.flatMap((kind) => recordBlocks(change, kind, ctx))],
    'The change file lists no elements or records.'));

  blocks.push(heading(2, 'Choices not taken'));
  const choices = choiceItems(change, ctx);
  blocks.push(choices.length === 0 ? paragraph('No choices are recorded as not taken.') : list(choices));

  blocks.push(heading(2, 'Known gap'));
  const pairs = gapItems(change, ctx);
  blocks.push(pairs.length === 0 ? paragraph('The change added or removed no known-gap entries.') : list(pairs));

  blocks.push(heading(2, 'Check'));
  blocks.push(list([['Exit: ', String(change.check.exit)], ['Summary: ', change.check.summary]]), code(change.check.output));
  return doc(change.id, blocks);
}
