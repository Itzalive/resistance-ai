// SVG diagrams drawn at build time (spec, Writers, Diagrams (SVG, in HTML)). Flowcharts are laid out by Graphviz
// (WebAssembly, in this process); sequence diagrams are drawn here. Lines and text use currentColor, so a diagram takes
// the page's text colour in a light or a dark theme; known-gap arrows are red.
import { locateGraphviz, importGraphviz } from './graphviz.mjs';
import { escapeHtml } from './html.mjs';

export const RED = '#d00000';
const FONT = 'Helvetica,Arial,sans-serif';
const JOINER = '⁠';

// Text as one drawable line: a line feed is a space, and a lone surrogate or a non-character (which would make
// Graphviz drop the whole label) is U+FFFD.
export function drawable(text) {
  return Array.from(String(text).replace(/\n/g, ' '), (ch) => {
    const code = ch.codePointAt(0);
    const bad = (code >= 0xd800 && code <= 0xdfff) || (code >= 0xfdd0 && code <= 0xfdef) || (code & 0xfffe) === 0xfffe;
    return bad ? '�' : ch;
  }).join('');
}

// A label as Graphviz reads it: an HTML-like label (`<...>`) with the text XML-escaped. Graphviz still expands escape
// sequences such as \N (the node name) in it, so a word joiner follows every backslash; the SVG drops every joiner.
export function dotLabel(text) {
  return `<${escapeHtml(drawable(text)).replace(/\\/g, `\\${JOINER}`)}>`;
}

function flowchartDot(nodes, arrows, frame) {
  const ids = new Map(nodes.map((node, index) => [node.id, `n${index + 1}`]));
  const nodeLine = (node, indent) => `${indent}${ids.get(node.id)} [label=${dotLabel(node.text)}];`;
  const lines = [
    'digraph diagram {',
    `  rankdir=LR; fontname="${FONT}"; fontsize=12;`,
    `  node [shape=box fontname="${FONT}" fontsize=12];`,
    `  edge [fontname="${FONT}" fontsize=11];`,
  ];
  const framed = new Set(frame === null ? [] : frame.ids);
  for (const id of framed) if (!ids.has(id)) throw new Error(`framed element ${id} is not a node`);
  if (frame !== null) {
    lines.push(`  subgraph cluster_frame { label=${dotLabel(frame.text)};`);
    lines.push(...nodes.filter((node) => framed.has(node.id)).map((node) => nodeLine(node, '    ')));
    lines.push('  }');
  }
  lines.push(...nodes.filter((node) => !framed.has(node.id)).map((node) => nodeLine(node, '  ')));
  for (const arrow of arrows) {
    const from = ids.get(arrow.from);
    const to = ids.get(arrow.to);
    if (from === undefined || to === undefined) throw new Error(`arrow ${arrow.from} -> ${arrow.to} has an end that is not a node`);
    const attrs = [];
    if (arrow.dashed) attrs.push('style=dashed');
    if (arrow.red) attrs.push(`color="${RED}" fontcolor="${RED}"`);
    if (arrow.text) attrs.push(`label=${dotLabel(arrow.text)}`);
    lines.push(`  ${from} -> ${to}${attrs.length > 0 ? ` [${attrs.join(' ')}]` : ''};`);
  }
  lines.push('}');
  return lines.join('\n');
}

// Graphviz's SVG with only the drawing kept: from <svg> on, no joiners, comments, titles or background, and black as
// currentColor.
function drawingOnly(text) {
  const svg = text.replace(/\r/g, '').replaceAll(JOINER, '');
  return svg.slice(svg.indexOf('<svg'))
    .replace(/<!--[\s\S]*?-->\n?/g, '')
    .replace(/<title>[\s\S]*?<\/title>\n?/g, '')
    .replace(/<polygon fill="[^"]*" stroke="none"[^>]*\/>\n?/, '')
    .replace(/(stroke|fill)="black"/g, '$1="currentColor"')
    .replace(/<text (?![^>]*\sfill=)/g, '<text fill="currentColor" ')
    .trimEnd();
}

let graphviz = null;

// Loads Graphviz once: the repository's copy at the pinned version, else the plugin's (graphviz.mjs). `repoRoot` null
// looks in the plugin only. The tool calls this before building, so a missing copy is a clean `graphviz-missing`.
export async function loadGraphviz(repoRoot = null) {
  if (graphviz === null) graphviz = await (await importGraphviz(locateGraphviz(repoRoot))).load();
  return graphviz;
}

// A left-to-right flowchart: the same nodes, arrows and frame the Mermaid flowchart takes.
export async function flowchartSvg(nodes, arrows, frame = null) {
  const gv = await loadGraphviz();
  return drawingOnly(gv.dot(flowchartDot(nodes, arrows, frame), 'svg'));
}

// Sequence diagram layout, in pixels. Text width is estimated per character.
const CHAR = 7;
const BOX_H = 28;
const TOP = 10;
const ROW = 36;
const LOOP_ROW = 46;
const LOOP_W = 30;
const textWidth = (text) => Array.from(String(text)).length * CHAR;
const n = (value) => String(Math.round(value));

function textAt(x, y, text, anchor = 'middle') {
  return `<text fill="currentColor" x="${n(x)}" y="${n(y)}" text-anchor="${anchor}" font-family="${FONT}" font-size="12">${escapeHtml(drawable(text))}</text>`;
}

function head(x, y, direction) {
  const back = x - 8 * direction;
  return `<polygon fill="currentColor" stroke="currentColor" points="${n(x)},${n(y)} ${n(back)},${n(y - 4)} ${n(back)},${n(y + 4)}"/>`;
}

// The same participants and messages the Mermaid sequence takes: boxes in columns in the order given, a lifeline
// under each, one row per message, calls solid and replies dashed, a message to itself a loop.
export function sequenceSvg(participants, messages) {
  const column = new Map(participants.map((participant, index) => [participant.id, index]));
  for (const message of messages) {
    if (!column.has(message.from) || !column.has(message.to)) {
      throw new Error(`message ${message.from} -> ${message.to} has an end that is not a participant`);
    }
  }
  const widths = participants.map((participant) => Math.max(60, textWidth(participant.text) + 20));
  const gaps = widths.slice(1).map((width, index) => (widths[index] + width) / 2 + 24);
  let right = widths[widths.length - 1] / 2 + 10;
  for (const message of messages) {
    const from = column.get(message.from);
    const to = column.get(message.to);
    const need = textWidth(message.text) + 24;
    if (from === to) {
      const room = LOOP_W + need;
      if (from < gaps.length) gaps[from] = Math.max(gaps[from], room + widths[from + 1] / 2);
      else right = Math.max(right, room + 10);
      continue;
    }
    const lo = Math.min(from, to);
    const hi = Math.max(from, to);
    const have = gaps.slice(lo, hi).reduce((sum, gap) => sum + gap, 0);
    if (have < need) for (let at = lo; at < hi; at += 1) gaps[at] += (need - have) / (hi - lo);
  }
  const xs = [widths[0] / 2 + 10];
  for (const gap of gaps) xs.push(xs[xs.length - 1] + gap);
  const width = xs[xs.length - 1] + right;

  const rows = [];
  let y = TOP + BOX_H + 18;
  for (const message of messages) {
    const from = xs[column.get(message.from)];
    const to = xs[column.get(message.to)];
    const kind = message.reply ? 'reply' : 'call';
    const dash = message.reply ? ' stroke-dasharray="5,3"' : '';
    if (message.from === message.to) {
      y += 6;
      const bottom = y + 18;
      rows.push(`<g class="${kind}">`
        + `<path class="loop" fill="none" stroke="currentColor"${dash} d="M${n(from)},${n(y)} H${n(from + LOOP_W)} V${n(bottom)} H${n(from + 8)}"/>`
        + head(from, bottom, -1)
        + textAt(from + LOOP_W + 6, y + 13, message.text, 'start')
        + '</g>');
      y += LOOP_ROW - 6;
      continue;
    }
    y += 14;
    const direction = to > from ? 1 : -1;
    rows.push(`<g class="${kind}">`
      + `<line stroke="currentColor"${dash} x1="${n(from)}" y1="${n(y)}" x2="${n(to - 8 * direction)}" y2="${n(y)}"/>`
      + head(to, y, direction)
      + textAt((from + to) / 2, y - 6, message.text)
      + '</g>');
    y += ROW - 14;
  }
  const height = y + 10;

  const boxes = participants.map((participant, index) => '<g class="participant">'
    + `<rect fill="none" stroke="currentColor" x="${n(xs[index] - widths[index] / 2)}" y="${TOP}" width="${n(widths[index])}" height="${BOX_H}"/>`
    + textAt(xs[index], TOP + 18, participant.text)
    + '</g>');
  const lifelines = xs.map((x) => `<line class="lifeline" stroke="currentColor" stroke-opacity="0.5" x1="${n(x)}" y1="${TOP + BOX_H}" x2="${n(x)}" y2="${n(height - 6)}"/>`);
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${n(width)}" height="${n(height)}" viewBox="0 0 ${n(width)} ${n(height)}">`,
    ...boxes, ...lifelines, ...rows,
    '</svg>',
  ].join('\n');
}

// Each diagram block of a document gets the SVG of its figure (`flowchart` or `sequence`).
export async function drawFigures(doc) {
  const blocks = [];
  for (const block of doc.blocks) {
    if (block.type !== 'diagram' || !block.figure) {
      blocks.push(block);
      continue;
    }
    const { figure } = block;
    const drawn = figure.kind === 'flowchart'
      ? await flowchartSvg(figure.nodes, figure.arrows, figure.frame ?? null)
      : sequenceSvg(figure.participants, figure.messages);
    blocks.push({ ...block, svg: drawn });
  }
  return { ...doc, blocks };
}
