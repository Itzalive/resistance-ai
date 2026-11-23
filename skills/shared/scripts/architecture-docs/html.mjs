// HTML writer. Every value is HTML-escaped; diagrams are inline SVG drawn at build time (svg.mjs). A page carries no
// script, its Content-Security-Policy allows none, and its style reads in a light and a dark theme.
import { MARKER } from './out.mjs';
import { SAFE_HREF } from './tree.mjs';

export const CSP = "default-src 'none'; style-src 'unsafe-inline'";
const STYLE = ':root{color-scheme:light dark}'
  + 'body{font-family:system-ui,sans-serif;max-width:60rem;margin:0 auto;padding:1rem;line-height:1.5;color:#1a1a1a;background:#fff}'
  + 'a{color:#0645ad}'
  + '.table{overflow-x:auto}table{border-collapse:collapse}th,td{border:1px solid #999;padding:.25rem .5rem;text-align:left;vertical-align:top}'
  + 'pre{overflow-x:auto}.diagram{overflow-x:auto;margin:1rem 0}.diagram svg{max-width:none;height:auto}'
  + '@media (prefers-color-scheme:dark){'
  + 'body{color:#e6e6e6;background:#16181c}a{color:#8ab4f8}th,td{border-color:#555}'
  + '.diagram [stroke="#d00000"]{stroke:#ff6b6b}.diagram [fill="#d00000"]{fill:#ff6b6b}}';

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
      // The wrapper scrolls a wide table on a narrow screen and leaves the table's semantics alone.
      return `<div class="table"><table>\n<thead><tr>${head}</tr></thead>\n<tbody>\n${rows.join('\n')}\n</tbody>\n</table></div>`;
    }
    case 'code':
      return `<pre><code>${escapeHtml(String(node.text).replace(/\n+$/, ''))}</code></pre>`;
    case 'diagram':
      // The SVG comes from svg.mjs (drawFigures), which escapes all model text and keeps only drawing.
      if (typeof node.svg !== 'string') throw new Error('a diagram has no drawing');
      return `<div class="diagram">${node.svg}</div>`;
    default:
      throw new Error(`unknown block ${node.type}`);
  }
}

// Spec, write rule 2 and Writers: the marker line first, then the policy; no script.
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
    '</body>',
    '</html>',
    '',
  ].join('\n');
}
