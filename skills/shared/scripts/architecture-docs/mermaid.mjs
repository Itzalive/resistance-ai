// Mermaid diagram text. Node ids are generated (n1, n2, ... in the order given); every label is entity-encoded, so model
// text cannot close a quote, end a statement or open a directive. Mermaid decodes `#<code>;` before it parses.
import { cmp } from '../architecture-delta/report.mjs';

export const ARROW_LIMIT = 80;
export const STEP_LIMIT = 200;
const SAFE = /^[A-Za-z0-9 .'/_-]$/;
const RED = 'stroke:#d00,color:#d00';

export function label(text) {
  return Array.from(String(text).replace(/\n/g, ' '))
    .map((ch) => (SAFE.test(ch) ? ch : `#${ch.codePointAt(0)};`))
    .join('');
}

// A left-to-right flowchart. `nodes`: { id, text }; `arrows`: { from, to, dashed, red, text } by node id, drawn solid or
// dashed, red ones in red, with the text as a label when it is not empty; `frame`: null, or { text, ids }, the nodes
// drawn inside one frame. Returns null when there are more than ARROW_LIMIT arrows.
export function flowchart(nodes, arrows, frame = null) {
  if (arrows.length > ARROW_LIMIT) return null;
  const ids = new Map(nodes.map((node, index) => [node.id, `n${index + 1}`]));
  const nodeLine = (node, indent) => `${indent}${ids.get(node.id)}["${label(node.text)}"]`;
  const lines = ['flowchart LR'];
  if (frame === null) {
    lines.push(...nodes.map((node) => nodeLine(node, '  ')));
  } else {
    const framed = new Set(frame.ids);
    for (const id of framed) if (!ids.has(id)) throw new Error(`framed element ${id} is not a node`);
    lines.push(`  subgraph frame["${label(frame.text)}"]`);
    lines.push(...nodes.filter((node) => framed.has(node.id)).map((node) => nodeLine(node, '    ')));
    lines.push('  end');
    lines.push(...nodes.filter((node) => !framed.has(node.id)).map((node) => nodeLine(node, '  ')));
  }
  const red = [];
  arrows.forEach((arrow, at) => {
    const from = ids.get(arrow.from);
    const to = ids.get(arrow.to);
    if (from === undefined || to === undefined) throw new Error(`arrow ${arrow.from} -> ${arrow.to} has an end that is not a node`);
    const text = arrow.text ? `|"${label(arrow.text)}"|` : '';
    lines.push(`  ${from} ${arrow.dashed ? '-.->' : '-->'}${text} ${to}`);
    if (arrow.red) red.push(at);
  });
  if (red.length > 0) lines.push(`  linkStyle ${red.join(',')} ${RED}`);
  return lines.join('\n');
}

// A sequence diagram. `participants`: { id, text }, drawn in the order given, with ids generated in element-id order;
// `messages`: { from, to, reply, text } by participant id, calls solid and replies dashed. Returns null when there are
// more than STEP_LIMIT messages.
export function sequence(participants, messages) {
  if (messages.length > STEP_LIMIT) return null;
  const ids = new Map(participants.map((participant) => participant.id).sort(cmp).map((id, index) => [id, `n${index + 1}`]));
  const lines = ['sequenceDiagram', ...participants.map((participant) => `  participant ${ids.get(participant.id)} as ${label(participant.text)}`)];
  for (const message of messages) {
    const from = ids.get(message.from);
    const to = ids.get(message.to);
    if (from === undefined || to === undefined) throw new Error(`message ${message.from} -> ${message.to} has an end that is not a participant`);
    lines.push(`  ${from}${message.reply ? '-->>' : '->>'}${to}: ${label(message.text)}`);
  }
  return lines.join('\n');
}
