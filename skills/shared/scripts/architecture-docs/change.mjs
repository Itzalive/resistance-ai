// A change record (spec, What each document holds, Change record): the change's summary, asker, run, date and
// approval; a diagram of the elements it added or changed; what changed; the choices not taken; its known-gap pairs;
// its check. A change file holds only ids, so a record is printed as it stands in the model now.
import { doc, heading, paragraph, list, table, code, diagram, docLink } from './tree.mjs';
import { changeDoc, elementTarget, recordTarget, relative } from './facts.mjs';
import { decisionBlocks, contractBlocks, holeBlocks, elementLinks } from './records-doc.mjs';
import { drawing, drawingText, TOO_MANY_ARROWS } from './area-diagram.mjs';

export const GONE = ' (not in the current model)';
const PARTS = ['added', 'changed', 'removed'];
const ELEMENT_HEADER = ['Element', 'Title', 'Description', 'Code', 'Rules', 'Tags'];
// The record kinds of a change file after its elements, in document order: the change file's key, the heading word,
// the Map of current records in `base`, and how a current record is printed in full.
const KINDS = [
  { key: 'decisions', word: 'Decisions', records: 'decisions', blocks: decisionBlocks },
  { key: 'contracts', word: 'Contracts', records: 'contracts', blocks: contractBlocks },
  { key: 'holes', word: 'Open questions', records: 'holes', blocks: holeBlocks },
];

const orSay = (blocks, text) => (blocks.length > 0 ? blocks : [paragraph(text)]);
const goneText = (id) => `${id}${GONE}`;

function elementRow(id, ctx) {
  const element = ctx.elements.get(id);
  return [[docLink(id, relative(ctx.doc, elementTarget(id, ctx.byElement)))], [element.title], [element.description ?? ''],
    [element.code.join(', ')], [element.rules.join(', ')], [element.tags.map((tag) => `#${tag}`).join(' ')]];
}

// Spec, What changed: each list as the change file gives it. Added and changed elements still in the model in a table,
// then the gone ones as plain text; removed ids as plain text.
function elementBlocks(change, ctx) {
  const blocks = [];
  for (const part of PARTS) {
    const ids = change.elements[part];
    if (ids.length === 0) continue;
    blocks.push(heading(3, `Elements ${part}`));
    if (part === 'removed') {
      blocks.push(list(ids.map((id) => [id])));
      continue;
    }
    const current = ids.filter((id) => ctx.elements.has(id));
    const gone = ids.filter((id) => !ctx.elements.has(id));
    if (current.length > 0) blocks.push(table(ELEMENT_HEADER, current.map((id) => elementRow(id, ctx))));
    if (gone.length > 0) blocks.push(list(gone.map((id) => [goneText(id)])));
  }
  return blocks;
}

// Spec, What changed: added and changed records still in the model in full, in the change file's order; a gone id as
// plain text; removed ids as plain text.
function recordBlocks(change, kind, ctx) {
  const blocks = [];
  for (const part of PARTS) {
    const ids = change[kind.key][part];
    if (ids.length === 0) continue;
    blocks.push(heading(3, `${kind.word} ${part}`));
    if (part === 'removed') {
      blocks.push(list(ids.map((id) => [id])));
      continue;
    }
    for (const id of ids) {
      const record = ctx[kind.records].get(id);
      blocks.push(...(record === undefined ? [paragraph(goneText(id))] : kind.blocks(record, ctx, 4)));
    }
  }
  return blocks;
}

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

// Spec, Change record (amended): the added and changed elements still in the model, framed and marked; an id in both
// lists is marked `added`.
function diagramBlock(change, gap, ctx) {
  const marks = new Map();
  for (const id of change.elements.changed) if (ctx.elements.has(id)) marks.set(id, 'changed');
  for (const id of change.elements.added) if (ctx.elements.has(id)) marks.set(id, 'added');
  if (marks.size === 0) return paragraph('No element the change added or changed is in the current model.');
  const text = drawingText(drawing([...marks.keys()], change.id, gap, ctx, marks));
  return text === null ? paragraph(TOO_MANY_ARROWS) : diagram(text);
}

export function buildChange(data, gap, change, base) {
  const ctx = { ...base, doc: changeDoc(change.id), area: null };
  const approval = change.approved === null ? 'Not yet approved' : `approved by ${change.approved.by} on ${change.approved.date}`;
  const blocks = [list([
    ['Summary: ', change.summary], ['Asked by: ', change.asked_by], ['Run: ', change.run], ['Date: ', change.date],
    ['Approval: ', approval],
  ])];

  blocks.push(heading(2, 'Diagram'), diagramBlock(change, gap, ctx));

  blocks.push(heading(2, 'What changed'));
  blocks.push(...orSay([...elementBlocks(change, ctx), ...KINDS.flatMap((kind) => recordBlocks(change, kind, ctx))],
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
