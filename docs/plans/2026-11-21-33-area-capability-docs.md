# Architecture Docs: Area and Capability Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `architecture-docs build` also writes `areas/<name>.md` and `.html` and `capabilities/<name>.md` and `.html`, and `check` compares them; the pack area slice lists the capabilities through the area, and pack text guards code fences and the line separators U+2028 and U+2029.

**Architecture:** This repository has no architecture model. New modules in `skills/shared/scripts/architecture-docs/`: `area-diagram.mjs` (the drawing rules, shared with the change records of plan 4), `area.mjs` (the area document) and `capability.mjs` (the capability document). `mermaid.mjs` gains a frame and red arrows for the flowchart, and the sequence diagram. `facts.mjs` gains the per-element link index (moved from `pack-blocks.mjs`, so the area documents and the pack share it), an area's capabilities, and `documentBase`, the lookups every area and capability document reads, built once per build. `pack-text.mjs` and `pack.mjs` take the spec amendment of 2026-11-21. `build.mjs` adds the documents to the build, each with a `--timeout` check after it.

**Tech Stack:** Node ESM, pytest.

**Spec:** `docs/superpowers/specs/2026-11-17-architecture-docs-design.md`, "Writers" (Pack text, Diagrams), "What each document holds" (Shared rules, Drawing rules, Area, Capability, AI pack for the area slice's capabilities), AC-9 (the area case left by plan 2a), AC-12 and AC-13 (area and capability parts), AC-17 (the `capabilities` folder), AC-18, AC-19, AC-20 (the area part), AC-21, and the amended AC-25 and AC-26 — decisions applied: none. The owner settled seven questions on 2026-11-21 in one spec amendment (commit `c081dce`) before this plan: the pack area slice's `## Capabilities`, code-fence and U+2028/U+2029 guards in pack text, the field-line known limit, "Pack text" pointing to "Pack fields", neighbour labels naming their first area with no `click` lines, and the 80-arrow limit applying to flowcharts only. After the alignment check's first round the owner approved a second amendment (commit `6fae32e`): Dependencies name every area of the other end, only a drawn arrow hides another, the runtime arrow label's form, and neighbour labels using the first area's name. This is plan 3 of the spec's four (#33); plan 4 (change records and the improvement list, #34) reuses `area-diagram.mjs`.

**Open decisions:** none. The drawing rules' hiding, the runtime label, the neighbour label and the Dependencies areas are spec text since `6fae32e`. One rule pair the tasks apply as written: node ids follow element-id order ("Diagrams") and participants are declared in order of first appearance ("Capability").

**Size:** 9 tasks, 2 entry paths (`build`, `check`), 1961 lines (reported, not a target)

**Trust boundary:** changed — see Trust-boundary table. No new file writes: only `writer.mjs` writes, and the safety tests (`tests/scripts/test_architecture_docs_safety.py`) scan every new module unchanged. No comment or string in a docs module may hold a forbidden call name followed by `(`: the names in `CHANGES_FILES` (`write`, `link`, `rm`, `cp`, `rename`, `mkdir`, `unlink`, `truncate` and the others) must not be followed by an opening bracket anywhere in the new modules. The new documents carry model, record and known-gap text into Markdown, HTML and Mermaid; the writers' escaping and the label encoding are their defence, and Task 9 feeds hostile text through every new document.

### Risk & Confidence Assessment

**Confidence:** 90% — every code block was run: a dry run built each task from this plan's blocks in a scratch copy (per-task RED and GREEN counts below, then the full suite), and killed every "Reviewer looks at" mutation; the generated diagrams were parsed by Mermaid 12.2.0.

**Complexity Risk:** Medium — the implied-arrow rule: an arrow is hidden when another of its style runs from at or inside its source to at or inside its target, the two not the same; known-gap arrows never hide or are hidden. Five exact-arrow tests pin it.

**Environmental Risk:** Low — no new dependency, no new file write, no subprocess; the build at the 5,000-element cap was measured (see below).

**Unknown variables:**
- None in the repository. What stays unverified is the executor's transcription: a test or code block copied with a changed escape (`\\n`, `\\u2028`, `\\#`) fails its exact-text assert, which is the intended signal.
- How a reader's Markdown renderer lays out a Mermaid `subgraph` and `linkStyle`: the diagram text is parsed by Mermaid 12.2.0 in the dry run, not rendered.

**Main failure modes:** an arrow hidden or drawn against the drawing rules (Task 6 tests every case by exact arrow list); a section of a document missing, out of order or with a wrong link (Tasks 7 and 8 compare exact trees); a raw U+2028 typed into `pack-text.mjs` instead of the `\u2028` escape (a syntax error that fails every pack test); a module comment that names a forbidden call (the safety test fails the commit).

**Measured at the cap:** an export-shaped model of 5,000 elements, 10,000 imports, 5,000 runtime links, 2,000 decisions, 500 known-gap entries, 51 areas (one holding every element) and 20 capabilities of 300 steps builds its area documents in 1.21 s, its capability documents in 0.10 s, the pack in 0.09 s and the overview in 0.02 s (Markdown and HTML rendered), with the shared link index.

---

## Caller and test sweep

Searched: `skills/`, `tests/`, `scripts/`, `agents/` with `rg -n "linkIndex|flowchart\(|areaSlice|buildFiles|renderHtml\(overview|wrote [0-9]+ files|known-gap entries\. capab|headings\(text\) ==" skills tests scripts agents`, and `rg -n "rglob|iterdir" tests/scripts/test_architecture_docs_*.py` for tests that list the output folder.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `linkIndex` moves from `pack-blocks.mjs` to `facts.mjs` | `skills/shared/scripts/architecture-docs/pack-blocks.mjs:31-39` | definition | 2 | delete the comment line and the nine-line `function linkIndex` (Task 2 Step 3 gives the exact text) |
| same | `skills/shared/scripts/architecture-docs/pack-blocks.mjs:5` | import | 2 | `import { areasByElement, areasOf, isCrossCutting, linkIndex, recordElements } from './facts.mjs';` |
| same | `skills/shared/scripts/architecture-docs/pack-blocks.mjs:27` `links: linkIndex(data),` | caller | — | none: the name is now imported |
| the pack area slice ends with `## Capabilities` | `tests/scripts/test_architecture_docs_pack.py:329` (`test_area_slice` expected text) | assert | 3 | the last line becomes `...capabilities: buy [capabilities/buy.md]\n\n"` followed by `"## Capabilities\n\n- buy: Buy [capabilities/buy.md]\n"` (Task 3 Step 1) |
| same | `tests/scripts/test_architecture_docs_pack.py:336` (`test_area_slice_sections_and_order`) | assert | 3 | `assert headings(text) == ["## Elements", "## Decisions", "## Contracts", "## Open questions", "## Known gap", "## Capabilities"]` |
| same | `tests/scripts/test_architecture_docs_pack.py:338` | assert | 3 | `assert text.rstrip("\n").split("\n\n")[-3] == (` (the known-gap lines are now third from the end) |
| the layout paragraph names an area slice's capabilities | `tests/scripts/test_architecture_docs_pack.py:397` `parts[2].startswith("This pack holds the architecture model")` | assert | — | none: the paragraph's start is unchanged; Task 3 adds a test for the new sentence |
| `flowchart(nodes, arrows)` → `flowchart(nodes, arrows, frame = null)`; arrows may carry `red` | `skills/shared/scripts/architecture-docs/overview.mjs:34` | caller | — | none: no frame, and its arrows have no `red` |
| same | `tests/scripts/test_architecture_docs_writers.py:175-199` (four flowchart tests) | test | — | none: they pass two arguments and assert the unframed text, which is unchanged |
| `buildFiles` adds the area and capability documents | `skills/shared/scripts/architecture-docs.mjs:67` | caller | — | none: same signature and return shape |
| same | `tests/scripts/test_architecture_docs_tool.py:32`, `:47`, `:54`, `:56`, `:57`, `:156` (file counts and lists) | assert | — | none: the default test model (`SHOP_MODEL`) has no views, so it still writes four files |
| same | `tests/scripts/test_architecture_docs_pack.py:511` (`test_build_writes_the_pack` lists `pack/` only), `:554-563`, `:566-574` | assert | — | none: they look only under `pack/`, or assert single lines with `in` |
| same | `tests/scripts/test_architecture_docs_overview.py:61-74` (`build` with an area and a capability) | fixture | — | none: the overview tests read `README.md` and `index.html` only |
| the overview's two files are written through `addDocument` | `skills/shared/scripts/architecture-docs/build.mjs:29-31` | caller | 9 | replaced by `addDocument(files, 'README.md', buildOverview(data, gap));` (Task 9 Step 3) |

Not affected (checked): `tests/scripts/test_architecture_docs_writer.py:27` and `:51` list folders built from their own file sets; `tests/scripts/test_architecture_docs_out.py` calls `listOut` directly; `scripts/` and `agents/` hold no caller.

## Trust-boundary table

| Producer or reader | Where it is used | Text it receives | Untrusted source | Task | Proving test |
|---|---|---|---|---|---|
| `oneLine` and `multiLine` (U+2028, U+2029, fence lines) | every pack file, read raw by agents | export text, line feeds and separators kept | model and record authors | 1 | `test_pack_multi_line_fields_guard_code_fences`, `test_pack_line_separators_count_as_line_feeds` |
| the area slice's capability lines | `pack/areas/<name>.md` | capability names (view ids) and titles | model authors | 3 | `test_area_slice_lists_its_capabilities` (a title with a line feed on one line) |
| flowchart frame label, `linkStyle` line | area diagrams | area titles; arrow indices (numbers only) | model authors | 4 | `test_flowchart_frame_and_red_arrows` (a `;` in the frame label encoded) |
| sequence participant and message labels | capability diagrams | element titles, step labels | model authors | 5 | `test_sequence_diagram` (`;`, `:`, `%%{init}%%` encoded) |
| neighbour labels and runtime arrow labels | area diagrams | element titles, area names, relationship kinds and titles | model authors | 6, 9 | `test_area_drawing` (the label text); `test_build_escapes_hostile_text` (no `;`, `"` or `%%` in any diagram label) |
| area and capability document cells and paragraphs | Markdown and HTML documents | element titles, descriptions, code, rules, tags; record text; step labels; known-gap reason and `close_by` | model, record and known-gap authors | 7, 8, 9 | the writers' escaping (plan 2b, `test_markdown_escapes_model_text`, `test_html_escapes_every_value`); end to end: `test_build_escapes_hostile_text` (AC-12) |
| known-gap entries | area documents (Known gap table), area diagrams | `from`, `to`, `reason`, `close_by` | known-gap file authors | 9 | `test_build_escapes_hostile_text`: an escape sequence in `reason` and `close_by` never reaches a file (kills `readGap` skipping `cleanGap`, carried from plan 2b) |
| link targets | every new document | `areas/<name>.md`, `capabilities/<name>.md`, `README.md`, relative | model authors (view names) | 7, 8, 9 | names are `[a-z0-9-]`, 1 to 64 characters (plan 1's view rules); `relative` and `SAFE_HREF` refuse anything else (plan 2b); `test_build_writes_area_and_capability_documents` |
| output paths | `writer.mjs` (writes under `--out`) | `areas/<name>.md` and `.html`, `capabilities/<name>.md` and `.html` | model authors (view names) | 9 | `areas` and `capabilities` are in `out.mjs` `FOLDERS`; `test_check_reports_a_removed_area`, `test_build_removes_the_emptied_capabilities_folder` |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | Task 1 items 1–4 (strong), Task 2 items 1–3, Task 3 items 1–6; full suite `uv run pytest -q` (Task 2 moves code the pack reads) |
| C2 | 6 | 4–6 | Task 4 items 1–5, Task 5 items 1–6, Task 6 items 1–9; full suite `uv run pytest -q` (Task 4 changes the overview's flowchart function) |
| C3 | 9 | 7–9 | Task 7 items 1–11, Task 8 items 1–7, Task 9 items 1–8; full suite `uv run pytest -q` |

## Shared test fixture

Tasks 6 to 8 test the new modules against one export-shaped fixture, written in Task 6 into `tests/scripts/test_architecture_docs_area.py` and extended with records in Task 7. It is not a valid model (records skip fields the documents never print). Its areas: `front` (`shop`, `shop.api`, `shop.api.orders`, `shop.web`) and `money` (`pay`, `pay.gateway`); `bank` and `ledger` are in no area. It has an import implied by a more specific one (`shop.api -> pay` by `shop.api.orders -> pay.gateway`), a runtime link implied the same way (`shop -> pay`), an import and two runtime links between the same pair (`shop.web -> bank`), a relationship and a known-gap entry between two neighbours (`bank -> pay`, seen from `front`), and a known-gap entry to an element with no relationship (`shop.api -> ledger`). Task 9 builds a real model through `build` instead.

## How to apply the code blocks

Every edit is one of four kinds, each followed by its fenced block: **Create** a file, **Append to** a file (the block is added at its end), **Replace the contents of** a file, or **In** a file, **replace** one exact block **with** another (the old block occurs exactly once). Copy blocks byte for byte: the escapes `\n`, `\\`, `\u2028` and `\u2029` are part of the code. A block's fence may be four backticks when the code holds three.

---


### Task 1: pack text guards code fences and counts U+2028 and U+2029 as line feeds

**Tier:** strong — the pack text rules are the pack's only defence against record text an agent reads raw (trust boundary); complete code is given, but the tier stays strong for that boundary.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/pack-text.mjs`
- Test: `tests/scripts/test_architecture_docs_pack.py`

**Callers that move with this task:** none (every pack writer already goes through `oneLine` and `multiLine`)

**Reviewer looks at:**
1. Fence lines with backticks not guarded — mutation: in `pack-text.mjs`, drop the three backticks from `GUARDED` — killed by: `test_pack_multi_line_fields_guard_code_fences`
2. Fence lines with tildes not guarded — mutation: in `pack-text.mjs`, drop `~~~` from `GUARDED` — killed by: `test_pack_multi_line_fields_guard_code_fences`
3. One-line fields keep U+2028 and U+2029 — mutation: in `pack-text.mjs`, replace `export const oneLine = (text) => String(text).replace(LINE_BREAK, ' ');` with `export const oneLine = (text) => String(text).replace(/\n/g, ' ');` — killed by: `test_pack_line_separators_count_as_line_feeds`
4. Multi-line fields do not split at U+2028 and U+2029 — mutation: in `pack-text.mjs`, replace `String(text).replace(LINE_BREAK, '\n').split('\n')` with `String(text).split('\n')` — killed by: `test_pack_line_separators_count_as_line_feeds`

- Satisfies Spec AC: AC-25 (the fence line and the line separators); Writers, Pack text (amendment c081dce)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_docs_pack.py`:

`````python


def test_pack_multi_line_fields_guard_code_fences() -> None:  # Pack text: a fence line cannot open a code block
    text = "Use A.\n```js\n~~~\n``two\nkeep ``` here\n~~ two\n````"
    assert text_fn("multiLine", text) == "Use A.\n\\```js\n\\~~~\n``two\nkeep ``` here\n~~ two\n\\````"


def test_pack_line_separators_count_as_line_feeds() -> None:  # Pack text: U+2028 and U+2029; AC-25
    assert text_fn("oneLine", "a" + chr(0x2028) + "b" + chr(0x2029) + "c\nd") == "a b c d"
    assert text_fn("multiLine", "a" + chr(0x2028) + "# b" + chr(0x2029) + "--- c") == "a\n\\# b\n\\--- c"
`````

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_pack.py`
Expected: FAIL, 2 failed, 44 passed (the fence lines are not guarded; U+2028 and U+2029 are kept).

- [ ] **Step 3: GREEN.**

**Replace the contents of** `skills/shared/scripts/architecture-docs/pack-text.mjs` **with**:

````js
// Pack text (spec, Writers, Pack text): the pack is read raw by agents, so ids and text are written as `export` gives
// them, unescaped. The line separators U+2028 and U+2029 count as line feeds. A one-line field loses its line feeds; in
// a multi-line field every line is kept, and a line starting with `#`, `---`, three backticks or `~~~` gets a leading
// `\`, so record text cannot start a heading, a separator or a code fence.
import { MARKER } from './out.mjs';

const LINE_BREAK = /[\n\u2028\u2029]/g;
export const oneLine = (text) => String(text).replace(LINE_BREAK, ' ');

const GUARDED = /^(#|---|```|~~~)/;
export const multiLine = (text) => String(text).replace(LINE_BREAK, '\n').split('\n')
  .map((line) => (GUARDED.test(line) ? `\\${line}` : line)).join('\n');

// Spec, Pack layout: the marker line, `# <title>`, then the file's parts (headings, paragraphs and blocks of lines),
// one blank line apart, ending in one line feed.
export function packFile(title, parts) {
  return `${[MARKER, `# ${oneLine(title)}`, ...parts].join('\n\n')}\n`;
}
````

The pattern `[\n\u2028\u2029]` is written with `\u` escapes, not the characters themselves: a raw U+2028 inside a JavaScript regular expression literal is a line terminator and a syntax error.

- [ ] **Step 4: run GREEN and the callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_pack.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (50 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/pack-text.mjs tests/scripts/test_architecture_docs_pack.py
git commit -m "feat(#33): pack text guards code fence lines and treats U+2028 and U+2029 as line feeds"
```

---

### Task 2: the per-element link index moves into `facts.mjs`

**Tier:** fast — a pure move with every edit written out; the pack tests pin the behaviour.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/facts.mjs` (append `linkIndex`)
- Modify: `skills/shared/scripts/architecture-docs/pack-blocks.mjs` (drop its copy, import it)
- Test: `tests/scripts/test_architecture_docs_facts.py`

**Callers that move with this task:** sweep rows `pack-blocks.mjs:5` and `pack-blocks.mjs:31-39`

**Reviewer looks at:**
1. A decision binding an element twice is listed twice — mutation: in `facts.mjs`, replace `for (const id of new Set(decision.binds)) at(id).boundBy.push(decision);` with `for (const id of decision.binds) at(id).boundBy.push(decision);` — killed by: `test_link_index`
2. An entry naming an unknown element fails — mutation: in `facts.mjs`, replace `const at = (id) => index.get(id) ?? empty();` with `const at = (id) => index.get(id);` — killed by: `test_link_index`
3. Runtime links filed under the wrong end — mutation: in `facts.mjs`, replace `for (const link of data.runtime) { at(link.from).out.push(link); at(link.to).in.push(link); }` with `for (const link of data.runtime) { at(link.to).out.push(link); at(link.from).in.push(link); }` — killed by: `test_link_index`

**Pinned by:** `tests/scripts/test_architecture_docs_pack.py::test_element_block` asserts the exact `uses`, `used by`, `runtime` and `bound by` lines built from the index, and `test_area_slice` the same lines in a whole slice; both fail if the moved index groups an entry under the wrong element or drops one.

- Satisfies Spec AC: none new (shared lookups for the area documents; the spec's Availability row: no quadratic rescan at the 5,000-element cap)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_docs_facts.py`:

```python


LINKS = {
    "elements": [{"id": e} for e in ("a", "b", "c")],
    "allowed": [{"from": "a", "to": "b", "titles": []}, {"from": "c", "to": "a", "titles": []}],
    "runtime": [{"from": "b", "to": "a", "kind": "http", "titles": ["t"]}, {"from": "ghost", "to": "c", "kind": "event", "titles": []}],
    "decisions": [{"id": "D-1", "binds": ["a", "a", "c"]}, {"id": "D-2", "binds": ["a"]}],
}


def test_link_index() -> None:  # Area and AI pack: each element's entries, grouped once
    code = ("const i = f.linkIndex(data);\n"
            "process.stdout.write(JSON.stringify(Object.fromEntries([...i].map(([id, e]) => [id, {"
            " from: e.from.map((x) => x.to), to: e.to.map((x) => x.from), out: e.out.map((x) => x.to), in: e.in.map((x) => x.from),"
            " boundBy: e.boundBy.map((d) => d.id) }]))));")
    assert run_on(LINKS, code) == {
        "a": {"from": ["b"], "to": ["c"], "out": [], "in": ["b"], "boundBy": ["D-1", "D-2"]},
        "b": {"from": [], "to": ["a"], "out": ["a"], "in": [], "boundBy": []},
        "c": {"from": ["a"], "to": [], "out": [], "in": ["ghost"], "boundBy": ["D-1"]},
    }
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_facts.py`
Expected: FAIL, 1 failed, 14 passed (`f.linkIndex is not a function`).

- [ ] **Step 3: GREEN.**

**Append to** `skills/shared/scripts/architecture-docs/facts.mjs`:

```js

// Each element's allowed, runtime and binding-decision entries, grouped once so a document does not rescan the export:
// `from` and `to` (allowed entries from and to it), `out` and `in` (runtime links from and to it), `boundBy` (decisions
// whose `binds` hold it, in export order).
export function linkIndex(data) {
  const empty = () => ({ from: [], to: [], out: [], in: [], boundBy: [] });
  const index = new Map(data.elements.map((element) => [element.id, empty()]));
  const at = (id) => index.get(id) ?? empty();
  for (const entry of data.allowed) { at(entry.from).from.push(entry); at(entry.to).to.push(entry); }
  for (const link of data.runtime) { at(link.from).out.push(link); at(link.to).in.push(link); }
  for (const decision of data.decisions) for (const id of new Set(decision.binds)) at(id).boundBy.push(decision);
  return index;
}
```

**In** `skills/shared/scripts/architecture-docs/pack-blocks.mjs`, **replace**:

```js
// Each element's allowed, runtime and binding-decision entries, grouped once so a block does not rescan the export.
function linkIndex(data) {
  const index = new Map(data.elements.map((element) => [element.id, { from: [], to: [], out: [], in: [], boundBy: [] }]));
  const at = (id) => index.get(id) ?? { from: [], to: [], out: [], in: [], boundBy: [] };
  for (const entry of data.allowed) { at(entry.from).from.push(entry); at(entry.to).to.push(entry); }
  for (const link of data.runtime) { at(link.from).out.push(link); at(link.to).in.push(link); }
  for (const decision of data.decisions) for (const id of new Set(decision.binds)) at(id).boundBy.push(decision);
  return index;
}

// The same context for another slice: the maps are kept, only the held sets change.
```

**with**:

```js
// The same context for another slice: the maps are kept, only the held sets change.
```

**In** `skills/shared/scripts/architecture-docs/pack-blocks.mjs`, **replace**:

```js
import { areasByElement, areasOf, isCrossCutting, recordElements } from './facts.mjs';
```

**with**:

```js
import { areasByElement, areasOf, isCrossCutting, linkIndex, recordElements } from './facts.mjs';
```

- [ ] **Step 4: run GREEN and the callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_facts.py tests/scripts/test_architecture_docs_pack.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (65 passed).

- [ ] **Step 5: refactor.** Confirm `pack-blocks.mjs` has no `function linkIndex` left: `rg -n "function linkIndex" skills/shared/scripts/architecture-docs` prints only `facts.mjs`.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/facts.mjs skills/shared/scripts/architecture-docs/pack-blocks.mjs tests/scripts/test_architecture_docs_facts.py
git commit -m "refactor(#33): the per-element link index moves into facts.mjs for the area documents to share"
```

---

### Task 3: an area's capabilities, and the pack area slice lists them

**Tier:** standard — a filter and one new pack section, with full code; the section's line is pack text (one-line title, pack-file suffix).

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/facts.mjs` (append `areaCapabilities`)
- Modify: `skills/shared/scripts/architecture-docs/pack.mjs` (the `## Capabilities` section, the layout paragraph)
- Test: `tests/scripts/test_architecture_docs_facts.py`, `tests/scripts/test_architecture_docs_pack.py`

**Callers that move with this task:** sweep rows `test_architecture_docs_pack.py:329`, `:336`, `:338`

**Reviewer looks at:**
1. A capability counted only by its steps' sources — mutation: in `facts.mjs`, replace `capability.steps.some((step) => inArea.has(step.from) || inArea.has(step.to))` with `capability.steps.some((step) => inArea.has(step.from))` — killed by: `test_area_capabilities`
2. Capabilities not sorted by name — mutation: in `facts.mjs`, drop the `.sort` from `areaCapabilities` — killed by: `test_area_slice_lists_its_capabilities`
3. The capability line has no pack file — mutation: in `pack.mjs`, write the capability line as `- <name>: <title>` without `ref` — killed by: `test_area_slice_lists_its_capabilities`
4. The capability title keeps its line feeds — mutation: in `pack.mjs`, write the capability title without `oneLine` — killed by: `test_area_slice_lists_its_capabilities`
5. The Capabilities section written even when empty — mutation: in `pack.mjs`, replace `    ...section('Capabilities', lineBlock(` with `    ...['## Capabilities', ...lineBlock(` — killed by: `test_area_slice_with_no_capability_leaves_the_section_out`
6. The layout paragraph does not name an area slice's capabilities — mutation: in `pack.mjs`, replace `known-gap entries, and the capabilities that pass through it. '` with `known-gap entries. '` — killed by: `test_pack_layout_names_an_area_slice_s_capabilities`

- Satisfies Spec AC: AC-26 (an area slice lists each capability with a step in the area, with its pack file); Pack layout (amendment c081dce)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_docs_facts.py`:

```python


def test_area_capabilities() -> None:  # Area and AI pack: the capabilities with a step whose end is an area element
    data = {"capabilities": [
        {"name": "buy", "steps": [{"from": "shop.web", "to": "shop.api"}]},
        {"name": "pay", "steps": [{"from": "bank", "to": "pay"}]},
        {"name": "refund", "steps": [{"from": "bank", "to": "shop.api"}]},
        {"name": "idle", "steps": []},
    ]}
    names = lambda area: [c["name"] for c in facts("areaCapabilities", data, {"elements": area})]  # noqa: E731
    assert names(["shop.api"]) == ["buy", "refund"]
    assert names(["shop.web"]) == ["buy"]
    assert names(["pay"]) == ["pay"]
    assert names([]) == []
```

**Append to** `tests/scripts/test_architecture_docs_pack.py`:

```python


def test_area_slice_lists_its_capabilities() -> None:  # Pack layout: `## Capabilities`; AC-26 (an area slice's capabilities)
    text = pack("p.areaSlice(data, gap, data.areas[0], base)")
    assert text.endswith("\n\n## Capabilities\n\n- buy: Buy [capabilities/buy.md]\n")
    more = pack("(() => { const more = { ...data, capabilities: [...data.capabilities, { name: 'audit', title: 'Audit\\nlog',"
                " description: null, steps: [{ from: 'bank', to: 'shop', label: null, reply: false, kinds: ['uses'] }] }] };"
                " return p.areaSlice(more, gap, more.areas[0], packContext(more)); })()")
    assert more.endswith("\n\n## Capabilities\n\n- audit: Audit log [capabilities/audit.md]\n- buy: Buy [capabilities/buy.md]\n")


def test_area_slice_with_no_capability_leaves_the_section_out() -> None:  # Pack layout: an empty section is left out
    text = pack("p.areaSlice(data, gap, { name: 'bank', title: 'Bank', description: null, elements: ['bank'] }, base)")
    assert "## Capabilities" not in text


def test_pack_layout_names_an_area_slice_s_capabilities() -> None:  # AI pack: how the pack is laid out
    text = pack("p.packIndex(data, gap, base)")
    assert ("areas/<name>.md holds one area: its elements, decisions, contracts, open questions and known-gap entries, "
            "and the capabilities that pass through it. capabilities/<name>.md holds one capability") in text
```

**In** `tests/scripts/test_architecture_docs_pack.py`, **replace**:

```python
"compatibility: no rule stated\nnotes: n1 # n\ndecisions: D-2, D-3 [README.md]\ncapabilities: buy [capabilities/buy.md]\n"
    )
```

**with**:

```python
"compatibility: no rule stated\nnotes: n1 # n\ndecisions: D-2, D-3 [README.md]\ncapabilities: buy [capabilities/buy.md]\n\n"
        "## Capabilities\n\n- buy: Buy [capabilities/buy.md]\n"
    )
```

**In** `tests/scripts/test_architecture_docs_pack.py`, **replace**:

```python
    assert headings(text) == ["## Elements", "## Decisions", "## Contracts", "## Open questions", "## Known gap"]
```

**with**:

```python
    assert headings(text) == ["## Elements", "## Decisions", "## Contracts", "## Open questions", "## Known gap", "## Capabilities"]
```

**In** `tests/scripts/test_architecture_docs_pack.py`, **replace**:

```python
    assert text.rstrip("\n").split("\n\n")[-1] == (
        "- shop.api -> shop.web
```

**with**:

```python
    assert text.rstrip("\n").split("\n\n")[-3] == (
        "- shop.api -> shop.web
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_facts.py tests/scripts/test_architecture_docs_pack.py`
Expected: FAIL, 5 failed, 60 passed (`areaCapabilities` is missing; the slices have no `## Capabilities` section; the layout paragraph is the old one).

- [ ] **Step 3: GREEN.**

**Append to** `skills/shared/scripts/architecture-docs/facts.mjs`:

```js

// Spec, Area and AI pack: the capabilities with a step whose end is an area element, in name order.
export function areaCapabilities(data, area) {
  const inArea = new Set(area.elements);
  return data.capabilities.filter((capability) => capability.steps.some((step) => inArea.has(step.from) || inArea.has(step.to)))
    .sort((x, y) => cmp(x.name, y.name));
}
```

**In** `skills/shared/scripts/architecture-docs/pack.mjs`, **replace**:

```js
import { areaRecords, capabilityRecords, outsideAreas } from './facts.mjs';
import { packFile, multiLine } from './pack-text.mjs';
```

**with**:

```js
import { areaCapabilities, areaRecords, capabilityRecords, outsideAreas } from './facts.mjs';
import { packFile, multiLine, oneLine } from './pack-text.mjs';
```

**In** `skills/shared/scripts/architecture-docs/pack.mjs`, **replace**:

```js
  gapLine, stepLine,
} from './pack-blocks.mjs';
```

**with**:

```js
  gapLine, stepLine, ref,
} from './pack-blocks.mjs';
```

**In** `skills/shared/scripts/architecture-docs/pack.mjs`, **replace**:

```js
    ...section('Known gap', lineBlock(records.gap.map((entry) => gapLine(entry, ctx)))),
  ]);
}

export function capabilitySlice
```

**with**:

```js
    ...section('Known gap', lineBlock(records.gap.map((entry) => gapLine(entry, ctx)))),
    ...section('Capabilities', lineBlock(areaCapabilities(data, area)
      .map((capability) => `- ${ref('capabilities', capability.name, ctx, `: ${oneLine(capability.title)}`)}`))),
  ]);
}

export function capabilitySlice
```

**In** `skills/shared/scripts/architecture-docs/pack.mjs`, **replace**:

```js
  + 'decisions, contracts, open questions and known-gap entries. capabilities/<name>.md holds one capability: its steps, '
```

**with**:

```js
  + 'decisions, contracts, open questions and known-gap entries, and the capabilities that pass through it. '
  + 'capabilities/<name>.md holds one capability: its steps, '
```

- [ ] **Step 4: run GREEN and the callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_facts.py tests/scripts/test_architecture_docs_pack.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (69 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/facts.mjs skills/shared/scripts/architecture-docs/pack.mjs tests/scripts/test_architecture_docs_facts.py tests/scripts/test_architecture_docs_pack.py
git commit -m "feat(#33): an area's capabilities; the pack area slice lists them with their pack files"
```

---

### Task 4: the flowchart draws a frame and red arrows

**Tier:** standard — complete code; labels stay entity-encoded (trust boundary) and the overview's calls are unchanged.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/mermaid.mjs` (`flowchart` gains `frame` and `red`)
- Test: `tests/scripts/test_architecture_docs_writers.py`

**Callers that move with this task:** sweep row `overview.mjs:34` (no edit: `frame` defaults to `null` and its arrows have no `red`)

**Reviewer looks at:**
1. The wrong arrow is red — mutation: in `mermaid.mjs`, replace `if (arrow.red) red.push(at);` with `if (arrow.red) red.push(at + 1);` — killed by: `test_flowchart_frame_and_red_arrows`
2. Every node drawn inside the frame — mutation: in `mermaid.mjs`, replace `lines.push(...nodes.filter((node) => framed.has(node.id)).map((node) => nodeLine(node, '    ')));` with `lines.push(...nodes.map((node) => nodeLine(node, '    ')));` — killed by: `test_flowchart_frame_and_red_arrows`
3. The frame label not encoded — mutation: in `mermaid.mjs`, replace `subgraph frame["${label(frame.text)}"]` with `subgraph frame["${frame.text}"]` — killed by: `test_flowchart_frame_and_red_arrows`
4. A framed id that is no node is accepted — mutation: in `mermaid.mjs`, delete the line that refuses a framed id that is no node — killed by: `test_flowchart_refuses_a_framed_id_that_is_no_node`
5. A link style line with no red arrow — mutation: in `mermaid.mjs`, replace `if (red.length > 0) lines.push(` with `if (red.length >= 0) lines.push(` — killed by: `test_flowchart_with_no_red_arrow_has_no_link_style`

**Pinned by:** `tests/scripts/test_architecture_docs_writers.py::test_flowchart_nodes_and_arrows` asserts the exact unframed text (`flowchart LR`, then two-space node lines, then arrows); `test_flowchart_arrow_limit` the 80 and 81 cases; `test_architecture_docs_overview.py::test_overview_sections` the overview's diagram. They fail if the unframed path changes.

- Satisfies Spec AC: Drawing rules (framed elements in one frame; known-gap arrows red); AC-19 (the diagram text it rests on)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_docs_writers.py`:

```python


def test_flowchart_frame_and_red_arrows() -> None:  # Drawing rules: framed elements in one frame; known gap in red
    nodes = [{"id": "a", "text": "A"}, {"id": "b", "text": "B (x)"}, {"id": "c", "text": "C"}]
    arrows = [{"from": "a", "to": "b", "dashed": False, "red": True, "text": "known gap"},
              {"from": "a", "to": "c", "dashed": True, "red": False, "text": ""},
              {"from": "c", "to": "b", "dashed": False, "red": True, "text": ""}]
    assert mermaid("flowchart", nodes, arrows, {"text": "Front;end", "ids": ["c", "a"]})["value"] == (
        'flowchart LR\n  subgraph frame["Front#59;end"]\n    n1["A"]\n    n3["C"]\n  end\n  n2["B #40;x#41;"]\n'
        '  n1 -->|"known gap"| n2\n  n1 -.-> n3\n  n3 --> n2\n  linkStyle 0,2 stroke:#d00,color:#d00'
    )


def test_flowchart_with_no_red_arrow_has_no_link_style() -> None:  # Drawing rules: only known-gap arrows are red
    nodes = [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]
    text = mermaid("flowchart", nodes, [{"from": "a", "to": "b", "dashed": False, "red": False, "text": ""}],
                   {"text": "F", "ids": ["a", "b"]})["value"]
    assert text == 'flowchart LR\n  subgraph frame["F"]\n    n1["A"]\n    n2["B"]\n  end\n  n1 --> n2'


def test_flowchart_refuses_a_framed_id_that_is_no_node() -> None:  # fail closed: a frame names only drawn nodes
    result = mermaid("flowchart", [{"id": "a", "text": "A"}], [], {"text": "F", "ids": ["a", "ghost"]})
    assert result["ok"] is False
    assert "ghost" in result["message"]
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_writers.py`
Expected: FAIL, 3 failed, 31 passed (no frame is drawn, no `linkStyle` line, a framed id that is no node is accepted).

- [ ] **Step 3: GREEN.**

**Replace the contents of** `skills/shared/scripts/architecture-docs/mermaid.mjs` **with**:

```js
// Mermaid diagram text. Node ids are generated (n1, n2, ... in the order given); every label is entity-encoded, so model
// text cannot close a quote, end a statement or open a directive. Mermaid decodes `#<code>;` before it parses.
export const ARROW_LIMIT = 80;
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
```

- [ ] **Step 4: run GREEN and the callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_writers.py tests/scripts/test_architecture_docs_overview.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (46 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/mermaid.mjs tests/scripts/test_architecture_docs_writers.py
git commit -m "feat(#33): the flowchart draws framed elements in one frame and known-gap arrows in red"
```

---

### Task 5: the sequence diagram

**Tier:** standard — complete code; participant and message labels are entity-encoded (trust boundary).

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/mermaid.mjs` (`STEP_LIMIT`, `sequence`)
- Test: `tests/scripts/test_architecture_docs_writers.py`

**Callers that move with this task:** none (new export)

**Reviewer looks at:**
1. A reply drawn solid — mutation: in `mermaid.mjs`, replace `${message.reply ? '-->>' : '->>'}` with `${message.reply ? '->>' : '->>'}` — killed by: `test_sequence_diagram`
2. Participant ids in drawing order — mutation: in `mermaid.mjs`, replace `participants.map((participant) => participant.id).sort(cmp).map(` with `participants.map((participant) => participant.id).map(` — killed by: `test_sequence_diagram`
3. The step limit off by one — mutation: in `mermaid.mjs`, replace `if (messages.length > STEP_LIMIT) return null;` with `if (messages.length >= STEP_LIMIT) return null;` — killed by: `test_sequence_step_limit`
4. A message label not encoded — mutation: in `mermaid.mjs`, write the message text without `label` — killed by: `test_sequence_diagram`
5. A participant label not encoded — mutation: in `mermaid.mjs`, write the participant text without `label` — killed by: `test_sequence_diagram`
6. A message to no participant accepted — mutation: in `mermaid.mjs`, never throw for a message end that is no participant — killed by: `test_sequence_refuses_a_message_to_no_participant`

- Satisfies Spec AC: Capability (participants in order of first appearance, calls solid, replies dashed); Shared rules (over 200 steps, a note; amendment c081dce); AC-12 (labels)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_docs_writers.py`:

```python


def test_sequence_diagram() -> None:  # Capability: participants by first appearance, ids in element-id order; replies dashed
    participants = [{"id": "shop.web", "text": "Web"}, {"id": "shop.api", "text": "API; v2"}, {"id": "bank", "text": "Bank"}]
    messages = [{"from": "shop.web", "to": "shop.api", "reply": False, "text": "order: now"},
                {"from": "shop.api", "to": "bank", "reply": False, "text": ""},
                {"from": "shop.api", "to": "shop.web", "reply": True, "text": "%%{init}%%"}]
    assert mermaid("sequence", participants, messages)["value"] == (
        "sequenceDiagram\n  participant n3 as Web\n  participant n2 as API#59; v2\n  participant n1 as Bank\n"
        "  n3->>n2: order#58; now\n  n2->>n1: \n  n2-->>n3: #37;#37;#123;init#125;#37;#37;"
    )


def test_sequence_step_limit() -> None:  # Shared rules: a sequence diagram over 200 steps is replaced by a note
    participants = [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]
    message = {"from": "a", "to": "b", "reply": False, "text": "x"}
    assert mermaid("sequence", participants, [message] * 200)["value"].count("->>") == 200
    assert mermaid("sequence", participants, [message] * 201)["value"] is None


def test_sequence_refuses_a_message_to_no_participant() -> None:  # fail closed: a message names only participants
    for message in ({"from": "a", "to": "ghost", "reply": False, "text": ""}, {"from": "ghost", "to": "a", "reply": True, "text": ""}):
        result = mermaid("sequence", [{"id": "a", "text": "A"}], [message])
        assert result["ok"] is False
        assert "ghost" in result["message"]
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_writers.py`
Expected: FAIL, 3 failed, 34 passed (`m.sequence is not a function`).

- [ ] **Step 3: GREEN.**

**In** `skills/shared/scripts/architecture-docs/mermaid.mjs`, **replace**:

```js
// text cannot close a quote, end a statement or open a directive. Mermaid decodes `#<code>;` before it parses.
export const ARROW_LIMIT = 80;
```

**with**:

```js
// text cannot close a quote, end a statement or open a directive. Mermaid decodes `#<code>;` before it parses.
import { cmp } from '../architecture-delta/report.mjs';

export const ARROW_LIMIT = 80;
export const STEP_LIMIT = 200;
```

**Append to** `skills/shared/scripts/architecture-docs/mermaid.mjs`:

```js

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
```

- [ ] **Step 4: run GREEN and the callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_writers.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (41 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/mermaid.mjs tests/scripts/test_architecture_docs_writers.py
git commit -m "feat(#33): the sequence diagram, with the 200-step limit"
```

---

### Task 6: the drawing rules

**Tier:** standard — complete code; the judgement (which arrows are implied, which ends are neighbours) is pinned by exact-arrow tests.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/facts.mjs` (append `documentBase`)
- Create: `skills/shared/scripts/architecture-docs/area-diagram.mjs`
- Test: `tests/scripts/test_architecture_docs_area.py` (created here)

**Callers that move with this task:** none (new module)

**Reviewer looks at:**
1. An arrow implied by itself — mutation: in `area-diagram.mjs`, replace `if (from !== arrow.from || to !== arrow.to) implied.add(` with `implied.add(` — killed by: `test_area_drawing`
2. Implied only when both ends are strictly inside — mutation: in `area-diagram.mjs`, replace `if (from !== arrow.from || to !== arrow.to) implied.add(` with `if (from !== arrow.from && to !== arrow.to) implied.add(` — killed by: `test_an_arrow_is_implied_only_by_one_strictly_inside`
3. Known-gap arrows hidden like the others — mutation: in `area-diagram.mjs`, replace `const drawn = style === 'gap' ? [...pairs[style].values()] : hideImplied([...pairs[style].values()]);` with `const drawn = hideImplied([...pairs[style].values()]);` — killed by: `test_known_gap_arrows_are_never_hidden_and_hide_nothing`
4. An arrow hidden by one of another style — mutation: in `area-diagram.mjs`, hide implied arrows over all three styles together instead of within each style — killed by: `test_an_import_hides_only_its_own_style`
5. An arrow between two neighbours drawn — mutation: in `area-diagram.mjs`, delete the line in `add` that skips a pair with no framed end — killed by: `test_area_drawing`
6. Runtime kinds and titles not sorted — mutation: in `area-diagram.mjs`, replace `[...[...pair.kinds].sort(cmp), ...[...pair.titles].sort(cmp).map(` with `[...pair.kinds, ...[...pair.titles].map(` — killed by: `test_area_drawing`
7. A neighbour labelled without its area — mutation: in `area-diagram.mjs`, return the bare title for every node (the `if (framed.has(id)) return title;` line becomes `return title;`) — killed by: `test_area_drawing`
8. Known-gap entries outside the area drawn — mutation: in `area-diagram.mjs`, add every known-gap entry as an arrow, whether or not it has a framed end — killed by: `test_area_drawing`
9. An arrow hidden by one the diagram does not draw — mutation: in `area-diagram.mjs`, let `hideImplied` also take an arrow the diagram does not draw (`bank -> pay.gateway` in the test) as an implying arrow — killed by: `test_an_arrow_is_hidden_only_by_a_drawn_one`

- Satisfies Spec AC: AC-19 (neighbour labelled with its area, gap red and labelled, both arrows of a shared pair, runtime dashed with its kind, no implied import, no arrow between neighbours); AC-21 (the arrow limit); Drawing rules (amendment c081dce: neighbour labels, no `click` lines)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Create** `tests/scripts/test_architecture_docs_area.py`:

```python
"""Area and capability documents (spec 2026-11-17-architecture-docs-design.md, "Drawing rules", "Area", "Capability")."""

from __future__ import annotations

import json

from arch_delta_support import DOCS_LIB, lib_url, require_node, run_module

require_node()


def element(id_: str, title: str, **over) -> dict:
    record = {"id": id_, "kind": "container", "tags": [], "code": [], "rules": [], "title": title, "description": None}
    record.update(over)
    return record


# Export-shaped, not a valid model (records skip fields the documents never print). Area `front` frames shop and its
# children; `money` holds pay and its gateway; bank and ledger are in no area.
DATA = {
    "elements": [
        element("bank", "Bank", kind="system"),
        element("ledger", "Ledger", kind="system"),
        element("pay", "Pay", kind="system"),
        element("pay.gateway", "Gateway"),
        element("shop", "Shop", kind="system", description="Sells things.", tags=["edge", "web"], code=["src/shop", "src/lib"],
                rules=["BR-1", "BR-2"]),
        element("shop.api", "API"),
        element("shop.api.orders", "Orders", kind="component"),
        element("shop.web", "Web"),
    ],
    "allowed": [
        {"from": "bank", "to": "pay", "titles": []},
        {"from": "shop.api", "to": "pay", "titles": []},
        {"from": "shop.api.orders", "to": "pay.gateway", "titles": []},
        {"from": "shop.web", "to": "bank", "titles": []},
        {"from": "shop.web", "to": "shop.api", "titles": ["orders"]},
    ],
    "runtime": [
        {"from": "shop", "to": "pay", "kind": "http", "titles": []},
        {"from": "shop.api", "to": "pay.gateway", "kind": "http", "titles": ["charges"]},
        {"from": "shop.web", "to": "bank", "kind": "event", "titles": ["reports"]},
        {"from": "shop.web", "to": "bank", "kind": "http", "titles": ["feeds", "reports"]},
    ],
    "decisions": [],
    "contracts": [],
    "holes": [],
    "changes": [],
    "coverage": None,
    "areas": [
        {"name": "front", "title": "Front", "description": "The shop.", "elements": ["shop", "shop.api", "shop.api.orders", "shop.web"]},
        {"name": "money", "title": "Money", "description": None, "elements": ["pay", "pay.gateway"]},
    ],
    "capabilities": [],
}
GAP = [
    {"from": "bank", "to": "pay", "reason": "between neighbours", "close_by": None},
    {"from": "shop.api", "to": "ledger", "reason": "cycle in current code", "close_by": "2027-01"},
]


def run(code: str, data: dict = DATA, gap: list = GAP) -> object:
    snippet = (
        f"import * as d from {json.dumps(lib_url('area-diagram.mjs', DOCS_LIB))};\n"
        f"import {{ documentBase }} from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\n"
        f"const data = {json.dumps(data)};\nconst gap = {json.dumps(gap)};\nconst base = documentBase(data);\n"
        f"process.stdout.write(JSON.stringify({code}));\n"
    )
    proc = run_module(snippet)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def arrow(from_: str, to: str, style: str, text: str = "") -> dict:
    return {"from": from_, "to": to, "style": style, "dashed": style == "runtime", "red": style == "gap", "text": text}


def test_area_drawing() -> None:  # AC-19; Drawing rules
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, gap, base)")
    assert picture["frame"] == {"text": "Front", "ids": ["shop", "shop.api", "shop.api.orders", "shop.web"]}
    assert picture["nodes"] == [
        {"id": "bank", "text": "Bank (no area)"},
        {"id": "ledger", "text": "Ledger (no area)"},
        {"id": "pay", "text": "Pay (money)"},
        {"id": "pay.gateway", "text": "Gateway (money)"},
        {"id": "shop", "text": "Shop"},
        {"id": "shop.api", "text": "API"},
        {"id": "shop.api.orders", "text": "Orders"},
        {"id": "shop.web", "text": "Web"},
    ]
    assert picture["arrows"] == [
        arrow("shop.api", "ledger", "gap", "known gap"),
        arrow("shop.api", "pay.gateway", "runtime", 'http, "charges"'),
        arrow("shop.api.orders", "pay.gateway", "import"),
        arrow("shop.web", "bank", "import"),
        arrow("shop.web", "bank", "runtime", 'event, http, "feeds", "reports"'),
        arrow("shop.web", "shop.api", "import"),
    ]


def test_area_drawing_of_the_other_area() -> None:  # Drawing rules: neighbours and arrows of an unscoped area
    picture = run("d.drawing(data.areas[1].elements, data.areas[1].title, gap, base)")
    assert [node["text"] for node in picture["nodes"]] == ["Bank (no area)", "Pay", "Gateway", "Shop (front)", "API (front)",
                                                            "Orders (front)"]
    assert picture["arrows"] == [
        arrow("bank", "pay", "import"),
        arrow("bank", "pay", "gap", "known gap"),
        arrow("shop.api", "pay.gateway", "runtime", 'http, "charges"'),
        arrow("shop.api.orders", "pay.gateway", "import"),
    ]


def test_known_gap_arrows_are_never_hidden_and_hide_nothing() -> None:  # Drawing rules: known-gap arrows
    gap = [{"from": "shop", "to": "ledger", "reason": "r", "close_by": None},
           {"from": "shop.api", "to": "ledger", "reason": "r", "close_by": None},
           {"from": "shop.api.orders", "to": "pay.gateway", "reason": "r", "close_by": None}]
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, gap, base)", gap=gap)
    drawn = [(a["from"], a["to"], a["style"]) for a in picture["arrows"]]
    assert ("shop", "ledger", "gap") in drawn and ("shop.api", "ledger", "gap") in drawn
    assert ("shop.api", "pay.gateway", "runtime") in drawn and ("shop.api.orders", "pay.gateway", "gap") in drawn


def test_an_import_hides_only_its_own_style() -> None:  # Drawing rules: within the import or the runtime style
    data = {**DATA, "runtime": [{"from": "shop.api", "to": "pay", "kind": "http", "titles": []}]}
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, [], base)", data=data)
    drawn = [(a["from"], a["to"], a["style"]) for a in picture["arrows"]]
    assert ("shop.api", "pay", "runtime") in drawn and ("shop.api", "pay", "import") not in drawn


def test_an_arrow_is_implied_only_by_one_strictly_inside() -> None:  # Drawing rules: X' at or inside X, Y' at or inside Y
    data = {**DATA, "runtime": [], "allowed": [
        {"from": "shop.web", "to": "pay", "titles": []},
        {"from": "shop.api", "to": "pay.gateway", "titles": []},
        {"from": "shop.api", "to": "pay", "titles": []},
        {"from": "shop", "to": "bank", "titles": []},
        {"from": "shop.web", "to": "pay.gateway", "titles": []},
    ]}
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, [], base)", data=data, gap=[])
    drawn = [(a["from"], a["to"]) for a in picture["arrows"]]
    assert drawn == [("shop", "bank"), ("shop.api", "pay.gateway"), ("shop.web", "pay.gateway")]


def test_area_drawing_with_no_relationships() -> None:  # Drawing rules: framed elements are drawn with no arrows
    data = {**DATA, "allowed": [], "runtime": []}
    picture = run("d.drawing(data.areas[1].elements, data.areas[1].title, [], base)", data=data, gap=[])
    assert picture == {"nodes": [{"id": "pay", "text": "Pay"}, {"id": "pay.gateway", "text": "Gateway"}], "arrows": [],
                       "frame": {"text": "Money", "ids": ["pay", "pay.gateway"]}}


def test_area_drawing_text_and_arrow_limit() -> None:  # AC-21 (the diagram part); Shared rules
    text = run("d.drawingText(d.drawing(data.areas[1].elements, data.areas[1].title, gap, base))")
    assert text.split("\n")[:4] == ["flowchart LR", '  subgraph frame["Money"]', '    n2["Pay"]', '    n3["Gateway"]']
    assert text.endswith("  linkStyle 1 stroke:#d00,color:#d00")
    many = {**DATA, "allowed": [{"from": "pay", "to": f"x{i}", "titles": []} for i in range(81)],
            "elements": DATA["elements"] + [element(f"x{i}", f"X{i}") for i in range(81)], "runtime": []}
    assert run("d.drawingText(d.drawing(data.areas[1].elements, data.areas[1].title, [], base))", data=many) is None
    many["allowed"] = many["allowed"][:80]
    assert run("d.drawingText(d.drawing(data.areas[1].elements, data.areas[1].title, [], base))", data=many).count(" --> ") == 80


def test_an_arrow_is_hidden_only_by_a_drawn_one() -> None:  # Drawing rules: the implying arrow has a framed end
    data = {**DATA, "runtime": [], "allowed": [{"from": "bank", "to": "pay", "titles": []}, {"from": "bank", "to": "pay.gateway", "titles": []}],
            "areas": [{"name": "solo", "title": "Solo", "description": None, "elements": ["pay"]}]}
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, [], base)", data=data, gap=[])
    assert picture["arrows"] == [arrow("bank", "pay", "import")]
    assert [node["id"] for node in picture["nodes"]] == ["bank", "pay"]
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py`
Expected: FAIL, 8 failed (the snippet cannot import `area-diagram.mjs`, and `documentBase` is not exported).

- [ ] **Step 3: GREEN.**

**Append to** `skills/shared/scripts/architecture-docs/facts.mjs`:

```js

// What every area and capability document reads, built once per build: `byElement` (areasByElement), `links`
// (linkIndex), `titles` (titlesOf), `elements` and `decisions` (Maps by id).
export function documentBase(data) {
  return {
    byElement: areasByElement(data),
    links: linkIndex(data),
    titles: titlesOf(data),
    elements: new Map(data.elements.map((element) => [element.id, element])),
    decisions: new Map(data.decisions.map((decision) => [decision.id, decision])),
  };
}
```

**Create** `skills/shared/scripts/architecture-docs/area-diagram.mjs`:

```js
// The drawing rules (spec, What each document holds, Drawing rules): framed elements and their neighbours, import,
// runtime and known-gap arrows, implied arrows hidden. `base` comes from `documentBase`.
import { cmp } from '../architecture-delta/report.mjs';
import { ARROW_LIMIT, flowchart } from './mermaid.mjs';

const STYLES = ['import', 'runtime', 'gap'];

// An element and every element it is inside: `a.b.c`, `a.b`, `a`.
function selfAndAbove(id) {
  const parts = id.split('.');
  return parts.map((_, at) => parts.slice(0, parts.length - at).join('.'));
}

// Within one style, an arrow X -> Y is implied by an arrow X' -> Y' with X' at or inside X, Y' at or inside Y, and the
// two arrows not the same.
function hideImplied(arrows) {
  const implied = new Set();
  for (const arrow of arrows) {
    for (const from of selfAndAbove(arrow.from)) {
      for (const to of selfAndAbove(arrow.to)) {
        if (from !== arrow.from || to !== arrow.to) implied.add(JSON.stringify([from, to]));
      }
    }
  }
  return arrows.filter((arrow) => !implied.has(JSON.stringify([arrow.from, arrow.to])));
}

// The nodes, arrows and frame of a diagram whose framed elements are `framedIds`: { nodes, arrows, frame }.
export function drawing(framedIds, frameText, gap, base) {
  const framed = new Set(framedIds);
  const neighbours = new Set();
  const pairs = Object.fromEntries(STYLES.map((style) => [style, new Map()]));
  const add = (style, from, to, kind = null, titles = []) => {
    if (!framed.has(from) && !framed.has(to)) return;
    for (const end of [from, to]) if (!framed.has(end)) neighbours.add(end);
    const key = JSON.stringify([from, to]);
    if (!pairs[style].has(key)) pairs[style].set(key, { from, to, kinds: new Set(), titles: new Set() });
    const pair = pairs[style].get(key);
    if (kind !== null) pair.kinds.add(kind);
    for (const title of titles) pair.titles.add(title);
  };
  for (const id of framed) {
    const links = base.links.get(id);
    for (const entry of [...links.from, ...links.to]) add('import', entry.from, entry.to);
    for (const link of [...links.out, ...links.in]) add('runtime', link.from, link.to, link.kind, link.titles);
  }
  for (const entry of gap) add('gap', entry.from, entry.to);

  const text = {
    import: () => '',
    runtime: (pair) => [...[...pair.kinds].sort(cmp), ...[...pair.titles].sort(cmp).map((title) => `"${title}"`)].join(', '),
    gap: () => 'known gap',
  };
  const arrows = STYLES.flatMap((style) => {
    const drawn = style === 'gap' ? [...pairs[style].values()] : hideImplied([...pairs[style].values()]);
    return drawn.map((pair) => ({
      from: pair.from, to: pair.to, style, dashed: style === 'runtime', red: style === 'gap', text: text[style](pair),
    }));
  }).sort((x, y) => cmp(x.from, y.from) || cmp(x.to, y.to) || STYLES.indexOf(x.style) - STYLES.indexOf(y.style));

  const nodeText = (id) => {
    const title = base.titles.elements.get(id) ?? id;
    if (framed.has(id)) return title;
    const areas = base.byElement.get(id) ?? [];
    return `${title} (${areas.length > 0 ? areas[0] : 'no area'})`;
  };
  const nodes = [...framed, ...neighbours].sort(cmp).map((id) => ({ id, text: nodeText(id) }));
  return { nodes, arrows, frame: { text: frameText, ids: [...framed].sort(cmp) } };
}

// The diagram text, or null when it has more than ARROW_LIMIT arrows.
export function drawingText(picture) {
  return flowchart(picture.nodes, picture.arrows, picture.frame);
}

export const TOO_MANY_ARROWS = `The diagram has more than ${ARROW_LIMIT} arrows and is not drawn; the tables list everything.`;
```

- [ ] **Step 4: run GREEN and the callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py tests/scripts/test_architecture_docs_facts.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (28 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/facts.mjs skills/shared/scripts/architecture-docs/area-diagram.mjs tests/scripts/test_architecture_docs_area.py
git commit -m "feat(#33): the drawing rules: framed elements, neighbours, import, runtime and known-gap arrows, implied arrows hidden"
```

---

### Task 7: the area document

**Tier:** standard — complete code; a document tree over existing helpers, every section pinned by an exact-tree test.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/area.mjs`
- Test: `tests/scripts/test_architecture_docs_area.py`

**Callers that move with this task:** none (new module)

**Reviewer looks at:**
1. The area document without its area (no Also binds) — mutation: in `area.mjs`, replace `const ctx = { ...base, doc: areaDoc(area.name), area: area.name };` with `const ctx = { ...base, doc: areaDoc(area.name), area: null };` — killed by: `test_area_document_decisions`
2. An element held by another area not linked — mutation: in `area.mjs`, replace `return target === ctx.doc ? [id] : [docLink(id, relative(ctx.doc, target))];` with `return [id];` — killed by: `test_area_document_links_an_element_held_by_another_area`
3. Used by names the element itself — mutation: in `area.mjs`, replace `links.to.map((entry) => entry.from)` with `links.to.map((entry) => entry.to)` — killed by: `test_area_document_dependencies`
4. An incoming runtime link shown as outgoing — mutation: in `area.mjs`, replace `rows.push(row('runtime from', other, detail(link)));` with `rows.push(row('runtime to', other, detail(link)));` — killed by: `test_area_document_runtime_from`
5. An other end in no area shows nothing — mutation: in `area.mjs`, replace `return names.length > 0 ? areaLinks(names, ctx) : ['Not in any area'];` with `return areaLinks(names, ctx);` — killed by: `test_area_document_dependencies`
6. A missing close_by printed as null — mutation: in `area.mjs`, replace `[entry.close_by ?? '']` with `[String(entry.close_by)]` — killed by: `test_area_document_known_gap_with_no_close_by`
7. Every capability listed in every area — mutation: in `area.mjs`, replace `const capabilities = areaCapabilities(data, area);` with `const capabilities = data.capabilities;` — killed by: `test_area_document_contracts_open_questions_gap_and_capabilities`
8. An empty section left blank — mutation: in `area.mjs`, replace `const orSay = (blocks, text) => (blocks.length > 0 ? blocks : [paragraph(text)]);` with `const orSay = (blocks) => blocks;` — killed by: `test_area_document_with_nothing`
9. No note over the arrow limit — mutation: in `area.mjs`, replace `blocks.push(text === null ? paragraph(TOO_MANY_ARROWS) : diagram(text));` with `blocks.push(diagram(String(text)));` — killed by: `test_area_document_over_the_arrow_limit`
10. The description left out — mutation: in `area.mjs`, delete the line that adds the area description — killed by: `test_area_document_layout`
11. Dependencies name only the first area of the other end — mutation: in `area.mjs`, pass only the first of the other end's areas to `areaLinks` — killed by: `test_area_document_dependencies_name_every_area_of_the_other_end`

- Satisfies Spec AC: Area (every section); AC-20 (a cross-cutting decision in both areas with "Also binds"; no principle); AC-21 (the note, the tables complete)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_docs_area.py`:

```python


RECORDS = {
    **DATA,
    "decisions": [
        {"id": "D-0", "decision": "Keep the web thin.", "reason": None, "rejected": [], "binds": ["shop.web"], "capabilities": ["buy"],
         "status": "current", "evidence": "spec", "sources": []},
        {"id": "D-1", "decision": "Log every call.", "reason": "Audit.", "rejected": [], "binds": ["shop.web", "pay"],
         "obligations": ["Log."], "status": "current", "evidence": "spec", "sources": []},
        {"id": "D-2", "decision": "One API.", "reason": "Simple.", "rejected": [], "binds": ["shop.api"], "status": "planned",
         "evidence": "spec", "sources": []},
        {"id": "P-1", "decision": "Data stays in the EU.", "reason": "Law.", "rejected": [], "binds": [], "obligations": ["EU only."],
         "status": "current", "evidence": "spec", "sources": []},
    ],
    "contracts": [{"id": "C-1", "name": "Card API", "owner": "pay", "bound": ["shop.web"], "obligations": ["Ids"],
                   "compatibility": None, "capabilities": ["buy"]}],
    "holes": [{"id": "H-1", "what": "Why one API?", "binds": ["shop.api"], "evidence": "search"}],
    "capabilities": [
        {"name": "audit", "title": "Audit", "description": None, "steps": [
            {"from": "bank", "to": "ledger", "label": None, "reply": False, "kinds": ["uses"]}]},
        {"name": "buy", "title": "Buy", "description": "Buy a thing.", "steps": [
            {"from": "shop.web", "to": "shop.api", "label": "order", "reply": False, "kinds": ["uses"]},
            {"from": "shop.api", "to": "pay.gateway", "label": None, "reply": False, "kinds": ["http", "uses"]},
            {"from": "pay.gateway", "to": "shop.api", "label": "paid", "reply": True, "kinds": ["http"]}]},
    ],
}


def built(module: str, code: str, data: dict = RECORDS, gap: list = GAP) -> dict:
    snippet = (
        f"import * as m from {json.dumps(lib_url(module, DOCS_LIB))};\n"
        f"import {{ documentBase }} from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\n"
        f"const data = {json.dumps(data)};\nconst gap = {json.dumps(gap)};\nconst base = documentBase(data);\n"
        f"process.stdout.write(JSON.stringify({code}));\n"
    )
    proc = run_module(snippet)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def area_doc(index: int = 0, data: dict = RECORDS, gap: list = GAP) -> dict:
    return built("area.mjs", f"m.buildArea(data, gap, data.areas[{index}], base)", data, gap)


def section(document: dict, title: str) -> list:
    """The blocks under the level-2 heading `title`, up to the next level-2 heading."""
    blocks = document["blocks"]
    start = blocks.index({"type": "heading", "level": 2, "text": title}) + 1
    end = next((at for at in range(start, len(blocks)) if blocks[at]["type"] == "heading" and blocks[at]["level"] == 2), len(blocks))
    return blocks[start:end]


def L(text: str, href: str) -> dict:
    return {"type": "link", "text": text, "href": href}


def para(text: str) -> dict:
    return {"type": "paragraph", "parts": [text]}


def heads(document: dict, level: int) -> list:
    return [block["text"] for block in document["blocks"] if block["type"] == "heading" and block["level"] == level]


def test_area_document_layout() -> None:  # Area: title, description, then the sections in order
    document = area_doc()
    assert document["title"] == "Front"
    assert document["blocks"][0] == para("The shop.")
    assert heads(document, 2) == ["Diagram", "Elements", "Dependencies", "Decisions", "Contracts", "Open questions", "Known gap",
                                  "Capabilities"]
    diagram = section(document, "Diagram")
    assert len(diagram) == 1 and diagram[0]["type"] == "diagram"
    assert diagram[0]["text"].startswith('flowchart LR\n  subgraph frame["Front"]\n')
    assert '  n6 -->|"known gap"| n2' in diagram[0]["text"]


def test_area_document_elements() -> None:  # Area: Elements (id, title, description, code, rules, tags)
    rows = section(area_doc(), "Elements")[0]
    assert rows["header"] == ["Element", "Title", "Description", "Code", "Rules", "Tags"]
    assert rows["rows"] == [
        [["shop"], ["Shop"], ["Sells things."], ["src/shop, src/lib"], ["BR-1, BR-2"], ["#edge #web"]],
        [["shop.api"], ["API"], [""], [""], [""], [""]],
        [["shop.api.orders"], ["Orders"], [""], [""], [""], [""]],
        [["shop.web"], ["Web"], [""], [""], [""], [""]],
    ]


def test_area_document_links_an_element_held_by_another_area() -> None:  # Shared rules: an id links to its first area
    data = {**RECORDS, "areas": [{"name": "core", "title": "Core", "description": None, "elements": ["shop.api"]}, *RECORDS["areas"]]}
    rows = section(area_doc(1, data), "Elements")[0]["rows"]
    assert [row[0] for row in rows] == [["shop"], [L("shop.api", "core.md")], ["shop.api.orders"], ["shop.web"]]


def test_area_document_dependencies() -> None:  # Area: Dependencies, each with the other end's areas
    table = section(area_doc(), "Dependencies")[0]
    assert table["header"] == ["Element", "Relation", "Other end", "Kind and titles", "Its areas"]
    money = [L("money", "money.md"), " (Money)"]
    assert table["rows"] == [
        [["shop"], ["runtime to"], [L("pay", "money.md"), " (Pay)"], ["http"], money],
        [["shop.api"], ["uses"], [L("pay", "money.md"), " (Pay)"], [""], money],
        [["shop.api"], ["used by"], [L("shop.web", "front.md"), " (Web)"], [""], [L("front", "front.md"), " (Front)"]],
        [["shop.api"], ["runtime to"], [L("pay.gateway", "money.md"), " (Gateway)"], ['http, "charges"'], money],
        [["shop.api.orders"], ["uses"], [L("pay.gateway", "money.md"), " (Gateway)"], [""], money],
        [["shop.web"], ["uses"], [L("bank", "../README.md"), " (Bank)"], [""], ["Not in any area"]],
        [["shop.web"], ["uses"], [L("shop.api", "front.md"), " (API)"], [""], [L("front", "front.md"), " (Front)"]],
        [["shop.web"], ["runtime to"], [L("bank", "../README.md"), " (Bank)"], ['event, "reports"'], ["Not in any area"]],
        [["shop.web"], ["runtime to"], [L("bank", "../README.md"), " (Bank)"], ['http, "feeds", "reports"'], ["Not in any area"]],
    ]


def test_area_document_runtime_from() -> None:  # Area: an incoming runtime link names its source
    rows = section(area_doc(1), "Dependencies")[0]["rows"]
    assert [row[1][0] for row in rows] == ["used by", "used by", "runtime from", "used by", "runtime from"]
    assert rows[2] == [["pay"], ["runtime from"], [L("shop", "front.md"), " (Shop)"], ["http"], [L("front", "front.md"), " (Front)"]]


def test_area_document_decisions() -> None:  # Area: cross-cutting first, by id; "Also binds"; AC-20
    blocks = section(area_doc(), "Decisions")
    assert [block["text"] for block in blocks if block["type"] == "heading"] == ["D-1", "D-0", "D-2"]
    d1 = blocks[2]["items"]
    assert d1[-1] == ["Also binds: ", L("money", "money.md"), " (Money)"]
    assert ["Reason: ", "Reason not known"] in blocks[5]["items"]
    assert not any(item[0] == "Also binds: " for item in blocks[5]["items"])
    money = section(area_doc(1), "Decisions")
    assert [block["text"] for block in money if block["type"] == "heading"] == ["D-1"]
    assert money[2]["items"][-1] == ["Also binds: ", L("front", "front.md"), " (Front)"]
    assert "P-1" not in json.dumps(area_doc()) and "P-1" not in json.dumps(area_doc(1))


def test_area_document_contracts_open_questions_gap_and_capabilities() -> None:  # Area: the rest, in full
    document = area_doc()
    contracts = section(document, "Contracts")
    assert contracts[0] == {"type": "heading", "level": 3, "text": "C-1: Card API"}
    assert contracts[1]["items"][-1] == ["Also in: ", L("money", "money.md"), " (Money)"]
    holes = section(document, "Open questions")
    assert [holes[0]["text"], holes[1]] == ["H-1", para("Why one API?")]
    gap = section(document, "Known gap")[0]
    assert gap["header"] == ["From", "To", "Reason", "Close by"]
    assert gap["rows"] == [[[L("shop.api", "front.md"), " (API)"], [L("ledger", "../README.md"), " (Ledger)"],
                            ["cycle in current code"], ["2027-01"]]]
    capabilities = section(document, "Capabilities")[0]
    assert capabilities["header"] == ["Capability", "Description"]
    assert capabilities["rows"] == [[[L("buy", "../capabilities/buy.md"), " (Buy)"], ["Buy a thing."]]]


def test_area_document_known_gap_with_no_close_by() -> None:  # Area: `close_by` is optional
    rows = section(area_doc(1), "Known gap")[0]["rows"]
    assert rows == [[[L("bank", "../README.md"), " (Bank)"], [L("pay", "money.md"), " (Pay)"], ["between neighbours"], [""]]]


def test_area_document_with_nothing() -> None:  # Area: an empty section says so; no description, no paragraph
    data = {**RECORDS, "areas": [{"name": "side", "title": "Side", "description": None, "elements": []}]}
    document = area_doc(0, data)
    assert document["blocks"][0] == {"type": "heading", "level": 2, "text": "Diagram"}
    assert section(document, "Elements") == [para("The area has no elements.")]
    assert section(document, "Dependencies") == [para("No dependencies.")]
    assert section(document, "Decisions") == [para("No decisions bind an element of this area.")]
    assert section(document, "Contracts") == [para("No contracts.")]
    assert section(document, "Open questions") == [para("No open questions.")]
    assert section(document, "Known gap") == [para("No known-gap entries.")]
    assert section(document, "Capabilities") == [para("No capabilities pass through this area.")]


def test_area_document_over_the_arrow_limit() -> None:  # AC-21: the note, and the tables complete
    data = {**RECORDS, "allowed": [{"from": "pay", "to": f"x{i:02}", "titles": []} for i in range(81)], "runtime": [],
            "elements": RECORDS["elements"] + [element(f"x{i:02}", f"X{i}") for i in range(81)]}
    document = area_doc(1, data, [])
    assert section(document, "Diagram") == [para("The diagram has more than 80 arrows and is not drawn; the tables list everything.")]
    assert len(section(document, "Dependencies")[0]["rows"]) == 81


def test_area_document_dependencies_name_every_area_of_the_other_end() -> None:  # Area: "the other end's areas"
    data = {**RECORDS, "areas": [{"name": "core", "title": "Core", "description": None, "elements": ["pay.gateway"]}, *RECORDS["areas"]]}
    rows = section(area_doc(1, data), "Dependencies")[0]["rows"]
    assert [["shop.api.orders"], ["uses"], [L("pay.gateway", "core.md"), " (Gateway)"], [""],
            [L("core", "core.md"), " (Core)", ", ", L("money", "money.md"), " (Money)"]] in rows
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py`
Expected: FAIL, 11 failed, 8 passed (the snippet cannot import `area.mjs`).

- [ ] **Step 3: GREEN.**

**Create** `skills/shared/scripts/architecture-docs/area.mjs`:

```js
// An area document (spec, What each document holds, Area): title and description, the diagram, the elements, their
// dependencies, and the area's decisions, contracts, open questions, known-gap entries and capabilities.
import { cmp } from '../architecture-delta/report.mjs';
import { doc, heading, paragraph, table, diagram, docLink } from './tree.mjs';
import { areaDoc, areaCapabilities, areaRecords, elementTarget, relative } from './facts.mjs';
import { decisionBlocks, contractBlocks, holeBlocks, elementLinks, areaLinks, capabilityLinks } from './records-doc.mjs';
import { drawing, drawingText, TOO_MANY_ARROWS } from './area-diagram.mjs';

// An id is plain text in the document that holds it, a link elsewhere.
function idCell(id, ctx) {
  const target = elementTarget(id, ctx.byElement);
  return target === ctx.doc ? [id] : [docLink(id, relative(ctx.doc, target))];
}

const otherAreas = (id, ctx) => {
  const names = ctx.byElement.get(id) ?? [];
  return names.length > 0 ? areaLinks(names, ctx) : ['Not in any area'];
};

// Spec, Area, Dependencies: what each area element may use and what may use it, and its runtime links, each with the
// other end's areas. Rows: uses, used by, runtime to, runtime from, each sorted by the other end (runtime by kind next).
function dependencyRows(area, ctx) {
  const rows = [];
  for (const id of area.elements) {
    const links = ctx.links.get(id);
    const row = (relation, other, detail) => [[id], [relation], elementLinks([other], ctx), [detail], otherAreas(other, ctx)];
    for (const other of [...new Set(links.from.map((entry) => entry.to))].sort(cmp)) rows.push(row('uses', other, ''));
    for (const other of [...new Set(links.to.map((entry) => entry.from))].sort(cmp)) rows.push(row('used by', other, ''));
    const detail = (link) => [link.kind, ...link.titles.map((title) => `"${title}"`)].join(', ');
    const byOther = (x, y) => cmp(x.other, y.other) || cmp(x.link.kind, y.link.kind);
    const outgoing = links.out.map((link) => ({ other: link.to, link })).sort(byOther);
    const incoming = links.in.map((link) => ({ other: link.from, link })).sort(byOther);
    for (const { other, link } of outgoing) rows.push(row('runtime to', other, detail(link)));
    for (const { other, link } of incoming) rows.push(row('runtime from', other, detail(link)));
  }
  return rows;
}

const orSay = (blocks, text) => (blocks.length > 0 ? blocks : [paragraph(text)]);

export function buildArea(data, gap, area, base) {
  const ctx = { ...base, doc: areaDoc(area.name), area: area.name };
  const records = areaRecords(data, gap, area);
  const blocks = [];
  if (area.description !== null) blocks.push(paragraph(area.description));

  blocks.push(heading(2, 'Diagram'));
  const text = drawingText(drawing(area.elements, area.title, gap, base));
  blocks.push(text === null ? paragraph(TOO_MANY_ARROWS) : diagram(text));

  blocks.push(heading(2, 'Elements'));
  blocks.push(...orSay(area.elements.length === 0 ? [] : [table(['Element', 'Title', 'Description', 'Code', 'Rules', 'Tags'],
    area.elements.map((id) => {
      const element = ctx.elements.get(id);
      return [idCell(id, ctx), [element.title], [element.description ?? ''], [element.code.join(', ')],
        [element.rules.join(', ')], [element.tags.map((tag) => `#${tag}`).join(' ')]];
    }))], 'The area has no elements.'));

  blocks.push(heading(2, 'Dependencies'));
  const rows = dependencyRows(area, ctx);
  blocks.push(...orSay(rows.length === 0 ? [] : [table(['Element', 'Relation', 'Other end', 'Kind and titles', 'Its areas'], rows)],
    'No dependencies.'));

  blocks.push(heading(2, 'Decisions'));
  blocks.push(...orSay(records.decisions.flatMap((record) => decisionBlocks(record, ctx)), 'No decisions bind an element of this area.'));
  blocks.push(heading(2, 'Contracts'));
  blocks.push(...orSay(records.contracts.flatMap((record) => contractBlocks(record, ctx)), 'No contracts.'));
  blocks.push(heading(2, 'Open questions'));
  blocks.push(...orSay(records.holes.flatMap((record) => holeBlocks(record, ctx)), 'No open questions.'));

  blocks.push(heading(2, 'Known gap'));
  blocks.push(...orSay(records.gap.length === 0 ? [] : [table(['From', 'To', 'Reason', 'Close by'], records.gap.map((entry) => [
    elementLinks([entry.from], ctx), elementLinks([entry.to], ctx), [entry.reason], [entry.close_by ?? '']]))],
  'No known-gap entries.'));

  blocks.push(heading(2, 'Capabilities'));
  const capabilities = areaCapabilities(data, area);
  blocks.push(...orSay(capabilities.length === 0 ? [] : [table(['Capability', 'Description'], capabilities.map((capability) => [
    capabilityLinks([capability.name], ctx), [capability.description ?? '']]))], 'No capabilities pass through this area.'));
  return doc(area.title, blocks);
}
```

- [ ] **Step 4: run GREEN and the callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (23 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/area.mjs tests/scripts/test_architecture_docs_area.py
git commit -m "feat(#33): the area document: diagram, elements, dependencies, decisions, contracts, open questions, known gap, capabilities"
```

---

### Task 8: the capability document

**Tier:** standard — complete code; a document tree over existing helpers, pinned by exact-tree tests.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/capability.mjs`
- Test: `tests/scripts/test_architecture_docs_area.py`

**Callers that move with this task:** none (new module)

**Reviewer looks at:**
1. Participants in id order — mutation: in `capability.mjs`, replace `const participants = [...seen].map(` with `const participants = [...seen].sort().map(` — killed by: `test_capability_document`
2. Call and reply swapped in the table — mutation: in `capability.mjs`, replace `[step.reply ? 'reply' : 'call']` with `[step.reply ? 'call' : 'reply']` — killed by: `test_capability_document`
3. Steps numbered from 0 — mutation: in `capability.mjs`, replace `[String(at + 1)]` with `[String(at)]` — killed by: `test_capability_document`
4. An end in no area not named — mutation: in `capability.mjs`, delete the line that adds `Not in any area` — killed by: `test_capability_document_outside_any_area`
5. The capability document treated as an area document — mutation: in `capability.mjs`, replace `const ctx = { ...base, doc: capabilityDoc(capability.name), area: null };` with `const ctx = { ...base, doc: capabilityDoc(capability.name), area: '' };` — killed by: `test_capability_document_records_and_areas`
6. A capability with no steps drawn as an empty diagram — mutation: in `capability.mjs`, replace `if (capability.steps.length === 0) blocks.push(` with `if (false) blocks.push(` — killed by: `test_capability_document_with_no_steps`
7. No note over the step limit — mutation: in `capability.mjs`, replace `blocks.push(text === null ? paragraph(TOO_MANY_STEPS) : diagram(text));` with `blocks.push(diagram(String(text)));` — killed by: `test_capability_document_step_limit`

- Satisfies Spec AC: Capability (every section); AC-18 (steps link each end to its first area); AC-21 (200 steps drawn, 201 a note, the table complete)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_docs_area.py`:

```python


def capability_doc(index: int = 1, data: dict = RECORDS) -> dict:
    return built("capability.mjs", f"m.buildCapability(data, data.capabilities[{index}], base)", data, [])


def test_capability_document() -> None:  # Capability: title, description, sequence, steps, records, areas; AC-18
    document = capability_doc()
    assert document["title"] == "Buy"
    assert document["blocks"][0] == para("Buy a thing.")
    assert heads(document, 2) == ["Sequence", "Steps", "Decisions", "Contracts", "Areas involved"]
    assert section(document, "Sequence") == [{"type": "diagram", "text": (
        "sequenceDiagram\n  participant n3 as Web\n  participant n2 as API\n  participant n1 as Gateway\n"
        "  n3->>n2: order\n  n2->>n1: \n  n1-->>n2: paid")}]
    table = section(document, "Steps")[0]
    assert table["header"] == ["Step", "From", "To", "Label", "Call or reply", "Kinds"]
    web, api, gateway = ([L(id_, f"../areas/{area}.md"), f" ({title})"] for id_, area, title in
                         (("shop.web", "front", "Web"), ("shop.api", "front", "API"), ("pay.gateway", "money", "Gateway")))
    assert table["rows"] == [
        [["1"], web, api, ["order"], ["call"], ["uses"]],
        [["2"], api, gateway, [""], ["call"], ["http, uses"]],
        [["3"], gateway, api, ["paid"], ["reply"], ["http"]],
    ]


def test_capability_document_records_and_areas() -> None:  # Capability: the records naming it; the areas involved
    document = capability_doc()
    decisions = section(document, "Decisions")
    assert [block["text"] for block in decisions if block["type"] == "heading"] == ["D-0"]
    assert decisions[2]["items"][-1] == ["Areas: ", L("front", "../areas/front.md"), " (Front)"]
    contracts = section(document, "Contracts")
    assert contracts[0]["text"] == "C-1: Card API"
    assert section(document, "Areas involved") == [{"type": "list", "items": [
        [L("front", "../areas/front.md"), " (Front)"], [L("money", "../areas/money.md"), " (Money)"]]}]


def test_capability_document_outside_any_area() -> None:  # Capability: "Not in any area"; empty sections say so
    document = capability_doc(0)
    assert document["blocks"][0] == {"type": "heading", "level": 2, "text": "Sequence"}
    assert section(document, "Decisions") == [para("No decisions name this capability.")]
    assert section(document, "Contracts") == [para("No contracts name this capability.")]
    assert section(document, "Areas involved") == [{"type": "list", "items": [["Not in any area"]]}]
    assert section(document, "Steps")[0]["rows"][0][1] == [L("bank", "../README.md"), " (Bank)"]


def test_capability_document_with_an_end_in_no_area_and_one_in_an_area() -> None:  # Capability: both kinds of end
    data = {**RECORDS, "capabilities": [{"name": "feed", "title": "Feed", "description": None, "steps": [
        {"from": "bank", "to": "pay", "label": "settle", "reply": False, "kinds": ["uses"]}]}]}
    assert section(capability_doc(0, data), "Areas involved") == [{"type": "list", "items": [
        [L("money", "../areas/money.md"), " (Money)"], ["Not in any area"]]}]


def test_capability_document_with_no_steps() -> None:  # Capability: a capability with no steps
    data = {**RECORDS, "capabilities": [{"name": "idle", "title": "Idle", "description": None, "steps": []}]}
    document = capability_doc(0, data)
    assert section(document, "Sequence") == [para("The capability has no steps.")]
    assert section(document, "Steps") == [para("No steps.")]
    assert section(document, "Areas involved") == [para("No areas.")]


def test_capability_document_step_limit() -> None:  # AC-21 (capability part): 200 steps drawn, 201 replaced by the note
    step = {"from": "shop.web", "to": "shop.api", "label": "x", "reply": False, "kinds": ["uses"]}
    for count, drawn in ((200, True), (201, False)):
        data = {**RECORDS, "capabilities": [{"name": "loop", "title": "Loop", "description": None, "steps": [step] * count}]}
        document = capability_doc(0, data)
        sequence = section(document, "Sequence")
        if drawn:
            assert sequence[0]["type"] == "diagram" and sequence[0]["text"].count("->>") == 200
        else:
            assert sequence == [para("The capability has more than 200 steps, so its sequence diagram is not drawn; "
                                     "the steps table lists every step.")]
        assert len(section(document, "Steps")[0]["rows"]) == count
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py`
Expected: FAIL, 6 failed, 19 passed (the snippet cannot import `capability.mjs`).

- [ ] **Step 3: GREEN.**

**Create** `skills/shared/scripts/architecture-docs/capability.mjs`:

```js
// A capability document (spec, What each document holds, Capability): title and description, the sequence diagram,
// the steps, the decisions and contracts that name the capability, and the areas involved.
import { doc, heading, paragraph, list, table, diagram } from './tree.mjs';
import { STEP_LIMIT, sequence } from './mermaid.mjs';
import { areasOf, capabilityDoc, capabilityRecords } from './facts.mjs';
import { decisionBlocks, contractBlocks, elementLinks, areaLinks } from './records-doc.mjs';

export const TOO_MANY_STEPS = `The capability has more than ${STEP_LIMIT} steps, so its sequence diagram is not drawn; the steps table lists every step.`;

// Spec, Capability: participants in order of first appearance, labelled with their titles.
function sequenceText(capability, ctx) {
  const seen = new Set(capability.steps.flatMap((step) => [step.from, step.to]));
  const participants = [...seen].map((id) => ({ id, text: ctx.titles.elements.get(id) ?? id }));
  return sequence(participants, capability.steps.map((step) => ({ from: step.from, to: step.to, reply: step.reply, text: step.label ?? '' })));
}

const orSay = (blocks, text) => (blocks.length > 0 ? blocks : [paragraph(text)]);

export function buildCapability(data, capability, base) {
  const ctx = { ...base, doc: capabilityDoc(capability.name), area: null };
  const records = capabilityRecords(data, capability);
  const blocks = [];
  if (capability.description !== null) blocks.push(paragraph(capability.description));

  blocks.push(heading(2, 'Sequence'));
  if (capability.steps.length === 0) blocks.push(paragraph('The capability has no steps.'));
  else {
    const text = sequenceText(capability, ctx);
    blocks.push(text === null ? paragraph(TOO_MANY_STEPS) : diagram(text));
  }

  blocks.push(heading(2, 'Steps'));
  blocks.push(...orSay(capability.steps.length === 0 ? [] : [table(['Step', 'From', 'To', 'Label', 'Call or reply', 'Kinds'],
    capability.steps.map((step, at) => [[String(at + 1)], elementLinks([step.from], ctx), elementLinks([step.to], ctx),
      [step.label ?? ''], [step.reply ? 'reply' : 'call'], [step.kinds.join(', ')]]))], 'No steps.'));

  blocks.push(heading(2, 'Decisions'));
  blocks.push(...orSay(records.decisions.flatMap((record) => decisionBlocks(record, ctx)), 'No decisions name this capability.'));
  blocks.push(heading(2, 'Contracts'));
  blocks.push(...orSay(records.contracts.flatMap((record) => contractBlocks(record, ctx)), 'No contracts name this capability.'));

  // Spec, Capability: the areas of every step's ends, and "Not in any area" for an end in none.
  blocks.push(heading(2, 'Areas involved'));
  const names = areasOf(records.elements, ctx.byElement);
  const items = names.map((name) => areaLinks([name], ctx));
  if (records.elements.some((id) => (ctx.byElement.get(id) ?? []).length === 0)) items.push(['Not in any area']);
  blocks.push(items.length === 0 ? paragraph('No areas.') : list(items));
  return doc(capability.title, blocks);
}
```

- [ ] **Step 4: run GREEN and the callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (29 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/capability.mjs tests/scripts/test_architecture_docs_area.py
git commit -m "feat(#33): the capability document: sequence diagram, steps, records naming it, areas involved"
```

---

### Task 9: `build` and `check` write and compare the area and capability documents

**Tier:** standard — complete code; the end-to-end tests carry AC-9, AC-12, AC-13 and AC-18 to AC-21 through the real entry points.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/build.mjs`
- Test: `tests/scripts/test_architecture_docs_documents.py` (created here)

**Callers that move with this task:** sweep row `architecture-docs.mjs:67` (no edit); `build.mjs:29-31` (the overview's two files, now through `addDocument`)

**Reviewer looks at:**
1. ReadGap skips cleanGap — mutation: in `architecture-docs.mjs`, replace `  return cleanGap(entries);` with `  return entries;` — killed by: `test_build_escapes_hostile_text`
2. CleanGap leaves close_by uncleaned — mutation: in `build.mjs`, replace `close_by: entry.close_by === null ? null : cleanText(entry.close_by),` with `close_by: entry.close_by,` — killed by: `test_build_escapes_hostile_text`
3. No deadline check after an area document — mutation: in `build.mjs`, delete the `tick()` after each area document — killed by: `test_build_checks_the_deadline_after_each_area_and_capability_document`
4. No deadline check after a capability document — mutation: in `build.mjs`, delete the `tick()` after each capability document — killed by: `test_build_checks_the_deadline_after_each_area_and_capability_document`
5. No HTML page for a document — mutation: in `build.mjs`, write the HTML page only for `README.md` — killed by: `test_build_writes_area_and_capability_documents`
6. The capability documents not built — mutation: in `build.mjs`, loop over no capabilities — killed by: `test_build_writes_area_and_capability_documents`
7. A pack element title keeps U+2029 — mutation: in `pack-blocks.mjs`, write the element block title with only `\n` replaced, instead of `oneLine` — killed by: `test_build_pack_guards_fences_and_line_separators`
8. Pack decision text not split at U+2028 — mutation: in `pack-blocks.mjs`, split the decision text on `\n` only, keeping the guard, instead of `multiLine` — killed by: `test_build_pack_guards_fences_and_line_separators`

**Pinned by:** `tests/scripts/test_architecture_docs_overview.py::test_overview_page_matches_and_is_marked` reads `index.html` and asserts its marker line and its link `<a href="areas/front.html">front</a> (Shop)`; it fails if `addDocument` writes the overview page under another name or from another tree.

- Satisfies Spec AC: AC-9 (the area case), AC-12 and AC-13 (area and capability parts), AC-17 (the `capabilities` folder), AC-18, AC-19, AC-20, AC-21; the amended AC-25 and AC-26 through `build`; the `--timeout` deadline after each document (Threat model, Availability); plan 2b's carried mutants (`readGap` skipping `cleanGap`)
- Decisions applied: none (the 2026-11-21 amendment, commit `c081dce`, is spec text)
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Create** `tests/scripts/test_architecture_docs_documents.py`:

````python
"""`build` and `check` with area and capability documents (spec 2026-11-17-architecture-docs-design.md, "Area",
"Capability", AC-9, AC-12, AC-13, AC-18 to AC-21)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from arch_delta_support import DOCS_SCRIPT, make_repo, require_node, run_tool

require_node()

MARKER = "<!-- Generated by architecture-docs from the architecture model. Do not edit. -->"
ESC = chr(27)

MODEL = """specification {
  relationship http
  relationship event
}
model {
  shop = system 'Shop' {
    description 'Sells [x](javascript:alert(1)) <script> | ``` things'
    web = container 'Web'
    api = container 'API' {
      orders = component 'Orders'
    }
  }
  pay = system 'Pay' {
    gateway = container 'Gateway'
  }
  bank = system 'Bank'
  ledger = system 'Ledger; "x" %%{init}%%'
  shop.web -> shop.api 'orders'
  shop.api.orders -> pay.gateway
  shop.api -> pay
  shop.api -[http]-> pay.gateway 'charges'
  shop.web -> bank
  shop.web -[event]-> bank 'reports'
  bank -> pay 'settles'
}
views {
  view area-front of shop {
    title 'Front'
    include *
  }
  view area-money {
    title 'Money'
    include pay.gateway
  }
  view area-core {
    title 'Core'
    include shop.api.orders, pay.gateway
  }
  dynamic view capability-buy {
    title 'Buy'
    shop.web -> shop.api 'order; %%{init}%% now'
    shop.api -> pay.gateway
    pay.gateway -> shop.api 'paid'
  }
}
"""


def decision(id_: str, **over) -> dict:
    record = {"id": id_, "decision": "Decide " + id_ + ".", "reason": "Because.", "rejected": [], "binds": [], "status": "current",
              "evidence": "spec", "sources": ["docs/x.md"]}
    record.update(over)
    return record


DECISIONS = {"title": "Core", "holes": [{"id": "H-1", "what": "Why?", "binds": ["shop.api"], "evidence": "search"}], "decisions": [
    decision("D-1", decision="Log <script>alert(1)</script> | [x](javascript:alert(1))\nevery call.", binds=["shop.web", "pay.gateway"],
             obligations=["Log."], note="Red " + ESC + "[31mnote"),
    decision("D-2", binds=["shop.web"], capabilities=["buy"]),
    decision("P-1", obligations=["EU only."]),
]}
CONTRACTS = {"title": "Edge", "contracts": [{"id": "C-1", "name": "Card API", "owner": "pay.gateway", "bound": ["shop.web"],
                                             "obligations": ["Ids"], "compatibility": None, "capabilities": ["buy"]}]}
GAP = {"entries": [{"from": "shop.api", "to": "ledger", "reason": "Red " + ESC + "[31mgap | <b>", "close_by": "2027 " + ESC + "[0m01"},
                   {"from": "shop.web", "to": "pay.gateway", "reason": "no relationship"}]}
LEDGER = "Ledger#59; #34;x#34; #37;#37;#123;init#125;#37;#37; #40;no area#41;"


def write_json(folder: Path, rel: str, data: object) -> None:
    target = folder / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data), encoding="utf-8")


def built(tmp_path: Path, model: str = MODEL, records: bool = True) -> tuple[Path, Path]:
    repo = make_repo(tmp_path, model)
    folder = repo / "docs" / "architecture"
    if records:
        write_json(folder, "decisions/core.json", DECISIONS)
        write_json(folder, "contracts/edge.json", CONTRACTS)
        write_json(folder, "known-gap.json", GAP)
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    return repo, folder / "generated"


def files(out: Path, pattern: str = "*") -> list:
    return sorted(p.relative_to(out).as_posix() for p in out.rglob(pattern) if p.is_file())


def diagram_arrows(text: str) -> list:
    """The first Mermaid flowchart's arrows as (from label, arrow, label, to label); a red arrow is marked `red`."""
    block = re.search(r"```mermaid\nflowchart LR\n(.*?)\n```", text, re.S).group(1).split("\n")
    names = dict(re.findall(r'^\s+(n\d+)\["(.*)"\]$', "\n".join(block), re.M))
    red = set()
    for line in block:
        if line.startswith("  linkStyle "):
            red = {int(at) for at in line.split()[1].split(",")}
    arrows = []
    for line in block:
        found = re.match(r'^  (n\d+) (-->|-\.->)(?:\|"(.*)"\|)? (n\d+)$', line)
        if found:
            arrows.append((names[found.group(1)], found.group(2), found.group(3) or "", names[found.group(4)]))
    return [(*arrow, "red") if at in red else arrow for at, arrow in enumerate(arrows)]


def test_build_writes_area_and_capability_documents(tmp_path) -> None:  # AC-18, AC-13
    _, out = built(tmp_path)
    names = files(out)
    for name in ("areas/core.md", "areas/core.html", "areas/front.md", "areas/front.html", "areas/money.md", "areas/money.html",
                 "capabilities/buy.md", "capabilities/buy.html"):
        assert name in names
    overview = (out / "README.md").read_text(encoding="utf-8")
    for link in ("[core](areas/core.md)", "[front](areas/front.md)", "[money](areas/money.md)", "[buy](capabilities/buy.md)"):
        assert link in overview
    core = (out / "areas" / "core.md").read_text(encoding="utf-8")
    money = (out / "areas" / "money.md").read_text(encoding="utf-8")
    front = (out / "areas" / "front.md").read_text(encoding="utf-8")
    assert "| pay\\.gateway | Gateway |" in core and "| [pay\\.gateway](core.md) | Gateway |" in money
    assert "| shop\\.api\\.orders | Orders |" in core and "| [shop\\.api\\.orders](core.md) | Orders |" in front
    buy = (out / "capabilities" / "buy.md").read_text(encoding="utf-8")
    assert ("| 1 | [shop\\.web](../areas/front.md) \\(Web\\) | [shop\\.api](../areas/front.md) \\(API\\) |" in buy)
    assert "| 2 | [shop\\.api](../areas/front.md) \\(API\\) | [pay\\.gateway](../areas/core.md) \\(Gateway\\) |" in buy
    assert "| 3 | [pay\\.gateway](../areas/core.md) \\(Gateway\\) | [shop\\.api](../areas/front.md) \\(API\\) | paid | reply |" in buy
    for name in names:
        if name.endswith((".md", ".html")):
            assert (out / name).read_text(encoding="utf-8").startswith(MARKER + "\n"), name
    for name in ("areas/front.html", "capabilities/buy.html"):
        page = (out / name).read_text(encoding="utf-8")
        assert page.count("<script") == 2 and "content=\"default-src 'none'; script-src https://cdn.jsdelivr.net/npm/mermaid@12.2.0" in page
    page = (out / "areas" / "front.html").read_text(encoding="utf-8")
    assert '<a href="../index.html">bank</a>' in page and '<a href="../capabilities/buy.html">buy</a>' in page
    slice_ = (out / "pack" / "areas" / "front.md").read_text(encoding="utf-8")
    assert slice_.endswith("\n\n## Capabilities\n\n- buy: Buy [capabilities/buy.md]\n")  # AC-26 (an area slice's capabilities)


def test_build_area_diagram(tmp_path) -> None:  # AC-19
    _, out = built(tmp_path)
    arrows = diagram_arrows((out / "areas" / "front.md").read_text(encoding="utf-8"))
    assert ("API", "-->", "known gap", LEDGER, "red") in arrows
    assert ("Web", "-->", "known gap", "Gateway #40;core#41;", "red") in arrows
    assert ("Web", "-->", "", "Bank #40;no area#41;") in arrows
    assert ("Web", "-.->", "event#44; #34;reports#34;", "Bank #40;no area#41;") in arrows
    assert ("API", "-.->", "http#44; #34;charges#34;", "Gateway #40;core#41;") in arrows
    assert ("Orders", "-->", "", "Gateway #40;core#41;") in arrows
    assert not any(arrow[0] == "API" and arrow[3] == "Pay #40;no area#41;" for arrow in arrows)
    assert not any(arrow[0] == "Bank #40;no area#41;" for arrow in arrows)
    assert len(arrows) == 7


def test_build_cross_cutting_decision_and_principle(tmp_path) -> None:  # AC-20
    _, out = built(tmp_path)
    front = (out / "areas" / "front.md").read_text(encoding="utf-8")
    money = (out / "areas" / "money.md").read_text(encoding="utf-8")
    assert "### D\\-1\n" in front and "- Also binds: [core](core.md) \\(Core\\), [money](money.md) \\(Money\\)" in front
    assert "### D\\-1\n" in money and "- Also binds: [core](core.md) \\(Core\\), [front](front.md) \\(Front\\)" in money
    assert front.index("### D\\-1\n") < front.index("### D\\-2\n")
    holding = [name for name in files(out, "*.md") if not name.startswith("pack/") and "### P\\-1\n" in (out / name).read_text(encoding="utf-8")]
    assert holding == ["README.md"]


def test_build_escapes_hostile_text(tmp_path) -> None:  # AC-12 (area and capability documents); the known gap is cleaned
    _, out = built(tmp_path)
    for name in files(out):
        assert ESC not in (out / name).read_text(encoding="utf-8"), name
    front = (out / "areas" / "front.md").read_text(encoding="utf-8")
    assert "| Red gap \\| &lt;b&gt; | 2027 01 |" in front
    assert "Sells \\[x\\]\\(javascript:alert\\(1\\)\\) &lt;script&gt; \\| \\`\\`\\` things" in front
    assert "Log &lt;script&gt;alert\\(1\\)&lt;/script&gt; \\| \\[x\\]\\(javascript:alert\\(1\\)\\)\\\nevery call\\." in front
    for name in files(out, "*.md"):
        text = (out / name).read_text(encoding="utf-8")
        for block in re.findall(r"```mermaid\n(.*?)\n```", text, re.S):
            assert "%%" not in block and '""' not in block
            labels = re.findall(r'\["(.*?)"\]|\|"(.*?)"\||: (.*)$| as (.*)$', block, re.M)
            for label in ("".join(parts) for parts in labels):
                assert ";" not in re.sub(r"#\d+;", "", label) and '"' not in label, (name, label)
    buy = (out / "capabilities" / "buy.md").read_text(encoding="utf-8")
    assert "  n3->>n2: order#59; #37;#37;#123;init#125;#37;#37; now\n" in buy
    page = (out / "areas" / "front.html").read_text(encoding="utf-8")
    assert "<b>" not in page and "&lt;b&gt;" in page
    assert page.count("<script") == 2


def test_build_pack_guards_fences_and_line_separators(tmp_path) -> None:  # AC-25 (amended), through `build`
    model = MODEL.replace("  bank = system 'Bank'\n", "  bank = system 'Bank\nfeed" + chr(0x2029) + "line'\n")
    repo = make_repo(tmp_path, model)
    folder = repo / "docs" / "architecture"
    write_json(folder, "decisions/core.json", {"title": "Core", "holes": [], "decisions": [
        decision("D-3", decision="Use A.\n```js\nx" + chr(0x2028) + "# y", binds=["bank"])]})
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    text = (folder / "generated" / "pack" / "README.md").read_text(encoding="utf-8")
    assert "\n### bank: Bank feed line\n" in text
    assert "\n### D-3\nUse A.\n\\```js\nx\n\\# y\nreason: Because.\n" in text


AREA_MONEY ="  view area-money {\n    title 'Money'\n    include pay.gateway\n  }\n"
CAPABILITY_BUY = ("  dynamic view capability-buy {\n    title 'Buy'\n    shop.web -> shop.api 'order; %%{init}%% now'\n"
                  "    shop.api -> pay.gateway\n    pay.gateway -> shop.api 'paid'\n  }\n")


def test_check_reports_a_removed_area(tmp_path) -> None:  # AC-9 (the area case)
    repo, out = built(tmp_path)
    (repo / "docs" / "architecture" / "model.c4").write_text(MODEL.replace(AREA_MONEY, ""), encoding="utf-8")
    check = run_tool("check", "--repo", repo, script=DOCS_SCRIPT)
    assert check.returncode == 1
    lines = check.stdout.splitlines()
    for line in ("extra areas/money.md", "extra areas/money.html", "extra pack/areas/money.md", "changed README.md"):
        assert line in lines
    assert not any(line.startswith("extra ") for line in lines if "money" not in line)
    assert run_tool("build", "--repo", repo, script=DOCS_SCRIPT).returncode == 0
    for name in ("areas/money.md", "areas/money.html", "pack/areas/money.md"):
        assert not (out / name).exists()
    assert run_tool("check", "--repo", repo, script=DOCS_SCRIPT).returncode == 0


def test_build_removes_the_emptied_capabilities_folder(tmp_path) -> None:  # AC-17 (the capability documents)
    repo, out = built(tmp_path, records=False)
    (repo / "docs" / "architecture" / "model.c4").write_text(MODEL.replace(CAPABILITY_BUY, ""), encoding="utf-8")
    assert run_tool("build", "--repo", repo, script=DOCS_SCRIPT).returncode == 0
    assert not (out / "capabilities").exists() and not (out / "pack" / "capabilities").exists()
    assert (out / "areas" / "front.md").exists()


def big_model() -> str:
    children = "\n".join(f"    c{i:02} = container 'C{i}'" for i in range(81))
    arrows = "\n".join(f"  big.c{i:02} -> hub" for i in range(81))
    many = "\n".join("    big.c00 -> hub" for _ in range(81))
    lots = "\n".join("    big.c00 -> hub" for _ in range(201))
    return (f"model {{\n  big = system 'Big' {{\n{children}\n  }}\n  hub = system 'Hub'\n{arrows}\n}}\n"
            f"views {{\n  view area-big of big {{\n    include *\n  }}\n"
            f"  dynamic view capability-many {{\n{many}\n  }}\n  dynamic view capability-lots {{\n{lots}\n  }}\n}}\n")


def test_build_over_the_diagram_limits(tmp_path) -> None:  # AC-21
    _, out = built(tmp_path, big_model(), records=False)
    big = (out / "areas" / "big.md").read_text(encoding="utf-8")
    assert "```mermaid" not in big
    assert "The diagram has more than 80 arrows and is not drawn; the tables list everything\\." in big
    assert big.count("| uses | [hub](../README.md) \\(Hub\\) |") == 81
    many = (out / "capabilities" / "many.md").read_text(encoding="utf-8")
    assert "```mermaid\nsequenceDiagram\n" in many and many.count("->>") == 81
    lots = (out / "capabilities" / "lots.md").read_text(encoding="utf-8")
    assert "```mermaid" not in lots and "more than 200 steps" in lots
    assert "| 201 | [big\\.c00](../areas/big.md)" in lots


TICKS = (
    "let ticks = 0;\n"
    "const now = Date.now;\n"
    "Date.now = () => {\n"
    "  const stack = new Error().stack;\n"
    "  if (stack.includes('load.mjs') && stack.includes('architecture-docs/build.mjs') && !stack.includes('pack.mjs')) ticks += 1;\n"
    "  return now();\n"
    "};\n"
    "process.on('exit', () => process.stderr.write(`ticks ${ticks}\\n`));\n"
)


def test_build_checks_the_deadline_after_each_area_and_capability_document(tmp_path) -> None:  # Threat model: --timeout
    preload = tmp_path / "ticks.mjs"
    preload.write_text(TICKS, encoding="utf-8")
    repo = make_repo(tmp_path, MODEL)
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT, preload=preload)
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr.splitlines()[-1] == "ticks 6"  # model.json, the overview, three areas and one capability
````

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_documents.py`
Expected: FAIL, 8 failed, 1 passed (no area or capability document is written; the pack test passes already, its rules come from Task 1).

- [ ] **Step 3: GREEN.**

**In** `skills/shared/scripts/architecture-docs/build.mjs`, **replace**:

```js
import { renderHtml } from './html.mjs';
import { buildPack } from './pack.mjs';
```

**with**:

```js
import { renderHtml, pageHref } from './html.mjs';
import { buildPack } from './pack.mjs';
import { areaDoc, capabilityDoc, documentBase } from './facts.mjs';
import { buildArea } from './area.mjs';
import { buildCapability } from './capability.mjs';
```

**In** `skills/shared/scripts/architecture-docs/build.mjs`, **replace**:

```js
// Spec, What each document holds: every document is built from the export (and the cleaned known-gap entries).
```

**with**:

```js
// A document's Markdown file and its HTML page.
function addDocument(files, rel, tree) {
  files[rel] = renderMarkdown(tree);
  files[pageHref(rel)] = renderHtml(tree);
}

// Spec, What each document holds: every document is built from the export (and the cleaned known-gap entries).
```

**In** `skills/shared/scripts/architecture-docs/build.mjs`, **replace**:

```js
  const overview = buildOverview(data, gap);
  files['README.md'] = renderMarkdown(overview);
  files['index.html'] = renderHtml(overview);
  tick();
```

**with**:

```js
  addDocument(files, 'README.md', buildOverview(data, gap));
  tick();
  const base = documentBase(data);
  for (const area of data.areas) {
    addDocument(files, areaDoc(area.name), buildArea(data, gap, area, base));
    tick();
  }
  for (const capability of data.capabilities) {
    addDocument(files, capabilityDoc(capability.name), buildCapability(data, capability, base));
    tick();
  }
```

- [ ] **Step 4: run the full suite.**

Run: `uv run pytest -q` (about 2.5 minutes; allow 10)
Expected: PASS (671 passed, 1 skipped).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/build.mjs tests/scripts/test_architecture_docs_documents.py
git commit -m "feat(#33): build and check write and compare the area and capability documents"
```
