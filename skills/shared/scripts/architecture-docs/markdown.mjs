// Markdown writer. Model text outside code blocks is escaped so it cannot open a link, an HTML tag, a code span,
// a heading or a table break; a code block's fence is longer than any run of backticks in it.
import { MARKER } from './out.mjs';
import { SAFE_HREF } from './tree.mjs';

const PUNCTUATION = /[\\`*_{}[\]()#+\-.!|=~$]/g;
const FENCE = '`'.repeat(3);

export function escapeText(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(PUNCTUATION, (ch) => `\\${ch}`);
}

function target(href) {
  if (typeof href !== 'string' || !SAFE_HREF.test(href) || !href.endsWith('.md')) throw new Error(`unsafe link target ${href}`);
  return href;
}

// A block's leading spaces and tabs are written as entities, so they cannot open an indented code block.
const leadingSpaces = (line) => line.replace(/^[ \t]+/, (lead) => lead.replace(/ /g, '&#32;').replace(/\t/g, '&#9;'));

// Line feeds in text become hard breaks (a backslash at the end of the line), or spaces where the block is one line.
function inline(parts, { indent = '', oneLine = false } = {}) {
  return parts.map((part, index) => {
    if (typeof part === 'string') {
      if (oneLine) return escapeText(part.replace(/\n/g, ' '));
      return part.split('\n').map(escapeText)
        .map((line, at) => (index === 0 && at === 0 ? leadingSpaces(line) : line))
        .join(`\\\n${indent}`);
    }
    return `[${escapeText(String(part.text).replace(/\n/g, ' '))}](${target(part.href)})`;
  }).join('');
}

function fence(text) {
  const longest = (text.match(/`+/g) ?? []).reduce((max, run) => Math.max(max, run.length), 0);
  return '`'.repeat(Math.max(3, longest + 1));
}

function block(node) {
  switch (node.type) {
    case 'heading':
      return `${'#'.repeat(node.level)} ${inline([node.text], { oneLine: true })}`;
    case 'paragraph':
      return inline(node.parts);
    case 'list':
      return node.items.map((item) => `- ${inline(item, { indent: '  ' })}`).join('\n');
    case 'table': {
      const row = (cells) => `| ${cells.map((cell) => inline(cell, { oneLine: true })).join(' | ')} |`;
      return [row(node.header.map((text) => [text])), `|${' --- |'.repeat(node.header.length)}`, ...node.rows.map(row)].join('\n');
    }
    case 'code': {
      const text = String(node.text).replace(/\n+$/, '');
      const mark = fence(text);
      return `${mark}\n${text}\n${mark}`;
    }
    case 'diagram':
      return `${FENCE}mermaid\n${node.text}\n${FENCE}`;
    default:
      throw new Error(`unknown block ${node.type}`);
  }
}

// Spec, write rule 2: every Markdown file starts with the marker line.
export function renderMarkdown(doc) {
  return `${[MARKER, `# ${inline([doc.title], { oneLine: true })}`, ...doc.blocks.map(block)].join('\n\n')}\n`;
}
