// HTML writer. Every value is HTML-escaped; each page's Content-Security-Policy allows only the pinned Mermaid script
// and the one start-up script, by hash, plus inline styles.
import crypto from 'node:crypto';
import { MARKER } from './out.mjs';
import { SAFE_HREF } from './tree.mjs';

export const MERMAID_URL = 'https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js';
export const MERMAID_INTEGRITY = 'sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp';
export const STARTUP = "mermaid.initialize({ startOnLoad: true, securityLevel: 'strict' });";
const STARTUP_HASH = `sha256-${crypto.createHash('sha256').update(STARTUP, 'utf8').digest('base64')}`;
export const CSP = `default-src 'none'; script-src ${MERMAID_URL} '${STARTUP_HASH}'; style-src 'unsafe-inline'; img-src data:`;
const STYLE = 'body{font-family:system-ui,sans-serif;max-width:60rem;margin:0 auto;padding:1rem;line-height:1.5}'
  + 'table{border-collapse:collapse}th,td{border:1px solid #999;padding:.25rem .5rem;text-align:left;vertical-align:top}'
  + 'pre{overflow-x:auto}';

export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// A link to a Markdown document becomes a link to its page: README.md is index.html, any other x.md is x.html.
export function pageHref(href) {
  if (typeof href !== 'string' || !SAFE_HREF.test(href) || !href.endsWith('.md')) throw new Error(`unsafe link target ${href}`);
  const base = href.slice(0, -'.md'.length);
  if (base === 'README' || base.endsWith('/README')) return `${base.slice(0, -'README'.length)}index.html`;
  return `${base}.html`;
}

function inline(parts, oneLine = false) {
  return parts.map((part) => {
    if (typeof part === 'string') {
      const text = oneLine ? part.replace(/\n/g, ' ') : part;
      return text.split('\n').map(escapeHtml).join('<br>\n');
    }
    return `<a href="${escapeHtml(pageHref(part.href))}">${escapeHtml(String(part.text).replace(/\n/g, ' '))}</a>`;
  }).join('');
}

function block(node) {
  switch (node.type) {
    case 'heading':
      return `<h${node.level}>${inline([node.text], true)}</h${node.level}>`;
    case 'paragraph':
      return `<p>${inline(node.parts)}</p>`;
    case 'list':
      return `<ul>\n${node.items.map((item) => `<li>${inline(item)}</li>`).join('\n')}\n</ul>`;
    case 'table': {
      const head = node.header.map((text) => `<th>${inline([text], true)}</th>`).join('');
      const rows = node.rows.map((cells) => `<tr>${cells.map((cell) => `<td>${inline(cell, true)}</td>`).join('')}</tr>`);
      return `<table>\n<thead><tr>${head}</tr></thead>\n<tbody>\n${rows.join('\n')}\n</tbody>\n</table>`;
    }
    case 'code':
      return `<pre><code>${escapeHtml(String(node.text).replace(/\n+$/, ''))}</code></pre>`;
    case 'diagram':
      return `<pre class="mermaid">${escapeHtml(node.text)}</pre>`;
    default:
      throw new Error(`unknown block ${node.type}`);
  }
}

// Spec, write rule 2 and Writers: the marker line first; the policy, the pinned script and the start-up script.
export function renderHtml(doc) {
  const title = escapeHtml(String(doc.title).replace(/\n/g, ' '));
  return [
    MARKER,
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    `<meta http-equiv="Content-Security-Policy" content="${CSP}">`,
    `<title>${title}</title>`,
    `<style>${STYLE}</style>`,
    '</head>',
    '<body>',
    `<h1>${title}</h1>`,
    ...doc.blocks.map(block),
    `<script src="${MERMAID_URL}" integrity="${MERMAID_INTEGRITY}" crossorigin="anonymous"></script>`,
    `<script>${STARTUP}</script>`,
    '</body>',
    '</html>',
    '',
  ].join('\n');
}
