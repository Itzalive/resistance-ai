# Architecture Docs: Writers and the Overview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `architecture-docs build` also writes the overview, `README.md` and `index.html`, from one document tree through a Markdown writer, an HTML writer and a Mermaid diagram builder that escape all model text.

**Architecture:** This repository has no architecture model. New modules in `skills/shared/scripts/architecture-docs/`: `tree.mjs` (the document tree), `markdown.mjs` and `html.mjs` (the two writers), `mermaid.mjs` (labels and the flowchart), `facts.mjs` (which areas hold each element and record, where each id is written in full, relative links), `records-doc.mjs` (decisions, contracts and open questions in full) and `overview.mjs`. `build.mjs` adds the overview and takes the known-gap cleaning (`cleanGap`) from the CLI.

**Tech Stack:** Node ESM, pytest.

**Spec:** `docs/superpowers/specs/2026-11-17-architecture-docs-design.md`, "Writers", "What each document holds" (Shared rules, Overview), AC-12 and AC-13 (overview part), AC-18 and AC-20 (overview parts) — decisions applied: none. One spec amendment, made in Task 6: the overview's heading is "Architecture" (the spec said "the system title", which the model does not record). Sequence diagrams, frames and known-gap arrows belong to plan 3 (areas and capabilities); the links to area, capability, change and improvement documents point at files plans 3 and 4 add.

**Open decisions:** none

**Size:** 7 tasks, 2 entry paths (`build`, `check`), 1243 lines (reported, not a target)

**Trust boundary:** changed — see Trust-boundary table. No new file writes (only `writer.mjs` writes; the safety tests cover the new modules and must not be loosened: the tree's link constructor is named `docLink` because `link(` is a forbidden file call). The new output is where model and record text reaches readers, the threat model's injection row. No comment or string in a docs module may hold a forbidden call name followed by an opening bracket: the safety test scans whole files.

### Risk & Confidence Assessment

**Confidence:** 90% — the escaping rules are exact in the spec and each has a direct test; the overview is assembly of export facts.

**Complexity Risk:** Medium — escaping must hold for every path model text takes (headings, paragraphs, list items, table cells, link text, diagram labels).

**Environmental Risk:** Low — no new dependency; `node:crypto` for the start-up script hash.

**Main failure modes:** a model string that reaches a writer unescaped (each block type has a hostile-text test); a link to an unsafe target (writers refuse any target outside `[A-Za-z0-9._/-]`); the plan 2a tool tests that assume one output file (sweep rows).

---

## Caller and test sweep

Searched: `skills/`, `tests/` with `rg -n "buildFiles|readGap|cleanText|wrote 1 files|pack/model.json|missing pack|changed pack|snapshot\(out_of" skills/shared/scripts tests/scripts`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `build` writes three files | `tests/scripts/test_architecture_docs_tool.py:32` | assert | 7 | `"wrote 3 files, removed 0\n"` |
| same | `tests/scripts/test_architecture_docs_tool.py:47` | assert | 7 | `(1, "missing README.md\nmissing index.html\nmissing pack/model.json\n3 missing, 0 changed, 0 extra\n")` |
| same | `tests/scripts/test_architecture_docs_tool.py:54` | assert | 7 | `(1, "changed README.md\nextra areas/old.md\nchanged index.html\nchanged pack/model.json\n0 missing, 3 changed, 1 extra\n")` (the renamed element is in no area, so the overview's "Not in any area" table changes) |
| same | `tests/scripts/test_architecture_docs_tool.py:56` | assert | 7 | `"wrote 3 files, removed 1\n"` |
| same | `tests/scripts/test_architecture_docs_tool.py:57`, `:156` | assert | 7 | `== ["README.md", "index.html", "pack/model.json"]` |
| known-gap cleaning moves to `build.mjs` `cleanGap` | `skills/shared/scripts/architecture-docs.mjs` `readGap` | caller | 6 | `return cleanGap(entries);` in place of the `entries.map(...)`; import `cleanGap` from `./architecture-docs/build.mjs`; drop `clean`, `cleanText` from the errors import if unused after (`clean` is still used by `runCheck`) |
| `buildFiles(model, records, gap, tick)` | `architecture-docs.mjs` `main` | caller | — | none: same signature |

## Trust-boundary table

| Boundary | Rule | Mechanism | Task | Test |
|---|---|---|---|---|
| Model text in Markdown | Writers, Markdown | `escapeText` on the title, headings, paragraphs, list items, table cells and link text; line feeds as hard breaks or spaces | 1 | `test_markdown_escapes_model_text`, `test_markdown_table_cells_are_one_line`, `test_markdown_headings_and_links_are_escaped` |
| Code blocks | Writers, Markdown | fence longer than any backtick run | 1 | `test_markdown_code_fence_is_longer_than_any_backtick_run` |
| Link targets | Writers | `SAFE_HREF` in both writers; `pageHref` maps only `.md` targets | 1, 2 | `test_markdown_refuses_an_unsafe_link_target`, `test_html_refuses_an_unsafe_link_target` |
| Model text in HTML | Writers, HTML | `escapeHtml` on every value, the diagram text included | 2 | `test_html_escapes_every_value` |
| Scripts in pages | Writers, HTML; Threat Model (tampered script) | fixed CSP; the pinned Mermaid script with integrity and `crossorigin`; one start-up script by hash | 2 | `test_html_page_policy_and_scripts` |
| Model text in diagrams | Writers, Diagrams | `label` entity-encodes everything outside the safe set; generated node ids | 3 | `test_mermaid_label_encodes_everything_else` |
| Known-gap text | The tool | `cleanGap` cleans ids and text like `export` | 6 | `test_clean_gap` |
| The overview's producers | Shared rules | every model and record string reaches the page only through the writers | 7 | `test_overview_escapes_hostile_model_text` (element title and description; other producers share the same writers) |
| Hrefs built from names and ids | Areas and capabilities (name rule); records (change file names) | names are `[a-z0-9-]`, change ids are file names; `SAFE_HREF` refuses anything else and the build fails as `internal`, exit 2 | 4, 7 | name and file rules' own tests; `test_markdown_refuses_an_unsafe_link_target` |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | Task 1 items 1–5, Task 2 items 1–5, Task 3 items 1–4; focused tests `uv run pytest -q tests/scripts/test_architecture_docs_writers.py tests/scripts/test_architecture_docs_safety.py` |
| C2 | 7 | 4–7 | Task 4 items 1–3, Task 5 items 1–5, Task 6 item 1, Task 7 items 1–9; full suite `uv run pytest -q` |

---

### Task 1: the document tree and the Markdown writer

**Tier:** strong — the writers are the injection defence of the threat model; complete code is given, but the tier stays at strong for that boundary.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/tree.mjs`, `skills/shared/scripts/architecture-docs/markdown.mjs`
- Test: `tests/scripts/test_architecture_docs_writers.py` (create)

**Callers that move with this task:** none.

**Reviewer looks at:**
- every listed punctuation mark escaped — mutation: drop `|` from the escape set — killed by: `test_markdown_escapes_model_text`; mutation: drop `&` handling — killed by the same test
- line feeds — mutation: keep raw line feeds in a table cell — killed by: `test_markdown_table_cells_are_one_line`; mutation: join paragraph lines without the hard break — killed by: `test_markdown_keeps_line_feeds_as_hard_breaks`
- code fences — mutation: always fence with three backticks — killed by: `test_markdown_code_fence_is_longer_than_any_backtick_run`
- link targets — mutation: drop the safe-target check — killed by: `test_markdown_refuses_an_unsafe_link_target`
- the marker comes first — mutation: put the title before the marker — killed by: `test_markdown_page_starts_with_the_marker`

- Satisfies Spec AC: AC-12 (Markdown part), AC-13 (Markdown marker)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_docs_writers.py`:

```python
"""Writers of the architecture docs tool: Markdown, HTML and Mermaid (spec 2026-11-17-architecture-docs-design.md, "Writers")."""

from __future__ import annotations

import pytest

from arch_delta_support import DOCS_LIB, call, require_node

require_node()

MARKER = "<!-- Generated by architecture-docs from the architecture model. Do not edit. -->"


def render(module: str, fn: str, doc: dict) -> dict:
    return call(module, fn, doc, lib=DOCS_LIB)


def md(blocks: list, title: str = "T") -> str:
    result = render("markdown.mjs", "renderMarkdown", {"title": title, "blocks": blocks})
    assert result["ok"], result
    return result["value"]


def body(blocks: list) -> list:
    """The page's pieces after the marker and the title, without the final line feed."""
    return md(blocks).rstrip("\n").split("\n\n")[2:]


def para(*parts) -> dict:
    return {"type": "paragraph", "parts": list(parts)}


def link(text: str, href: str) -> dict:
    return {"type": "link", "text": text, "href": href}


def test_markdown_page_starts_with_the_marker() -> None:  # AC-13
    assert md([para("x")], title="Overview") == MARKER + "\n\n# Overview\n\nx\n"


def test_markdown_escapes_model_text() -> None:  # AC-12
    text = "[x](javascript:alert(1)) <script> a|b *c* _d_ `e` {f} #g +h -i 1. !j =k ~l \\m &n"
    assert body([para(text)])[0] == (
        r"\[x\]\(javascript:alert\(1\)\) &lt;script&gt; a\|b \*c\* \_d\_ \`e\` \{f\} \#g \+h \-i 1\. \!j \=k \~l \\m &amp;n"
    )


def test_markdown_keeps_line_feeds_as_hard_breaks() -> None:
    assert body([para("one\ntwo")])[0] == "one\\\ntwo"
    item = body([{"type": "list", "items": [["one\ntwo"], ["three"]]}])[0]
    assert item == "- one\\\n  two\n- three"


def test_markdown_table_cells_are_one_line() -> None:
    table = {"type": "table", "header": ["A|B", "C"], "rows": [[["x\ny"], [link("L", "areas/a.md")]]]}
    assert body([table])[0] == "| A\\|B | C |\n| --- | --- |\n| x y | [L](areas/a.md) |"


def test_markdown_headings_and_links_are_escaped() -> None:
    blocks = [{"type": "heading", "level": 2, "text": "A *b*\nc"}, para(link("D-1 [x]", "../README.md"), " after")]
    assert body(blocks) == ["## A \\*b\\* c", "[D\\-1 \\[x\\]](../README.md) after"]


def test_markdown_code_fence_is_longer_than_any_backtick_run() -> None:
    assert body([{"type": "code", "text": "a ``` b\nc <d>\n"}])[0] == "````\na ``` b\nc <d>\n````"
    assert body([{"type": "code", "text": "plain"}])[0] == "```\nplain\n```"


def test_markdown_diagram_is_a_mermaid_fence() -> None:
    assert body([{"type": "diagram", "text": "flowchart LR\n  n1[\"A\"]"}])[0] == "```mermaid\nflowchart LR\n  n1[\"A\"]\n```"


@pytest.mark.parametrize("href", ["javascript:alert(1)", "a b.md", "https://x.example/a.md", "a.md#x"])
def test_markdown_refuses_an_unsafe_link_target(href: str) -> None:
    result = render("markdown.mjs", "renderMarkdown", {"title": "T", "blocks": [para(link("x", href))]})
    assert result["ok"] is False
    assert "unsafe link target" in result["message"]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_writers.py`. Expected: FAIL (module not found).
- [ ] **Step 3: GREEN.** Create `tree.mjs`:

```js
// The document tree the writers turn into Markdown and HTML. Strings are model text; links point at documents.
// Inline parts (in paragraphs, list items and table cells) are strings or links.
export const heading = (level, text) => ({ type: 'heading', level, text });
export const paragraph = (...parts) => ({ type: 'paragraph', parts });
export const list = (items) => ({ type: 'list', items });
export const table = (header, rows) => ({ type: 'table', header, rows });
export const code = (text) => ({ type: 'code', text });
export const diagram = (text) => ({ type: 'diagram', text });
// Named docLink: the safety test forbids any call named like fs.link outside the writer.
export const docLink = (text, href) => ({ type: 'link', text, href });
export const doc = (title, blocks) => ({ title, blocks });

// A link target: a relative path to a document, made only of safe characters.
export const SAFE_HREF = /^[A-Za-z0-9._/-]+$/;
```

Create `markdown.mjs`:

```js
// Markdown writer. Model text outside code blocks is escaped so it cannot open a link, an HTML tag, a code span,
// a heading or a table break; a code block's fence is longer than any run of backticks in it.
import { MARKER } from './out.mjs';
import { SAFE_HREF } from './tree.mjs';

const PUNCTUATION = /[\\`*_{}[\]()#+\-.!|=~]/g;
const FENCE = '`'.repeat(3);

export function escapeText(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(PUNCTUATION, (ch) => `\\${ch}`);
}

function target(href) {
  if (typeof href !== 'string' || !SAFE_HREF.test(href)) throw new Error(`unsafe link target ${href}`);
  return href;
}

// Line feeds in text become hard breaks (a backslash at the end of the line), or spaces where the block is one line.
function inline(parts, { indent = '', oneLine = false } = {}) {
  return parts.map((part) => {
    if (typeof part === 'string') {
      const text = oneLine ? part.replace(/\n/g, ' ') : part;
      return text.split('\n').map(escapeText).join(`\\\n${indent}`);
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
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_writers.py tests/scripts/test_architecture_docs_safety.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/tree.mjs skills/shared/scripts/architecture-docs/markdown.mjs tests/scripts/test_architecture_docs_writers.py && git commit -m "feat(#32): the document tree and the Markdown writer"`

### Task 2: the HTML writer

**Tier:** strong — injection defence (escaping, CSP, scripts); complete code.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/html.mjs`
- Test: `tests/scripts/test_architecture_docs_writers.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- every value escaped — mutation: drop the `"` replacement — killed by: `test_html_escapes_every_value` (the link text holds `"`); mutation: leave the title unescaped — killed by the same test
- the policy and the scripts — mutation: drop `crossorigin="anonymous"` — killed by: `test_html_page_policy_and_scripts`; mutation: hash a different start-up text — killed by the same test (the Python side hashes the script it finds)
- page links — mutation: map `README.md` to `README.html` — killed by: `test_html_links_point_at_pages`
- diagrams — mutation: put the diagram text in the page unescaped — killed by: `test_html_escapes_every_value`
- link targets — mutation: drop the safe-target check — killed by: `test_html_refuses_an_unsafe_link_target`

- Satisfies Spec AC: AC-12 (HTML part), AC-13
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Add `import base64` and `import hashlib` at the top of `tests/scripts/test_architecture_docs_writers.py`, then append:

```python
def page(blocks: list, title: str = "T") -> str:
    result = render("html.mjs", "renderHtml", {"title": title, "blocks": blocks})
    assert result["ok"], result
    return result["value"]


def test_html_page_policy_and_scripts() -> None:  # AC-13
    text = page([para("x")])
    lines = text.split("\n")
    assert lines[0] == MARKER and lines[1] == "<!doctype html>"
    start = '<script>mermaid.initialize({ startOnLoad: true, securityLevel: \'strict\' });</script>'
    assert start in lines
    script = start[len("<script>"):-len("</script>")]
    digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
    url = "https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js"
    policy = f"default-src 'none'; script-src {url} 'sha256-{digest}'; style-src 'unsafe-inline'; img-src data:"
    assert f'<meta http-equiv="Content-Security-Policy" content="{policy}">' in lines
    assert text.count("<script") == 2
    assert (f'<script src="{url}" integrity="sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp" '
            'crossorigin="anonymous"></script>') in lines


def test_html_escapes_every_value() -> None:  # AC-12
    blocks = [
        {"type": "heading", "level": 2, "text": "<b>h</b>"},
        para("a <script>alert(1)</script> & 'q'\nnext", link('say "hi"', "areas/a.md")),
        {"type": "table", "header": ["<th>"], "rows": [[["<td>\nx"]]]},
        {"type": "code", "text": "<code>\n"},
        {"type": "diagram", "text": "flowchart LR\n  n1[\"<A>\"]"},
    ]
    text = page(blocks, title="<T>")
    assert "<title>&lt;T&gt;</title>" in text and "<h1>&lt;T&gt;</h1>" in text
    assert "<h2>&lt;b&gt;h&lt;/b&gt;</h2>" in text
    assert "<p>a &lt;script&gt;alert(1)&lt;/script&gt; &amp; &#39;q&#39;<br>\nnext" in text
    assert '<a href="areas/a.html">say &quot;hi&quot;</a></p>' in text
    assert "<th>&lt;th&gt;</th>" in text and "<td>&lt;td&gt; x</td>" in text
    assert "<pre><code>&lt;code&gt;</code></pre>" in text
    assert '<pre class="mermaid">flowchart LR\n  n1[&quot;&lt;A&gt;&quot;]</pre>' in text
    assert text.count("<script") == 2


def test_html_links_point_at_pages() -> None:
    text = page([para(link("o", "README.md"), link("p", "../README.md"), link("q", "../areas/b.md"))])
    assert '<a href="index.html">o</a><a href="../index.html">p</a><a href="../areas/b.html">q</a>' in text


@pytest.mark.parametrize("href", ["javascript:alert(1)", "a.html", "a b.md"])
def test_html_refuses_an_unsafe_link_target(href: str) -> None:
    result = render("html.mjs", "renderHtml", {"title": "T", "blocks": [para(link("x", href))]})
    assert result["ok"] is False
    assert "unsafe link target" in result["message"]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_writers.py -k html`. Expected: FAIL (module not found).
- [ ] **Step 3: GREEN.** Create `html.mjs`:

```js
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
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_writers.py tests/scripts/test_architecture_docs_safety.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/html.mjs tests/scripts/test_architecture_docs_writers.py && git commit -m "feat(#32): the HTML writer, with the pinned Mermaid script and a fixed policy"`

### Task 3: Mermaid labels and the flowchart

**Tier:** strong — injection defence for diagram text; complete code.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/mermaid.mjs`
- Test: `tests/scripts/test_architecture_docs_writers.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- the safe set — mutation: allow `;` — killed by: `test_mermaid_label_encodes_everything_else`; mutation: allow `"` — killed by the same test
- characters beyond one UTF-16 unit — mutation: use `charCodeAt` — killed by: `test_mermaid_label_encodes_everything_else` (an astral character gives one entity)
- the arrow limit — mutation: `>=` instead of `>` — killed by: `test_flowchart_arrow_limit` (exactly 80 is drawn)
- arrows to unknown nodes — mutation: skip the check — killed by: `test_flowchart_refuses_an_arrow_to_no_node`

- Satisfies Spec AC: AC-12 (diagram part)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
def mermaid(fn: str, *args) -> dict:
    return call("mermaid.mjs", fn, *args, lib=DOCS_LIB)


def test_mermaid_label_encodes_everything_else() -> None:  # AC-12
    text = "Ab9 .'/_-;\"%%{init}%%" + chr(0xE9) + chr(0x1F600) + "\nx"
    assert mermaid("label", text)["value"] == (
        "Ab9 .'/_-#59;#34;#37;#37;#123;init#125;#37;#37;#233;#128512; x"
    )


def test_flowchart_nodes_and_arrows() -> None:
    nodes = [{"id": "a", "text": "A one"}, {"id": "b", "text": "B;two"}]
    arrows = [{"from": "a", "to": "b", "dashed": False, "text": ""}, {"from": "b", "to": "a", "dashed": True, "text": "http, event"}]
    assert mermaid("flowchart", nodes, arrows)["value"] == (
        'flowchart LR\n  n1["A one"]\n  n2["B#59;two"]\n  n1 --> n2\n  n2 -.->|"http#44; event"| n1'
    )


def test_flowchart_arrow_limit() -> None:
    nodes = [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]
    arrow = {"from": "a", "to": "b", "dashed": False, "text": ""}
    assert mermaid("flowchart", nodes, [arrow] * 80)["value"].count("-->") == 80
    assert mermaid("flowchart", nodes, [arrow] * 81)["value"] is None


def test_flowchart_refuses_an_arrow_to_no_node() -> None:
    result = mermaid("flowchart", [{"id": "a", "text": "A"}], [{"from": "a", "to": "ghost", "dashed": False, "text": ""}])
    assert result["ok"] is False
    assert "a -> ghost" in result["message"]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_writers.py -k "mermaid or flowchart"`. Expected: FAIL (module not found).
- [ ] **Step 3: GREEN.** Create `mermaid.mjs`:

```js
// Mermaid diagram text. Node ids are generated (n1, n2, ... in the order given); every label is entity-encoded, so model
// text cannot close a quote, end a statement or open a directive. Mermaid decodes `#<code>;` before it parses.
export const ARROW_LIMIT = 80;
const SAFE = /^[A-Za-z0-9 .'/_-]$/;

export function label(text) {
  return Array.from(String(text).replace(/\n/g, ' '))
    .map((ch) => (SAFE.test(ch) ? ch : `#${ch.codePointAt(0)};`))
    .join('');
}

// A left-to-right flowchart. `nodes`: { id, text }; `arrows`: { from, to, dashed, text } by node id, drawn solid or
// dashed, with the text as a label when it is not empty. Returns null when there are more than ARROW_LIMIT arrows.
export function flowchart(nodes, arrows) {
  if (arrows.length > ARROW_LIMIT) return null;
  const ids = new Map(nodes.map((node, index) => [node.id, `n${index + 1}`]));
  const lines = ['flowchart LR', ...nodes.map((node) => `  ${ids.get(node.id)}["${label(node.text)}"]`)];
  for (const arrow of arrows) {
    const from = ids.get(arrow.from);
    const to = ids.get(arrow.to);
    if (from === undefined || to === undefined) throw new Error(`arrow ${arrow.from} -> ${arrow.to} has an end that is not a node`);
    const text = arrow.text ? `|"${label(arrow.text)}"|` : '';
    lines.push(`  ${from} ${arrow.dashed ? '-.->' : '-->'}${text} ${to}`);
  }
  return lines.join('\n');
}
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_writers.py tests/scripts/test_architecture_docs_safety.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/mermaid.mjs tests/scripts/test_architecture_docs_writers.py && git commit -m "feat(#32): Mermaid labels and the flowchart"`

### Task 4: the facts the documents share

**Tier:** standard — complete code.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/facts.mjs`
- Test: `tests/scripts/test_architecture_docs_facts.py` (create)

**Callers that move with this task:** none.

**Reviewer looks at:**
- first area by name — mutation: keep areas in view order without the sort — killed by: `test_areas_by_element_are_sorted`
- principles — mutation: drop the `owner` condition — killed by: `test_principles_and_cross_cutting` (a decision with obligations, empty binds and an owner is not a principle)
- where a record is written in full — mutation: use only a contract's `bound`, not its `owner` — killed by: `test_record_targets`
- relative links — mutation: `path.relative` without `dirname` — killed by: `test_relative_links`

- Satisfies Spec AC: AC-18, AC-20 (link rules, overview part)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_docs_facts.py`:

```python
"""Facts shared by the generated documents (spec 2026-11-17-architecture-docs-design.md, "Shared rules")."""

from __future__ import annotations

from arch_delta_support import DOCS_LIB, call, require_node

require_node()

DATA = {
    "elements": [{"id": e, "title": e.upper()} for e in ("a", "a.x", "b", "c")],
    "areas": [{"name": "zeta", "title": "Zeta", "elements": ["a", "a.x"]}, {"name": "alpha", "title": "Alpha", "elements": ["a.x", "b"]}],
    "capabilities": [{"name": "pay", "title": "Pay", "steps": []}],
}


def facts(fn: str, *args) -> object:
    result = call("facts.mjs", fn, *args, lib=DOCS_LIB)
    assert result["ok"], result
    return result["value"]


def run(code: str) -> object:
    from arch_delta_support import lib_url, run_module
    import json
    snippet = f"import * as f from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\nconst data = {json.dumps(DATA)};\n{code}"
    proc = run_module(snippet)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_areas_by_element_are_sorted() -> None:
    assert run("process.stdout.write(JSON.stringify([...f.areasByElement(data)]));") == [
        ["a", ["zeta"]], ["a.x", ["alpha", "zeta"]], ["b", ["alpha"]], ["c", []],
    ]


def test_principles_and_cross_cutting() -> None:
    cases = [
        {"binds": [], "obligations": ["o"]},
        {"binds": [], "obligations": ["o"], "owner": "a"},
        {"binds": ["a"], "obligations": ["o"]},
        {"binds": []},
    ]
    assert [facts("isPrinciple", d) for d in cases] == [True, False, False, False]
    assert [facts("isCrossCutting", d) for d in cases] == [True, True, True, False]


def test_record_targets() -> None:
    code = (
        "const by = f.areasByElement(data);\n"
        "process.stdout.write(JSON.stringify([\n"
        "  f.recordTarget('decisions', { binds: ['a.x'] }, by),\n"
        "  f.recordTarget('decisions', { binds: [], obligations: ['o'] }, by),\n"
        "  f.recordTarget('decisions', { binds: ['c'] }, by),\n"
        "  f.recordTarget('contracts', { owner: 'b', bound: ['c'] }, by),\n"
        "  f.recordTarget('holes', { binds: ['a'] }, by),\n"
        "  f.elementTarget('a.x', by), f.elementTarget('c', by),\n"
        "]));\n"
    )
    assert run(code) == ["areas/alpha.md", "README.md", "README.md", "areas/alpha.md", "areas/zeta.md", "areas/alpha.md", "README.md"]


def test_relative_links() -> None:
    assert [facts("relative", "README.md", "areas/a.md"), facts("relative", "areas/a.md", "README.md"),
            facts("relative", "areas/a.md", "areas/b.md"), facts("relative", "README.md", "README.md")] == [
        "areas/a.md", "../README.md", "b.md", "README.md",
    ]


def test_top_level() -> None:
    assert [facts("topLevel", "a"), facts("topLevel", "a.x.y")] == ["a", "a"]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_facts.py`. Expected: FAIL (module not found).
- [ ] **Step 3: GREEN.** Create `facts.mjs`:

```js
// Facts the documents share, from the format 4 export: which areas hold each element and record, where each id is
// written in full, and relative links between documents (paths from the output folder, with '/').
import path from 'node:path';
import { cmp } from '../architecture-delta/report.mjs';

export const OVERVIEW = 'README.md';
export const IMPROVEMENTS = 'improvements.md';
export const areaDoc = (name) => `areas/${name}.md`;
export const capabilityDoc = (name) => `capabilities/${name}.md`;
export const changeDoc = (id) => `changes/${id}.md`;

// Spec, Terms: element ids are dotted paths; a top-level element has no dot.
export const topLevel = (id) => id.split('.')[0];

// Spec, Areas: an element's areas are the area views it is an element of, sorted by name.
export function areasByElement(data) {
  const byElement = new Map(data.elements.map((element) => [element.id, []]));
  for (const area of data.areas) for (const id of area.elements) byElement.get(id)?.push(area.name);
  for (const names of byElement.values()) names.sort(cmp);
  return byElement;
}

const has = (record, key) => Object.hasOwn(record, key);
export const isCrossCutting = (decision) => has(decision, 'obligations');
export const isPrinciple = (decision) => isCrossCutting(decision) && decision.binds.length === 0 && !has(decision, 'owner');

// Spec, Shared rules: a record's areas are the areas of the elements it binds (a contract's owner and bound elements).
export function recordElements(kind, record) {
  return kind === 'contracts' ? [record.owner, ...record.bound] : record.binds;
}

export function areasOf(ids, byElement) {
  return [...new Set(ids.flatMap((id) => byElement.get(id) ?? []))].sort(cmp);
}

// Where an id is written in full: its first area's document, or the overview.
export function elementTarget(id, byElement) {
  const areas = byElement.get(id) ?? [];
  return areas.length > 0 ? areaDoc(areas[0]) : OVERVIEW;
}

// A principle binds no element, so it has no area and is written in the overview.
export function recordTarget(kind, record, byElement) {
  const areas = areasOf(recordElements(kind, record), byElement);
  return areas.length > 0 ? areaDoc(areas[0]) : OVERVIEW;
}

// Spec, Shared rules: ids are shown as written, titles beside them.
export function titlesOf(data) {
  return {
    elements: new Map(data.elements.map((element) => [element.id, element.title])),
    areas: new Map(data.areas.map((area) => [area.name, area.title])),
    capabilities: new Map(data.capabilities.map((capability) => [capability.name, capability.title])),
  };
}

export function relative(from, to) {
  const rel = path.posix.relative(path.posix.dirname(from), to);
  return rel === '' ? path.posix.basename(to) : rel;
}
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_facts.py tests/scripts/test_architecture_docs_safety.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/facts.mjs tests/scripts/test_architecture_docs_facts.py && git commit -m "feat(#32): the facts the documents share"`

### Task 5: decisions, contracts and open questions in full

**Tier:** standard — complete code.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/records-doc.mjs`
- Test: `tests/scripts/test_architecture_docs_facts.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- a decision with no reason — mutation: print `null` — killed by: `test_decision_in_full` ("Reason not known")
- superseded decisions — mutation: print the status without the link — killed by: `test_decision_in_full`
- "Also binds" leaves out the document's own area — mutation: drop the filter — killed by: `test_decision_in_an_area_document`
- titles beside ids — mutation: drop the title part of `withTitle` — killed by: `test_decision_in_full`, `test_contract_and_open_question_in_full`
- a contract's compatibility of `null` — mutation: print `null` — killed by: `test_contract_and_open_question_in_full` ("No rule stated")

- Satisfies Spec AC: AC-20 (records in full)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append to `tests/scripts/test_architecture_docs_facts.py`:

```python
def blocks(js: str, doc: str = "README.md", area: str = "null") -> object:
    import json
    from arch_delta_support import lib_url, run_module
    code = (
        f"import * as f from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\n"
        f"import * as r from {json.dumps(lib_url('records-doc.mjs', DOCS_LIB))};\n"
        f"const data = {json.dumps(DATA)};\n"
        "const byElement = f.areasByElement(data);\n"
        "const decisions = new Map([['D-0', { id: 'D-0', binds: ['b'] }]]);\n"
        f"const ctx = {{ doc: {json.dumps(doc)}, byElement, titles: f.titlesOf(data), decisions, area: {area} }};\n"
        f"process.stdout.write(JSON.stringify({js}));\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def L(text: str, href: str) -> dict:
    return {"type": "link", "text": text, "href": href}


DECISION = ("{ id: 'D-1', decision: 'Use one store.', reason: null, rejected: ['Two stores', 'None'], binds: ['a', 'b'], "
            "status: 'superseded', superseded_by: 'D-0', evidence: 'spec', sources: ['docs/x.md'], owner: 'a', "
            "obligations: ['Keep ids'], compatibility: 'Additive only.', capabilities: ['pay'], note: 'N' }")


def test_decision_in_full() -> None:
    assert blocks(f"r.decisionBlocks({DECISION}, ctx)") == [
        {"type": "heading", "level": 3, "text": "D-1"},
        {"type": "paragraph", "parts": ["Use one store."]},
        {"type": "list", "items": [
            ["Reason: ", "Reason not known"],
            ["Rejected: ", "Two stores; None"],
            ["Obligations: ", "Keep ids"],
            ["Owner: ", L("a", "areas/zeta.md"), " (A)"],
            ["Compatibility: ", "Additive only."],
            ["Capabilities: ", L("pay", "capabilities/pay.md"), " (Pay)"],
            ["Status: superseded by ", L("D-0", "areas/alpha.md")],
            ["Evidence: ", "spec"],
            ["Sources: ", "docs/x.md"],
            ["Note: ", "N"],
            ["Binds: ", L("a", "areas/zeta.md"), " (A)", ", ", L("b", "areas/alpha.md"), " (B)"],
            ["Areas: ", L("alpha", "areas/alpha.md"), " (Alpha)", ", ", L("zeta", "areas/zeta.md"), " (Zeta)"],
        ]},
    ]


def test_decision_in_an_area_document() -> None:
    items = blocks(f"r.decisionBlocks({DECISION}, ctx)", doc="areas/zeta.md", area="'zeta'")[2]["items"]
    assert items[-1] == ["Also binds: ", L("alpha", "alpha.md"), " (Alpha)"]
    assert items[3] == ["Owner: ", L("a", "zeta.md"), " (A)"]


def test_contract_and_open_question_in_full() -> None:
    contract = "{ id: 'C-1', name: 'Orders API', owner: 'b', bound: ['c'], obligations: ['Ids', 'Order'], compatibility: null, decisions: ['D-0'] }"
    assert blocks(f"r.contractBlocks({contract}, ctx)") == [
        {"type": "heading", "level": 3, "text": "C-1: Orders API"},
        {"type": "list", "items": [
            ["Owner: ", L("b", "areas/alpha.md"), " (B)"],
            ["Bound: ", L("c", "README.md"), " (C)"],
            ["Obligations: ", "Ids; Order"],
            ["Compatibility: ", "No rule stated"],
            ["Decisions: ", L("D-0", "areas/alpha.md")],
            ["Areas: ", L("alpha", "areas/alpha.md"), " (Alpha)"],
        ]},
    ]
    hole = "{ id: 'H-1', what: 'Why two caches?', binds: ['c'], evidence: 'search' }"
    assert blocks(f"r.holeBlocks({hole}, ctx)") == [
        {"type": "heading", "level": 3, "text": "H-1"},
        {"type": "paragraph", "parts": ["Why two caches?"]},
        {"type": "list", "items": [["Binds: ", L("c", "README.md"), " (C)"], ["Evidence: ", "search"]]},
    ]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_facts.py -k "in_full or area_document"`. Expected: FAIL (module not found).
- [ ] **Step 3: GREEN.** Create `records-doc.mjs`:

```js
// Decisions, contracts and open questions printed in full, as document-tree blocks. `ctx`: { doc (the path of the
// document being built), byElement (areasByElement), titles (titlesOf), decisions (Map of id to decision), area (the
// area of an area document, or null) }.
import { heading, paragraph, list, docLink } from './tree.mjs';
import { areaDoc, areasOf, capabilityDoc, elementTarget, recordElements, recordTarget, relative } from './facts.mjs';

const has = (record, key) => Object.hasOwn(record, key);
const separated = (parts) => parts.flatMap((part, index) => (index === 0 ? [part] : [', ', part]));
// Spec, Shared rules: an id is shown as written, with its title beside it.
const titled = (groups) => groups.flatMap((group, index) => (index === 0 ? group : [', ', ...group]));
const withTitle = (id, href, title) => [docLink(id, href), ` (${title ?? id})`];

export const elementLinks = (ids, ctx) => titled(ids.map((id) =>
  withTitle(id, relative(ctx.doc, elementTarget(id, ctx.byElement)), ctx.titles.elements.get(id))));
export const areaLinks = (names, ctx) => titled(names.map((name) =>
  withTitle(name, relative(ctx.doc, areaDoc(name)), ctx.titles.areas.get(name))));
const capabilityLinks = (names, ctx) => titled(names.map((name) =>
  withTitle(name, relative(ctx.doc, capabilityDoc(name)), ctx.titles.capabilities.get(name))));

function decisionLink(id, ctx) {
  const decision = ctx.decisions.get(id);
  return decision === undefined ? id : docLink(id, relative(ctx.doc, recordTarget('decisions', decision, ctx.byElement)));
}

// Spec, Area: the other areas the record is in ("Also binds" in an area document; "Areas" elsewhere).
function areasItem(kind, record, ctx, alsoLabel) {
  const names = areasOf(recordElements(kind, record), ctx.byElement).filter((name) => name !== ctx.area);
  if (names.length === 0) return [];
  return [[ctx.area === null ? 'Areas: ' : alsoLabel, ...areaLinks(names, ctx)]];
}

export function decisionBlocks(decision, ctx, level = 3) {
  const items = [['Reason: ', decision.reason ?? 'Reason not known']];
  if (decision.rejected.length > 0) items.push(['Rejected: ', decision.rejected.join('; ')]);
  if (has(decision, 'obligations')) items.push(['Obligations: ', decision.obligations.join('; ')]);
  if (has(decision, 'owner')) items.push(['Owner: ', ...elementLinks([decision.owner], ctx)]);
  if (has(decision, 'compatibility')) items.push(['Compatibility: ', decision.compatibility]);
  if ((decision.capabilities ?? []).length > 0) items.push(['Capabilities: ', ...capabilityLinks(decision.capabilities, ctx)]);
  items.push(decision.status === 'superseded'
    ? ['Status: superseded by ', decisionLink(decision.superseded_by, ctx)]
    : ['Status: ', decision.status]);
  items.push(['Evidence: ', decision.evidence]);
  if (decision.sources.length > 0) items.push(['Sources: ', decision.sources.join('; ')]);
  if (has(decision, 'note')) items.push(['Note: ', decision.note]);
  if (decision.binds.length > 0) items.push(['Binds: ', ...elementLinks(decision.binds, ctx)]);
  items.push(...areasItem('decisions', decision, ctx, 'Also binds: '));
  return [heading(level, decision.id), paragraph(decision.decision), list(items)];
}

export function contractBlocks(contract, ctx, level = 3) {
  const items = [
    ['Owner: ', ...elementLinks([contract.owner], ctx)],
    ['Bound: ', ...elementLinks(contract.bound, ctx)],
    ['Obligations: ', contract.obligations.join('; ')],
    ['Compatibility: ', contract.compatibility ?? 'No rule stated'],
  ];
  if ((contract.notes ?? []).length > 0) items.push(['Notes: ', contract.notes.join('; ')]);
  if ((contract.decisions ?? []).length > 0) items.push(['Decisions: ', ...separated(contract.decisions.map((id) => decisionLink(id, ctx)))]);
  if ((contract.capabilities ?? []).length > 0) items.push(['Capabilities: ', ...capabilityLinks(contract.capabilities, ctx)]);
  items.push(...areasItem('contracts', contract, ctx, 'Also in: '));
  return [heading(level, `${contract.id}: ${contract.name}`), list(items)];
}

export function holeBlocks(hole, ctx, level = 3) {
  const items = [];
  if (hole.binds.length > 0) items.push(['Binds: ', ...elementLinks(hole.binds, ctx)]);
  items.push(['Evidence: ', hole.evidence]);
  if (has(hole, 'note')) items.push(['Note: ', hole.note]);
  return [heading(level, hole.id), paragraph(hole.what), list(items)];
}
```

(`test_contract_and_open_question_in_full` lists no "Areas" item for the hole: `c` is in no area.)

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_facts.py tests/scripts/test_architecture_docs_safety.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/records-doc.mjs tests/scripts/test_architecture_docs_facts.py && git commit -m "feat(#32): decisions, contracts and open questions in full"`

### Task 6: known-gap cleaning moves into `build.mjs`

**Tier:** standard — complete code; a move with a new direct test.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/build.mjs` (`cleanGap`), `skills/shared/scripts/architecture-docs.mjs` (`readGap` uses it)
- Test: `tests/scripts/test_architecture_docs_build.py` (create)

**Callers that move with this task:** the `readGap` sweep row.

**Reviewer looks at:**
- known-gap cleaning — mutation: `clean` on `reason` — killed by: `test_clean_gap` (the 250-character reason is not cut); mutation: `cleanText` on `from` — killed by the same test (the 250-character id is cut)

- Satisfies Spec AC: AC-12 (known-gap text)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_docs_build.py`:

```python
"""The documents of one build (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

from arch_delta_support import DOCS_LIB, call, require_node

require_node()


def test_clean_gap() -> None:  # AC-12 (known-gap text is cleaned like export output)
    entries = [{"from": "a" * 250, "to": "b", "reason": "r" * 250 + chr(27) + "[31m" + chr(0x202E) + "\nnext", "close_by": None}]
    result = call("build.mjs", "cleanGap", entries, lib=DOCS_LIB)
    assert result["value"] == [{"from": "a" * 199 + chr(0x2026), "to": "b", "reason": "r" * 250 + "\nnext", "close_by": None}]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_build.py`. Expected: FAIL (`cleanGap` is not a function).
- [ ] **Step 3: GREEN.** In `build.mjs`, change the errors import to `import { ToolError, clean, cleanText } from '../architecture-delta/errors.mjs';` and add:

```js
// Spec, The tool: known-gap entries are cleaned like `export` output before any document uses them.
export function cleanGap(entries) {
  return entries.map((entry) => ({
    from: clean(entry.from),
    to: clean(entry.to),
    reason: cleanText(entry.reason),
    close_by: entry.close_by === null ? null : cleanText(entry.close_by),
  }));
}
```

Make the `architecture-docs.mjs` sweep edit (`readGap` returns `cleanGap(entries)`).
- [ ] **Step 4:** `uv run pytest -q tests/scripts -k "architecture_docs"`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs.mjs skills/shared/scripts/architecture-docs/build.mjs tests/scripts/test_architecture_docs_build.py && git commit -m "refactor(#32): known-gap cleaning moves into build.mjs, with its own test"`

### Task 7: the overview, built into `README.md` and `index.html`

**Tier:** standard — complete code; assembly of the earlier modules.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/overview.mjs`
- Modify: `skills/shared/scripts/architecture-docs/build.mjs` (overview files)
- Modify: `docs/superpowers/specs/2026-11-17-architecture-docs-design.md` (the overview heading)
- Test: `tests/scripts/test_architecture_docs_overview.py` (create); `tests/scripts/test_architecture_docs_tool.py` (sweep rows)

**Callers that move with this task:** the `test_architecture_docs_tool.py` sweep rows.

**Reviewer looks at:**
- relationships lifted to top-level elements — mutation: draw unlifted pairs — killed by: `test_overview_sections` (one arrow `n1 --> n2` for two child-level imports)
- solid when any lifted relationship is an import — mutation: dashed whenever a runtime link is present — killed by: `test_overview_sections` (the `shop`→`pay` pair has an import and an `http` link and is solid)
- changes newest first — mutation: oldest first — killed by: `test_overview_sections`
- "Not in any area" — mutation: list every element — killed by: `test_overview_sections`; mutation: leave principles in it — killed by the same test
- a relationship within one top-level element is not drawn — mutation: drop `if (from === to) return;` — killed by: `test_overview_lifts_sorts_and_counts`
- the kinds of a dashed arrow sorted — mutation: drop the sort — killed by: `test_overview_lifts_sorts_and_counts` ("event, http")
- model health counts and links — mutation: unmapped count always 0, or drop the open-questions line — killed by: `test_overview_lifts_sorts_and_counts`
- no-area contracts in full — mutation: drop the no-area contract loop — killed by: `test_overview_lifts_sorts_and_counts`

**Pinned by:** the over-80-arrow note is reached through `flowchart` returning `null`, pinned by `test_flowchart_arrow_limit` (Task 3); the note's wording is not asserted.

- Satisfies Spec AC: AC-12 and AC-13 (end to end), AC-18 (overview part; the two-area case is plan 3's), AC-20 and AC-24 (overview parts)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_docs_overview.py`:

```python
"""The overview document (spec 2026-11-17-architecture-docs-design.md, "Overview")."""

from __future__ import annotations

import json
import re
from pathlib import Path

from arch_delta_support import DOCS_LIB, DOCS_SCRIPT, call, make_repo, require_node, run_tool

require_node()

MODEL = """specification {
  relationship http
}
model {
  shop = system 'Shop' {
    description 'Sells things'
    web = container 'Web'
    api = container 'API'
  }
  pay = system 'Pay'
  bank = system 'Bank'
  shop.web -> pay 'charges'
  shop.api -> pay
  shop.api -[http]-> pay 'notifies'
  pay -[http]-> bank 'settles'
}
views {
  view area-front of shop {
    include *
  }
  dynamic view capability-buy {
    title 'Buy'
    shop.web -> pay
  }
}
"""


def write(folder: Path, rel: str, data: object) -> None:
    target = folder / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data), encoding="utf-8")


def decision(id_: str, **over) -> dict:
    record = {"id": id_, "decision": "Decide " + id_ + ".", "reason": "Because.", "rejected": [], "binds": ["shop.web"],
              "status": "current", "evidence": "spec", "sources": ["docs/x.md"]}
    record.update(over)
    return record


def change(id_: str, summary: str, approved: object) -> dict:
    lists = {"added": [], "changed": [], "removed": []}
    return {"id": id_, "date": id_[:10], "run": "baseline", "asked_by": "#1", "summary": summary, "rejected": [],
            "elements": lists, "decisions": lists, "holes": lists, "contracts": lists, "gap": {"added": [], "removed": []},
            "check": {"exit": 0, "summary": "ok", "output": "ok\n"}, "approved": approved}


def build(tmp_path: Path) -> Path:
    repo = make_repo(tmp_path, MODEL)
    folder = repo / "docs" / "architecture"
    write(folder, "decisions/core.json", {"title": "Core", "holes": [{"id": "H-1", "what": "Why a bank?", "binds": ["bank"], "evidence": "search"}],
                                          "decisions": [decision("D-1"), decision("D-2", binds=["bank"]),
                                                        decision("P-1", binds=[], obligations=["Data stays in the EU."])]})
    write(folder, "contracts/edge.json", {"title": "Edge", "contracts": [
        {"id": "C-1", "name": "Card API", "owner": "pay", "bound": ["shop.web"], "obligations": ["Ids"], "compatibility": None}]})
    write(folder, "changes/2026-11-01-baseline.json", change("2026-11-01-baseline", "Baseline.", {"by": "Owner", "date": "2026-11-02"}))
    write(folder, "changes/2026-11-05-more.json", change("2026-11-05-more", "More.", None))
    write(folder, "known-gap.json", {"entries": [{"from": "pay", "to": "shop.api", "reason": "cycle in current code"}]})
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    return folder / "generated"


def test_overview_sections(tmp_path) -> None:  # AC-18, AC-20 (overview parts)
    text = (build(tmp_path) / "README.md").read_text(encoding="utf-8")
    sections = text.split("\n\n")
    assert sections[1] == "# Architecture"
    assert "## System" in sections
    assert ('```mermaid\nflowchart LR\n  n1["Bank"]\n  n2["Pay"]\n  n3["Shop"]\n'
            '  n2 -.->|"http"| n1\n  n3 --> n2\n```') in sections
    assert "| Area | Description | Elements |\n| --- | --- | --- |\n| [Shop](areas/front.md) |  | 3 |" in sections
    assert "| Capability | Description | Areas |\n| --- | --- | --- |\n| [Buy](capabilities/buy.md) |  | [front](areas/front.md) \\(Shop\\) |" in sections
    principles = sections[sections.index("## Principles"):sections.index("## Contracts")]
    assert principles[1:3] == ["### P\\-1", "Decide P\\-1\\."]
    assert ("| Contract | Owner | Bound | Compatibility |\n| --- | --- | --- | --- |\n"
            "| [C\\-1: Card API](areas/front.md) | [pay](README.md) \\(Pay\\) | [shop\\.web](areas/front.md) \\(Web\\) | No rule stated |") in sections
    changes = sections[sections.index("## Changes") + 1]
    assert changes == ("- [2026\\-11\\-05\\-more](changes/2026-11-05-more.md) \\(2026\\-11\\-05\\): More\\. \\(not yet approved\\)\n"
                       "- [2026\\-11\\-01\\-baseline](changes/2026-11-01-baseline.md) \\(2026\\-11\\-01\\): Baseline\\. "
                       "\\(approved by Owner on 2026\\-11\\-02\\)")
    health = sections[sections.index("## Model health") + 1]
    assert health.startswith("- Known\\-gap entries: 1, see [the improvement list](improvements.md)\n")
    assert "- Coverage: No coverage file" in health
    loose = sections[sections.index("## Not in any area") + 1]
    assert loose == "| Element | Title | Description |\n| --- | --- | --- |\n| bank | Bank |  |\n| pay | Pay |  |"
    after = sections[sections.index("## Not in any area"):]
    assert "### D\\-2" in after and "### H\\-1" in after and "### P\\-1" not in after and "### D\\-1" not in after


def test_overview_lifts_sorts_and_counts(tmp_path) -> None:  # Overview: lifting and kinds; model health; no-area records
    model = MODEL.replace("relationship http\n", "relationship http\n  relationship event\n").replace(
        "  pay -[http]-> bank 'settles'\n",
        "  pay -[http]-> bank 'settles'\n  shop.web -> shop.api\n  shop.api -[http]-> bank\n  shop.web -[event]-> bank\n")
    repo = make_repo(tmp_path, model)
    folder = repo / "docs" / "architecture"
    write(folder, "decisions/core.json", {"title": "Core", "holes": [], "decisions": [decision("D-3", binds=[])]})
    write(folder, "contracts/edge.json", {"title": "Edge", "contracts": [
        {"id": "C-2", "name": "Bank feed", "owner": "bank", "bound": ["pay"], "obligations": ["Daily"], "compatibility": "Additive."}]})
    write(folder, "coverage.json", {"answer": "Most code is mapped.", "baselined": [], "edge_nodes": [],
                                    "counts": {"modules": 3, "groups": 1},
                                    "unmapped": [{"module": "a", "reason": "r"}, {"module": "b", "reason": "r"}]})
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    sections = (folder / "generated" / "README.md").read_text(encoding="utf-8").split("\n\n")
    assert ('```mermaid\nflowchart LR\n  n1["Bank"]\n  n2["Pay"]\n  n3["Shop"]\n'
            '  n2 -.->|"http"| n1\n  n3 -.->|"event#44; http"| n1\n  n3 --> n2\n```') in sections
    see = ", see [the improvement list](improvements.md)"
    assert sections[sections.index("## Model health") + 1] == (
        f"- Known\\-gap entries: 0{see}\n- Open questions: 0{see}\n- Coverage: Most code is mapped\\.{see}\n- Unmapped modules: 2{see}")
    assert ("| [C\\-2: Bank feed](README.md) | [bank](README.md) \\(Bank\\) | [pay](README.md) \\(Pay\\) | Additive\\. |"
            in sections[sections.index("## Contracts") + 1])
    after = sections[sections.index("## Not in any area"):]
    assert "### D\\-3" in after and "### C\\-2: Bank feed" in after


def test_overview_page_matches_and_is_marked(tmp_path) -> None:  # AC-13
    folder = build(tmp_path)
    page = (folder / "index.html").read_text(encoding="utf-8")
    assert page.startswith("<!-- Generated by architecture-docs from the architecture model. Do not edit. -->\n<!doctype html>\n")
    assert '<a href="areas/front.html">Shop</a>' in page and page.count("<script") == 2


def test_overview_escapes_hostile_model_text(tmp_path) -> None:  # AC-12
    hostile = "[x](javascript:alert(1)) <script> | ` %%{init}%% ;"
    repo = make_repo(tmp_path, "model {\n  a = system '" + hostile + "' {\n    description '" + hostile + "'\n  }\n}\n")
    assert run_tool("build", "--repo", repo, script=DOCS_SCRIPT).returncode == 0
    folder = repo / "docs" / "architecture" / "generated"
    text = (folder / "README.md").read_text(encoding="utf-8")
    page = (folder / "index.html").read_text(encoding="utf-8")
    escaped = "\\[x\\]\\(javascript:alert\\(1\\)\\) &lt;script&gt; \\| \\` %%\\{init\\}%% ;"
    assert f"| a | {escaped} | {escaped} |" in text.split("\n")
    assert "](javascript" not in text and "<script" not in text
    assert page.count("<script") == 2 and '<a href="javascript' not in page and "&lt;script&gt;" in page
    node = [line for line in text.split("\n") if line.startswith('  n1["')][0]
    label = node[len('  n1["'):-len('"]')]
    assert '"' not in label and "%%" not in label and "#37;#37;" in label
    assert ";" not in re.sub(r"#[0-9]+;", "", label)
```

Make the sweep edits to `tests/scripts/test_architecture_docs_tool.py`.

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_overview.py tests/scripts/test_architecture_docs_tool.py`. Expected: FAIL (no `README.md`; the sweep asserts expect three files).
- [ ] **Step 3: GREEN.** Create `overview.mjs`:

```js
// The overview document: the system diagram, areas, capabilities, principles, contracts, changes, model health, and
// everything in no area.
import { cmp } from '../architecture-delta/report.mjs';
import { doc, heading, paragraph, list, table, diagram, docLink } from './tree.mjs';
import { flowchart } from './mermaid.mjs';
import {
  OVERVIEW, IMPROVEMENTS, areaDoc, capabilityDoc, changeDoc, topLevel, areasByElement, areasOf, isPrinciple, recordElements,
  recordTarget, titlesOf,
} from './facts.mjs';
import { decisionBlocks, contractBlocks, holeBlocks, elementLinks, areaLinks } from './records-doc.mjs';

export const OVERVIEW_TITLE = 'Architecture';

// Spec, Overview: relationships lifted to the top-level elements; one arrow per pair, solid when any lifted
// relationship is an import, otherwise dashed and labelled with the sorted kinds.
function systemDiagram(data) {
  const nodes = data.elements.filter((element) => !element.id.includes('.')).map((element) => ({ id: element.id, text: element.title }));
  if (nodes.length === 0) return paragraph('The model has no elements.');
  const pairs = new Map();
  const lift = (relationship, kind) => {
    const from = topLevel(relationship.from);
    const to = topLevel(relationship.to);
    if (from === to) return;
    const key = JSON.stringify([from, to]);
    if (!pairs.has(key)) pairs.set(key, { from, to, solid: false, kinds: new Set() });
    const pair = pairs.get(key);
    if (kind === null) pair.solid = true;
    else pair.kinds.add(kind);
  };
  for (const relationship of data.allowed) lift(relationship, null);
  for (const relationship of data.runtime) lift(relationship, relationship.kind);
  const arrows = [...pairs.values()]
    .sort((x, y) => cmp(x.from, y.from) || cmp(x.to, y.to))
    .map((pair) => ({ from: pair.from, to: pair.to, dashed: !pair.solid, text: pair.solid ? '' : [...pair.kinds].sort(cmp).join(', ') }));
  const text = flowchart(nodes, arrows);
  return text === null ? paragraph('The system diagram has more than 80 arrows and is not drawn; the tables list every element.') : diagram(text);
}

const orNone = (parts) => (parts.length > 0 ? parts : ['None']);

export function buildOverview(data, gap) {
  const byElement = areasByElement(data);
  const ctx = { doc: OVERVIEW, byElement, titles: titlesOf(data), decisions: new Map(data.decisions.map((d) => [d.id, d])), area: null };
  const blocks = [heading(2, 'System'), systemDiagram(data)];

  blocks.push(heading(2, 'Areas'));
  blocks.push(data.areas.length === 0 ? paragraph('The model has no area views.')
    : table(['Area', 'Description', 'Elements'], data.areas.map((area) => [
      [docLink(area.title, areaDoc(area.name))], [area.description ?? ''], [String(area.elements.length)]])));

  blocks.push(heading(2, 'Capabilities'));
  blocks.push(data.capabilities.length === 0 ? paragraph('The model has no capability views.')
    : table(['Capability', 'Description', 'Areas'], data.capabilities.map((capability) => [
      [docLink(capability.title, capabilityDoc(capability.name))], [capability.description ?? ''],
      orNone(areaLinks(areasOf(capability.steps.flatMap((step) => [step.from, step.to]), byElement), ctx))])));

  blocks.push(heading(2, 'Principles'));
  const principles = data.decisions.filter(isPrinciple);
  if (principles.length === 0) blocks.push(paragraph('No principles.'));
  for (const principle of principles) blocks.push(...decisionBlocks(principle, ctx));

  blocks.push(heading(2, 'Contracts'));
  blocks.push(data.contracts.length === 0 ? paragraph('No contracts.')
    : table(['Contract', 'Owner', 'Bound', 'Compatibility'], data.contracts.map((contract) => [
      [docLink(`${contract.id}: ${contract.name}`, recordTarget('contracts', contract, byElement))],
      elementLinks([contract.owner], ctx), elementLinks(contract.bound, ctx), [contract.compatibility ?? 'No rule stated']])));

  blocks.push(heading(2, 'Changes'));
  const changes = [...data.changes].sort((x, y) => cmp(y.date, x.date) || cmp(x.id, y.id));
  blocks.push(changes.length === 0 ? paragraph('No change records.') : list(changes.map((change) => [
    docLink(change.id, changeDoc(change.id)),
    ` (${change.date}): ${change.summary} `,
    change.approved === null ? '(not yet approved)' : `(approved by ${change.approved.by} on ${change.approved.date})`,
  ])));

  blocks.push(heading(2, 'Model health'));
  const see = [', see ', docLink('the improvement list', IMPROVEMENTS)];
  blocks.push(list([
    [`Known-gap entries: ${gap.length}`, ...see],
    [`Open questions: ${data.holes.length}`, ...see],
    [`Coverage: ${data.coverage === null ? 'No coverage file' : data.coverage.answer}`, ...see],
    [`Unmapped modules: ${data.coverage === null ? 0 : data.coverage.unmapped.length}`, ...see],
  ]));

  // Spec, Overview: the elements in no area, then every record (other than a principle) that has no area.
  blocks.push(heading(2, 'Not in any area'));
  const loose = data.elements.filter((element) => byElement.get(element.id).length === 0);
  const noArea = (kind, record) => areasOf(recordElements(kind, record), byElement).length === 0;
  const decisions = data.decisions.filter((d) => !isPrinciple(d) && noArea('decisions', d));
  const contracts = data.contracts.filter((c) => noArea('contracts', c));
  const holes = data.holes.filter((h) => noArea('holes', h));
  if (loose.length > 0) {
    blocks.push(table(['Element', 'Title', 'Description'], loose.map((element) => [[element.id], [element.title], [element.description ?? '']])));
  }
  for (const record of decisions) blocks.push(...decisionBlocks(record, ctx));
  for (const record of contracts) blocks.push(...contractBlocks(record, ctx));
  for (const record of holes) blocks.push(...holeBlocks(record, ctx));
  if (loose.length + decisions.length + contracts.length + holes.length === 0) {
    blocks.push(paragraph('Every element and record is in an area.'));
  }
  return doc(OVERVIEW_TITLE, blocks);
}
```

In `build.mjs`, add the imports `import { buildOverview } from './overview.mjs';`, `import { renderMarkdown } from './markdown.mjs';` and `import { renderHtml } from './html.mjs';`, and replace `buildFiles` with:

```js
// Spec, What each document holds: every document is built from the export (and the cleaned known-gap entries).
export function buildFiles(model, records, gap, tick = () => {}) {
  const data = exportJson(model, records);
  const files = {};
  files['pack/model.json'] = `${JSON.stringify({ generated: 'architecture-docs', export: data }, null, 2)}\n`;
  tick();
  const overview = buildOverview(data, gap);
  files['README.md'] = renderMarkdown(overview);
  files['index.html'] = renderHtml(overview);
  tick();
  return files;
}
```

In the spec's "Overview" list, replace "- The system title, and a diagram of the top-level elements" with "- The heading \"Architecture\", and a diagram of the top-level elements".

- [ ] **Step 4:** `uv run pytest -q tests/scripts -k "architecture_docs or architecture_delta"`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs tests/scripts docs/superpowers/specs/2026-11-17-architecture-docs-design.md && git commit -m "feat(#32): the overview, as README.md and index.html"`
