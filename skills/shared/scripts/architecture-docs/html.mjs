// HTML writer. Every value is HTML-escaped; diagrams are inline SVG drawn at build time (svg.mjs). A page carries no
// script, its Content-Security-Policy allows none, and its style reads in a light and a dark theme.
import { MARKER } from './out.mjs';
import { SAFE_HREF } from './tree.mjs';

export const CSP = "default-src 'none'; style-src 'unsafe-inline'";
// Colour tokens for each theme, then rules that use only the tokens. Diagram parts are coloured by class (svg.mjs), so
// the SVG's own currentColor and red stay as the fallback where this style does not reach.
const LIGHT = '--bg:#f6f7f9;--surface:#fff;--text:#1f2328;--muted:#5b6672;--border:#d9dee5;--accent:#0b63c4;'
  + '--accent-soft:#e8f1fc;--node:#eef1f5;--frame:#f4f8fd;--edge:#77818c;--gap:#c62828;--stripe:#f8f9fb;--code:#f1f3f6';
const DARK = '--bg:#0e1116;--surface:#161a21;--text:#e4e7eb;--muted:#9ba5b2;--border:#2a313c;--accent:#6aaeff;'
  + '--accent-soft:#18263a;--node:#1e242e;--frame:#131b27;--edge:#8a94a1;--gap:#ff6b6b;--stripe:#1a1f27;--code:#1c212a';
const STYLE = [
  `:root{color-scheme:light dark;${LIGHT}}`,
  `@media (prefers-color-scheme:dark){:root{${DARK}}}`,
  '*{box-sizing:border-box}',
  'body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}',
  'main{max-width:66rem;margin:0 auto;padding:1.5rem 1rem 4rem}',
  'header.top{background:var(--surface);border-bottom:1px solid var(--border);padding:.6rem 1rem;font-size:.9rem}',
  'header.top a::before{content:"\\2190  "}',
  'h1{font-size:1.85rem;line-height:1.2;letter-spacing:-.01em;margin:.25rem 0 1.25rem;overflow-wrap:anywhere}',
  'h2{font-size:1.3rem;margin:2.5rem 0 .9rem;padding-bottom:.4rem;border-bottom:2px solid var(--border)}',
  'h3{font-size:1.08rem;margin:1.75rem 0 .6rem}h4{font-size:1rem;margin:1.25rem 0 .5rem}',
  'a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}',
  'p,li,dd{overflow-wrap:anywhere}ul{padding-left:1.25rem}li{margin:.2rem 0}',
  '.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:.9rem 1.1rem;margin:.8rem 0;'
    + 'box-shadow:0 1px 2px rgba(0,0,0,.04)}',
  '.card>h3,.card>h4{margin:0 0 .4rem;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.95rem;color:var(--accent)}',
  '.card>p:last-child,.card>dl:last-child,.card>ul:last-child{margin-bottom:0}',
  'dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:.3rem 1rem;margin:.6rem 0;font-size:.93rem}',
  'dl.facts dt{color:var(--muted);font-weight:500}dl.facts dd{margin:0}',
  '@media (max-width:40rem){dl.facts{grid-template-columns:1fr;gap:0}dl.facts dd{margin-bottom:.5rem}}',
  '.table{overflow-x:auto}',
  '.table{background:var(--surface);border:1px solid var(--border);border-radius:12px;margin:.9rem 0}',
  'table{border-collapse:collapse;width:100%;font-size:.92rem}',
  'th,td{padding:.5rem .75rem;text-align:left;vertical-align:top;border-bottom:1px solid var(--border)}',
  'th{background:var(--accent-soft);font-weight:600;white-space:nowrap}tbody tr:nth-child(even){background:var(--stripe)}',
  'tbody tr:last-child td{border-bottom:0}.card .table{border-radius:8px;margin:.6rem 0 0}',
  'pre{background:var(--code);border:1px solid var(--border);border-radius:10px;padding:.8rem 1rem;overflow-x:auto;font-size:.85rem}',
  '.diagram{overflow:auto;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1rem;margin:1rem 0}',
  '.diagram svg{display:block;margin:0 auto;max-width:none;height:auto}',
  // Arial has Helvetica's widths, which Graphviz used to size each box.
  '.diagram text{fill:var(--text);font-family:Arial,Helvetica,sans-serif}',
  '.diagram .node path,.diagram .node polygon,.diagram .participant rect{fill:var(--node);stroke:var(--edge)}',
  '.diagram .node.framed path,.diagram .node.framed polygon{fill:var(--accent-soft);stroke:var(--accent)}',
  '.diagram .cluster path,.diagram .cluster polygon{fill:var(--frame);stroke:var(--border)}',
  '.diagram .edge path,.diagram .lifeline,.diagram .call line,.diagram .reply line,.diagram .loop{stroke:var(--edge)}',
  '.diagram .edge polygon,.diagram .call polygon,.diagram .reply polygon{fill:var(--edge);stroke:var(--edge)}',
  '.diagram .edge.gap path{stroke:var(--gap)}.diagram .edge.gap polygon{fill:var(--gap);stroke:var(--gap)}',
  '.diagram .edge.gap text{fill:var(--gap)}',
].join('');

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

// A list item that reads `Label: value` (a short capitalised label before the first colon of its first text part), as
// { label, rest }, or null. A list whose every item is one is drawn as a grid of facts.
const FACT = /^([A-Z][A-Za-z0-9 ,'()-]{0,40}): ([\s\S]*)$/;
function fact(item) {
  const match = typeof item[0] === 'string' ? FACT.exec(item[0]) : null;
  if (match === null) return null;
  return { label: match[1], rest: [match[2], ...item.slice(1)].filter((part) => part !== '') };
}

// A heading with no deeper heading before the next heading of its level or higher, at level 3 or below, is a record:
// it and its blocks up to the next heading are one card.
function withCards(blocks) {
  const out = [];
  let open = false;
  blocks.forEach((node, at) => {
    if (node.type === 'heading') {
      if (open) out.push('</section>');
      const next = blocks.slice(at + 1).find((other) => other.type === 'heading');
      open = node.level >= 3 && (next === undefined || next.level <= node.level);
      if (open) out.push('<section class="card">');
    }
    out.push(block(node));
  });
  if (open) out.push('</section>');
  return out;
}

function block(node) {
  switch (node.type) {
    case 'heading':
      return `<h${node.level}>${inline([node.text], true)}</h${node.level}>`;
    case 'paragraph':
      return `<p>${inline(node.parts)}</p>`;
    case 'list': {
      const facts = node.items.map(fact);
      if (facts.length > 0 && facts.every((item) => item !== null)) {
        return `<dl class="facts">\n${facts.map(({ label, rest }) => `<dt>${escapeHtml(label)}</dt><dd>${inline(rest)}</dd>`).join('\n')}\n</dl>`;
      }
      return `<ul>\n${node.items.map((item) => `<li>${inline(item)}</li>`).join('\n')}\n</ul>`;
    }
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
// `options.home`: the relative link to the overview page, shown in a top bar; null on the overview itself.
export function renderHtml(doc, options = {}) {
  const title = escapeHtml(String(doc.title).replace(/\n/g, ' '));
  const home = typeof options.home === 'string' ? [`<header class="top"><a href="${escapeHtml(options.home)}">Architecture overview</a></header>`] : [];
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
    ...home,
    '<main>',
    `<h1>${title}</h1>`,
    ...withCards(doc.blocks),
    '</main>',
    '</body>',
    '</html>',
    '',
  ].join('\n');
}
