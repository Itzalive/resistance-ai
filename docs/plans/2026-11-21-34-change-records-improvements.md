# Architecture Docs: Change Records and the Improvement List Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `architecture-docs build` also writes `changes/<id>.md` and `.html` for every change file, and `improvements.md` and `.html`, and `check` compares them; a change file's name is at most 64 characters.

**Architecture:** This repository has no architecture model. The records reader (`skills/shared/scripts/architecture-delta/records.mjs`) refuses a change-file name over 64 characters. Two new modules in `skills/shared/scripts/architecture-docs/`: `change.mjs` (the change record) and `improvements.mjs` (the improvement list). `area-diagram.mjs` `drawing()` takes an optional map of marks, so a change record's framed nodes read `<title> (added)` or `<title> (changed)`. `records-doc.mjs` gains the element row (`ELEMENT_HEADER`, `elementCells`) that the area document and the change record share. `facts.mjs` `documentBase` gains Maps of contracts and open questions by id, which a change record reads to print current records. `build.mjs` adds the documents to the build, each with a `--timeout` check after it. The overview already links to `changes/<id>.md` and `improvements.md`; after this plan those links resolve.

**Tech Stack:** Node ESM, pytest.

**Spec:** `docs/superpowers/specs/2026-11-17-architecture-docs-design.md`, "Records amendment" (the change-file name limit), "Drawing rules" (the change-record diagram), "Change record", "Improvement list", "Shared rules" (links, the 80-arrow note), AC-22, AC-23, AC-27, and the change-record and improvement-list parts of AC-8, AC-9, AC-12, AC-13, AC-17 and AC-21 — decisions applied: none. The owner settled four questions on 2026-11-21 in one spec amendment (commit `8473868`) before this plan: the mark is a label suffix, `<title> (added)` or `<title> (changed)`; the frame is labelled with the change id, and an id listed as both added and changed is marked `added` and shown in both lists; a change record has no Dependencies section, so a neighbour's label alone names its area; the Known gap section lists pairs only, each end linked when it is a model element and otherwise marked "(not in the current model)"; and the improvement list's layout (a heading `<group name> (<count>)`, "None." when empty, details after the id, then `Areas: <links>` or "Not in any area", unmapped modules sorted by module with no areas part). After the alignment check's first round the owner approved a second amendment (commit `8173d46`): a change file's name, without `.json`, is at most 64 characters (records layout rule 2, AC-27), so `export`, which cuts ids at 200 characters, never cuts a change id; and the owner chose that a cycle item shows its reason, as the amended layout lists. This is plan 4 of the spec's four (#34), the last.

**Open decisions:** none. The amendments `8473868` and `8173d46` are spec text. Two rules the tasks apply as written: a change record frames only ids still in the model (`drawing()` reads each framed id's links, and a gone id has none), and the known limit of pack text (only lines starting with `#`, `---`, three backticks or `~~~` are guarded) is unchanged: this plan writes no pack text. Presentation the spec leaves to the writer and the plan fixes in its tests: the `## Diagram` heading with a sentence when nothing is framed, one sentence for each empty section, `Added: ` and `Removed: ` items in one Known gap list, `approved by <by> on <date>`, `Exit: ` and `Summary: ` items, the improvement list's opening sentence, and the `: `, `; ` and `. ` separators of an improvement item; gone ids of every kind are one list after the current ones.

**Size:** 6 tasks, 1398 lines (reported, not a target). Entry paths: the docs tool's `build` and `check`. Task 1's rule sits in the records reader that every command loads through, so it also changes what the delta tool's `export` and `check` accept: four commands, one shared load step, the same place the spec's capabilities rule (plan 1) applies. The per-plan rule counts the docs tool's two paths; the records rule adds a refusal at load, not a new path, and its test runs through `export`.

**Trust boundary:** changed — see Trust-boundary table. No new file writes: only `writer.mjs` writes, and the safety tests (`tests/scripts/test_architecture_docs_safety.py`, `tests/scripts/test_architecture_delta_safety.py`) scan every changed module unchanged. No comment or string in a docs module may hold a forbidden call name followed by `(`: the names in `CHANGES_FILES` (`write`, `link`, `rm`, `cp`, `rename`, `mkdir`, `unlink`, `truncate` and the others) must not be followed by an opening bracket anywhere in the new modules. The new documents carry change-file, record, coverage and known-gap text into Markdown, HTML and Mermaid, and change ids into output paths; the writers' escaping, the label encoding and the change-file name rule are their defence, and Task 6 feeds hostile text through both new documents.

### Risk & Confidence Assessment

**Confidence:** 92% — every code block was run: a dry run built the code once in one scratch copy of main, with the alignment check's fixes as commits on top; this plan's blocks are computed from that copy, applying them in order to the baseline gives the dry run's final files byte for byte, and replaying the tasks in order in that copy gave the RED and GREEN counts below; every "Reviewer looks at" mutation was killed, and every generated diagram parsed with Mermaid 12.2.0.

**Complexity Risk:** Low — a one-line records rule, two document builders over facts the earlier plans already compute (`documentBase`, `areasOf`, `recordTarget`, the drawing rules), one optional argument, one shared element row, and build wiring; no branching on external state, no concurrency, no new file write. The one trap is framing an id that is no longer in the model, which `drawing()` cannot draw; Task 4's tests frame added, changed and gone ids together.

**Environmental Risk:** Low — no new dependency, no new file write, no subprocess; the build at the 5,000-element cap was measured (see below).

**Unknown variables:**
- None in the repository. What stays unverified is the executor's transcription: a test or code block copied with a changed escape (`\\n`, `\\(`, `#40;`) fails its exact-text assert, which is the intended signal.
- How a reader's Markdown renderer lays out the diagrams: the diagram text is parsed by Mermaid 12.2.0 in the dry run, not rendered.

**Main failure modes:** a section of a change record or of the improvement list missing, out of order, or with a wrong link (Tasks 4 and 5 compare exact trees); a gone id framed in a diagram (the build stops with an error; `test_change_record_diagram` frames one); a tool test still expecting four files after the improvement list is added (Task 6 moves those asserts); a module comment that names a forbidden call (the safety test fails the commit).

**Measured at the cap:** an export-shaped model of 5,000 elements, 10,000 imports, 5,000 runtime links, 2,000 decisions, 500 contracts, 500 open questions, 500 known-gap entries, 51 areas (one holding every element), a coverage file with 2,000 unmapped modules, and 1,001 change files (one of them adding or changing every element) builds its change records in 0.45 s and its improvement list in 0.09 s (Markdown and HTML rendered, 11.2 MB in all).

---

## Caller and test sweep

Searched: `skills/`, `tests/`, `scripts/`, `agents/` with `rg -n "drawing\(|documentBase|buildFiles|CHANGE_FILE|wrote [0-9]+ files|missing README|index.html\", \"pack|ticks [0-9]|rglob|iterdir|improvements|changes/|element\.tags\.map" skills tests scripts agents`, and `rg -n "changes/[0-9]{4}-[0-9]{2}-[0-9]{2}-" tests` for change-file names in tests (none is over 64 characters).

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `CHANGE_FILE` refuses a name over 64 characters | `skills/shared/scripts/architecture-delta/records.mjs:11` (`FOLDERS`) | caller | — | none: the pattern is used as before |
| same | every test that writes a change file (`tests/scripts/test_architecture_delta_records.py`, `test_architecture_docs_overview.py`, `test_architecture_docs_documents.py`) | fixture | — | none: their names are 16 to 30 characters |
| `drawing(framedIds, frameText, gap, base)` → `drawing(framedIds, frameText, gap, base, marks = new Map())` | `skills/shared/scripts/architecture-docs/area.mjs:48` | caller | — | none: an area document passes no marks |
| same | `tests/scripts/test_architecture_docs_area.py` (`test_area_drawing` and the other `d.drawing(...)` calls) | test | — | none: they pass four arguments and assert unmarked titles, which are unchanged |
| the area document's element row moves to `records-doc.mjs` (`ELEMENT_HEADER`, `elementCells`) | `skills/shared/scripts/architecture-docs/area.mjs:6`, `:52-57` | caller | 3 | the import gains `ELEMENT_HEADER` and `elementCells`; the table becomes `table(ELEMENT_HEADER, area.elements.map((id) => [idCell(id, ctx), ...elementCells(ctx.elements.get(id))]))` (Task 3 Step 1) |
| `documentBase` gains `contracts` and `holes` | `skills/shared/scripts/architecture-docs/build.mjs:40`, `tests/scripts/test_architecture_docs_area.py:66`, `:227` | caller | — | none: two keys added, none changed |
| `buildFiles` adds the change records and the improvement list | `skills/shared/scripts/architecture-docs.mjs:67` | caller | — | none: same signature and return shape |
| same | `tests/scripts/test_architecture_docs_tool.py:32` | assert | 6 | `(0, "wrote 6 files, removed 0\n")` |
| same | `tests/scripts/test_architecture_docs_tool.py:47` | assert | 6 | `"missing README.md\nmissing improvements.html\nmissing improvements.md\nmissing index.html\nmissing pack/README.md\nmissing pack/model.json\n6 missing, 0 changed, 0 extra\n"` |
| same | `tests/scripts/test_architecture_docs_tool.py:54` | assert | 6 | `"changed README.md\nextra areas/old.md\nchanged improvements.html\nchanged improvements.md\nchanged index.html\nchanged pack/README.md\nchanged pack/model.json\n0 missing, 6 changed, 1 extra\n"` (the improvement list names the retitled element) |
| same | `tests/scripts/test_architecture_docs_tool.py:56` | assert | 6 | `"wrote 6 files, removed 1\n"` |
| same | `tests/scripts/test_architecture_docs_tool.py:57`, `:156` | assert | 6 | `["README.md", "improvements.html", "improvements.md", "index.html", "pack/README.md", "pack/model.json"]` |
| same | `tests/scripts/test_architecture_docs_documents.py:224` (`test_check_reports_a_removed_area`) | assert | 6 | the expected lines add `"changed improvements.md"` (a known-gap entry's areas lose `money`) |
| same | `tests/scripts/test_architecture_docs_documents.py:276-282` (`test_build_checks_the_deadline_after_each_area_and_capability_document`, `ticks 6`) | assert | 6 | renamed `test_build_checks_the_deadline_after_each_document`; it writes one change file and expects `ticks 8` (model.json, the overview, three areas, one capability, one change record, the improvement list) |
| same | `tests/scripts/test_architecture_docs_pack.py:512-513` (lists `pack/` only), `tests/scripts/test_architecture_docs_overview.py` (reads `README.md` and `index.html` only), `tests/scripts/test_architecture_docs_documents.py:175` (`### P\-1` only in `README.md` among non-pack Markdown files: the improvement list links `P-1`, it never heads it) | assert | — | none |

Not affected (checked): `tests/scripts/test_architecture_docs_writer.py:27` and `:51` list folders built from their own file sets; `tests/scripts/test_architecture_docs_out.py` calls `listOut` directly and `changes` is already in `out.mjs` `FOLDERS`; `tests/scripts/test_architecture_docs_build.py` and `test_architecture_docs_facts.py` call none of the changed functions; `scripts/` and `agents/` hold no caller.

## Trust-boundary table

| Producer or reader | Where it is used | Text it receives | Untrusted source | Task | Proving test |
|---|---|---|---|---|---|
| change record list items, headings, tables and paragraphs | `changes/<id>.md` and `.html` | a change file's `summary`, `asked_by`, `run`, `date`, `rejected`, `approved.by`, `check.summary`; current record text | change-file and record authors | 4, 6 | the writers' escaping (plan 2b, `test_markdown_escapes_model_text`, `test_html_escapes_every_value`); end to end: `test_build_escapes_hostile_change_and_improvement_text` (a link, a tag, `\|`, `%%{init}%%` and an escape sequence) |
| ids in a change file's lists and known-gap pairs that are not model elements | `changes/<id>.md` and `.html` (What changed, Known gap) | any string: only `clean()`ed by `export`, never checked against the model | change-file authors | 4, 6 | `test_build_escapes_hostile_coverage_and_ids_not_in_the_model` (a hostile id added, removed and as a known-gap end: escaped, with its note) |
| the change record's code block | `changes/<id>.md` and `.html` | `check.output` | change-file authors | 4, 6 | `test_build_escapes_hostile_change_and_improvement_text`: an output holding three backticks gets a four-backtick fence, and its escape sequence never reaches the file |
| the change-record diagram's frame and node labels | `changes/<id>.md` and `.html` | the change id; element titles with the mark; neighbour titles and area names | change-file and model authors | 2, 4, 6 | `test_build_escapes_hostile_change_and_improvement_text` (a hostile title framed and marked: no `;`, `"` or `%%` left in the diagram); Mermaid's own label encoding (plan 2b, `test_mermaid_label_encodes_entity_and_statement_marks`) |
| improvement list items | `improvements.md` and `.html` | known-gap `reason` and `close_by`; record ids; element titles | known-gap, record and model authors | 5, 6 | `test_build_escapes_hostile_change_and_improvement_text` (a known-gap reason with `\|` and `<b>`, cleaned and escaped) |
| improvement list unmapped-code items | `improvements.md` and `.html` | coverage `unmapped` module and reason | coverage authors | 5, 6 | `test_build_escapes_hostile_coverage_and_ids_not_in_the_model` (a module holding a link and a reason holding `<b>`, `\|` and an escape sequence) |
| link targets | both new documents | `changes/<id>.md`, `areas/<name>.md`, `README.md`, relative | change-file and model authors | 1, 4, 5, 6 | change ids match the change-file pattern, at most 64 characters, and equal their file name (Task 1, `test_change_file_name_is_at_most_64_characters`), so `export` never cuts one; `relative` and `SAFE_HREF` refuse anything else (plan 2b); `test_build_writes_change_records` |
| output paths | `writer.mjs` (writes under `--out`) | `changes/<id>.md` and `.html`, `improvements.md` and `.html` | change-file authors (ids) | 1, 6 | `changes` is in `out.mjs` `FOLDERS`; one file pair per change file (`test_build_writes_one_record_per_change_file`); `test_check_reports_a_removed_change_file` (extra files reported, removed by `build`, the emptied folder removed) |

## Checkpoints

Mutation checkpoints run only around strong-tier tasks. Task 6 is the strong-tier task (it carries the trust boundary end to end); Tasks 1 to 5 are fast and standard, and their "Reviewer looks at" items are left to survivability and the code review at plan end.

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 6 | 6 | Task 6 items 1–7 (quick confirmation); the reviewer's own mutations at the decision points of Task 6 and the trust-boundary rows; full suite `uv run pytest -q` |
| — | — | 1–5 | Task 1 items 1–2, Task 2 items 1–2, Task 3 items 1–4, Task 4 items 1–14, Task 5 items 1–16: survivability and the code review |

## Shared test fixture

Tasks 2 to 5 test the modules against the export-shaped fixture of `tests/scripts/test_architecture_docs_area.py` (`DATA`, `RECORDS`, `GAP`, and the helpers `built`, `section`, `heads`, `L`, `para`, `element`), which `tests/scripts/test_architecture_docs_changes.py` imports. It is not a valid model (records skip fields the documents never print). Its areas: `front` (`shop`, `shop.api`, `shop.api.orders`, `shop.web`) and `money` (`pay`, `pay.gateway`); `bank` and `ledger` are in no area. Task 6 builds a real model through `build` instead, with the model, records and known gap of `tests/scripts/test_architecture_docs_documents.py`.

## How to apply the code blocks

Every edit is one of three kinds, each followed by its fenced block: **Create** a file, **Append to** a file (the block is added at its end), or **In** a file **replace** one exact block **with** another (the old block occurs exactly once). Copy blocks byte for byte: the escapes `\n`, `\\` and the Mermaid entities (`#40;`) are part of the code. A block's fence is longer than any run of backticks inside it.

---

### Task 1: a change file's name is at most 64 characters

**Tier:** fast — one lookahead in one pattern, complete code given.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/records.mjs` (`CHANGE_FILE`)
- Test: `tests/scripts/test_architecture_delta_records.py`

**Callers that move with this task:** none to edit; Step 4 runs the tests of the change-file fixtures (sweep rows `records.mjs:11` and the fixtures in `test_architecture_delta_records.py`, `test_architecture_docs_overview.py`, `test_architecture_docs_documents.py`)

**Reviewer looks at:**
1. The limit off by one — mutation: in `records.mjs`, replace `(?=.{1,64}\.json$)` with `(?=.{1,63}\.json$)` — killed by: `test_change_file_name_is_at_most_64_characters`
2. The limit dropped — mutation: delete `(?=.{1,64}\.json$)` — killed by: `test_change_file_name_is_at_most_64_characters`

- Satisfies Spec AC: AC-27 (64 characters accepted, 65 refused with `not a valid file name here`); Records amendment as amended (`8173d46`)
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_delta_records.py`:

```python


def test_change_file_name_is_at_most_64_characters(tmp_path) -> None:  # AC-27 (docs spec): a change id is never cut
    at_limit = "2026-11-16-" + "a" * 53
    over = "2026-11-16-" + "b" * 54
    files = {f"changes/{at_limit}.json": change(at_limit), f"changes/{over}.json": change(over)}
    repo, _ = model_folder(tmp_path, files)
    assert error_lines(run_tool("export", "--repo", repo)) == [f"error: record-error: changes/{over}.json: -: not a valid file name here"]
    (repo / "docs" / "architecture" / "changes" / f"{over}.json").unlink()
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    assert [record["id"] for record in json.loads(proc.stdout)["changes"]] == [at_limit]
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_records.py`
Expected: FAIL, 1 failed, 51 passed (the 65-character name is read).

- [ ] **Step 3: GREEN.**

**In** `skills/shared/scripts/architecture-delta/records.mjs` **replace**:

```js
const CHANGE_FILE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(-[a-z0-9]+)*\.json$/;
```

**with**:

```js
// A change file's name, without `.json`, is at most 64 characters, so `export` (which cuts ids at 200) never cuts a
// change id.
const CHANGE_FILE = /^(?=.{1,64}\.json$)[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(-[a-z0-9]+)*\.json$/;
```

- [ ] **Step 4: run the task's tests and the tests of the callers that write change files.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_records.py tests/scripts/test_architecture_docs_overview.py tests/scripts/test_architecture_docs_documents.py`
Expected: PASS (69 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/records.mjs tests/scripts/test_architecture_delta_records.py
git commit -m "fix(#34): a change file's name is at most 64 characters, so export never cuts a change id (AC-27)"
```

---

### Task 2: the drawing marks a change record's framed nodes

**Tier:** fast — one optional argument and one line, complete code given.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/area-diagram.mjs`
- Test: `tests/scripts/test_architecture_docs_area.py`

**Callers that move with this task:** none (sweep rows `area.mjs:48` and the area tests pass no marks)

**Reviewer looks at:**
1. The mark dropped from a framed node's label — mutation: in `area-diagram.mjs`, replace ``return marks.has(id) ? `${title} (${marks.get(id)})` : title;`` with `return title;` — killed by: `test_change_drawing_marks_framed_nodes`
2. Every framed node marked — mutation: replace the same line with ``return `${title} (${marks.get(id) ?? 'added'})`;`` — killed by: `test_drawing_leaves_an_unmarked_framed_node_as_its_title`

**Pinned by:** an area diagram's framed nodes stay their titles: `tests/scripts/test_architecture_docs_area.py::test_area_drawing` asserts `{"id": "shop", "text": "Shop"}` and the other framed nodes exactly; it fails if an absent `marks` adds any suffix.

- Satisfies Spec AC: AC-22 (the added element framed; the mark's form, amendment `8473868`)
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**In** `tests/scripts/test_architecture_docs_area.py` **replace**:

```python
    assert [node["id"] for node in picture["nodes"]] == ["bank", "pay"]
```

**with**:

```python
    assert [node["id"] for node in picture["nodes"]] == ["bank", "pay"]


def test_change_drawing_marks_framed_nodes() -> None:  # Change record: framed nodes labelled `<title> (added)` or `(changed)`
    marks = "new Map([['shop.web', 'added'], ['pay.gateway', 'changed']])"
    picture = run(f"d.drawing(['shop.web', 'pay.gateway'], '2026-11-05-more', [], base, {marks})", gap=[])
    assert picture["frame"] == {"text": "2026-11-05-more", "ids": ["pay.gateway", "shop.web"]}
    assert picture["nodes"] == [
        {"id": "bank", "text": "Bank (no area)"},
        {"id": "pay.gateway", "text": "Gateway (changed)"},
        {"id": "shop.api", "text": "API (front)"},
        {"id": "shop.api.orders", "text": "Orders (front)"},
        {"id": "shop.web", "text": "Web (added)"},
    ]


def test_drawing_leaves_an_unmarked_framed_node_as_its_title() -> None:  # Change record: only marked ids carry a mark
    picture = run("d.drawing(['shop.web', 'pay.gateway'], 'c', [], base, new Map([['shop.web', 'added']]))", gap=[])
    assert {node["id"]: node["text"] for node in picture["nodes"]}["pay.gateway"] == "Gateway"
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py`
Expected: FAIL, 1 failed, 27 passed (`drawing()` ignores the marks; the unmarked-node test passes already and guards the GREEN step).

- [ ] **Step 3: GREEN.**

**In** `skills/shared/scripts/architecture-docs/area-diagram.mjs` **replace**:

```js
// The nodes, arrows and frame of a diagram whose framed elements are `framedIds`: { nodes, arrows, frame }.
export function drawing(framedIds, frameText, gap, base) {
```

**with**:

```js
// The nodes, arrows and frame of a diagram whose framed elements are `framedIds`: { nodes, arrows, frame }. `marks` maps
// a framed id to `added` or `changed` (a change record's diagram); a marked node is labelled `<title> (<mark>)`.
export function drawing(framedIds, frameText, gap, base, marks = new Map()) {
```

**In** `skills/shared/scripts/architecture-docs/area-diagram.mjs` **replace**:

```js
    if (framed.has(id)) return title;
```

**with**:

```js
    if (framed.has(id)) return marks.has(id) ? `${title} (${marks.get(id)})` : title;
```

- [ ] **Step 4: run the task's tests and the area documents' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py tests/scripts/test_architecture_docs_documents.py`
Expected: PASS (37 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/area-diagram.mjs tests/scripts/test_architecture_docs_area.py
git commit -m "feat(#34): the drawing marks a change record's framed nodes added or changed"
```

---

### Task 3: one element row for the area document and the change record

**Tier:** fast — a move of existing code, complete code given; no behaviour changes.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/records-doc.mjs` (adds `ELEMENT_HEADER`, `elementCells`)
- Modify: `skills/shared/scripts/architecture-docs/area.mjs` (uses them)

**Callers that move with this task:** sweep row `area.mjs:6`, `:52-57` (this task's own edit)

**Reviewer looks at:**
1. The description cell lost — mutation: in `records-doc.mjs`, replace `[element.description ?? '']` with `['']` — killed by: `test_area_document_elements`
2. The code cell lost — mutation: replace `[element.code.join(', ')],` with `[''],` — killed by: `test_area_document_elements`
3. The rules cell lost — mutation: replace `[element.rules.join(', ')],` with `[''],` — killed by: `test_area_document_elements`
4. The tags cell lost — mutation: replace ``[element.tags.map((tag) => `#${tag}`).join(' ')]];`` with `['']];` — killed by: `test_area_document_elements`

**Pinned by:** the area document's element table is unchanged: `tests/scripts/test_architecture_docs_area.py::test_area_document_elements` asserts its header `["Element", "Title", "Description", "Code", "Rules", "Tags"]` and the row `[["shop"], ["Shop"], ["Sells things."], ["src/shop, src/lib"], ["BR-1, BR-2"], ["#edge #web"]]` exactly; it fails if any cell moves or changes.

- Satisfies Spec AC: Area, Elements (unchanged); Change record, What changed ("printed in full", used by Task 4)
- Decisions applied: none
- **Test retention:** none added (a move; pinned as above)

- [ ] **Step 1: GREEN (no RED: the behaviour is unchanged and pinned).**

**In** `skills/shared/scripts/architecture-docs/records-doc.mjs` **replace**:

```js
const withTitle = (id, href, title) => [docLink(id, href), ` (${title ?? id})`];
```

**with**:

```js
const withTitle = (id, href, title) => [docLink(id, href), ` (${title ?? id})`];

// Spec, Area and Change record: an element printed in full is a table row: id, title, description, code, rules, tags.
export const ELEMENT_HEADER = ['Element', 'Title', 'Description', 'Code', 'Rules', 'Tags'];
export const elementCells = (element) => [[element.title], [element.description ?? ''], [element.code.join(', ')],
  [element.rules.join(', ')], [element.tags.map((tag) => `#${tag}`).join(' ')]];
```

**In** `skills/shared/scripts/architecture-docs/area.mjs` **replace**:

```js
import { decisionBlocks, contractBlocks, holeBlocks, elementLinks, areaLinks, capabilityLinks } from './records-doc.mjs';
```

**with**:

```js
import {
  ELEMENT_HEADER, decisionBlocks, contractBlocks, holeBlocks, elementCells, elementLinks, areaLinks, capabilityLinks,
} from './records-doc.mjs';
```

**In** `skills/shared/scripts/architecture-docs/area.mjs` **replace**:

```js
  blocks.push(...orSay(area.elements.length === 0 ? [] : [table(['Element', 'Title', 'Description', 'Code', 'Rules', 'Tags'],
    area.elements.map((id) => {
      const element = ctx.elements.get(id);
      return [idCell(id, ctx), [element.title], [element.description ?? ''], [element.code.join(', ')],
        [element.rules.join(', ')], [element.tags.map((tag) => `#${tag}`).join(' ')]];
    }))], 'The area has no elements.'));
```

**with**:

```js
  blocks.push(...orSay(area.elements.length === 0 ? [] : [table(ELEMENT_HEADER,
    area.elements.map((id) => [idCell(id, ctx), ...elementCells(ctx.elements.get(id))]))], 'The area has no elements.'));
```

- [ ] **Step 2: run the area tests, the documents tests and the safety tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_area.py tests/scripts/test_architecture_docs_documents.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (41 passed).

- [ ] **Step 3: commit.**

```bash
git add skills/shared/scripts/architecture-docs/records-doc.mjs skills/shared/scripts/architecture-docs/area.mjs
git commit -m "refactor(#34): one element row for the area and change documents"
```

---

### Task 4: the change record

**Tier:** standard — complete code given; one new module and two lookups added to `documentBase`.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/change.mjs`
- Modify: `skills/shared/scripts/architecture-docs/facts.mjs` (`documentBase`)
- Test: `tests/scripts/test_architecture_docs_changes.py` (new)

**Callers that move with this task:** none (sweep row `documentBase`: two keys added)

**Reviewer looks at:**
1. `changed` overrides `added` for an id in both lists — mutation: in `change.mjs` `diagramBlock`, swap the two `for` lines so `added` is set first — killed by: `test_change_record_marks_an_id_in_both_lists_added`
2. A gone element framed — mutation: replace `  for (const id of change.elements.added) if (ctx.elements.has(id)) marks.set(id, 'added');` with `  for (const id of change.elements.added) marks.set(id, 'added');` — killed by: `test_change_record_diagram`
3. A diagram drawn with nothing to frame — mutation: delete the line `  if (marks.size === 0) return paragraph('No element the change added or changed is in the current model.');` — killed by: `test_change_record_with_nothing_to_draw`
4. Removed records printed in full — mutation: in `recordBlocks`, replace `if (part === 'removed') {` with `if (part === 'never') {` — killed by: `test_change_record_prints_current_records_in_full_and_gone_ones_as_text`
5. A gone element shown without its note — mutation: in `elementBlocks`, replace `blocks.push(list(gone.map((id) => [goneText(id)])));` with `blocks.push(list(gone.map((id) => [id])));` — killed by: `test_change_record_what_changed`
6. Current elements out of the file's order — mutation: replace `const current = ids.filter((id) => ctx.elements.has(id));` with `const current = ids.filter((id) => ctx.elements.has(id)).reverse();` — killed by: `test_change_record_prints_elements_in_full_in_file_order`
7. Gone records out of the file's order — mutation: replace `const gone = ids.filter((id) => !records.has(id));` with `const gone = ids.filter((id) => !records.has(id)).reverse();` — killed by: `test_change_record_prints_current_records_in_full_and_gone_ones_as_text`
8. Choices skip changed decisions — mutation: replace `new Set([...change.decisions.added, ...change.decisions.changed])` with `new Set([...change.decisions.added])` — killed by: `test_change_record_choices_not_taken`
9. Choices not deduplicated — mutation: replace the same expression with `[...change.decisions.added, ...change.decisions.changed]` — killed by: `test_change_record_choices_not_taken`
10. A gone known-gap end linked — mutation: replace `const end = (id) => (ctx.elements.has(id) ? elementLinks([id], ctx) : [goneText(id)]);` with `const end = (id) => elementLinks([id], ctx);` — killed by: `test_change_record_known_gap`
11. Approval ignored — mutation: replace `change.approved === null ? 'Not yet approved'` with `change.approved !== undefined ? 'Not yet approved'` — killed by: `test_change_record_approval`
12. The check output not in a code block — mutation: replace `code(change.check.output));` with `paragraph(change.check.output));` — killed by: `test_change_record_check`
13. An element not printed in full — mutation: replace `...elementCells(ctx.elements.get(id))]` with `...elementCells({ ...ctx.elements.get(id), description: null })]` — killed by: `test_change_record_prints_elements_in_full_in_file_order`
14. A change diagram of exactly 80 arrows replaced by the note — mutation: in `mermaid.mjs`, replace `if (arrows.length > ARROW_LIMIT) return null;` with `if (arrows.length >= ARROW_LIMIT) return null;` — killed by: `test_change_record_at_the_arrow_limit` (and 81 arrows by `test_change_record_over_the_arrow_limit`)

**Pinned by:** `documentBase`'s existing keys are unchanged: every area and capability test in `tests/scripts/test_architecture_docs_area.py` builds through it and compares exact trees.

- Satisfies Spec AC: AC-22 (in the module: "Not yet approved", the added element framed, the decision in full, the removed contract as plain text, the gone element marked "(not in the current model)", the decision's rejected options); AC-21 (the change-record flowchart: 80 arrows drawn, 81 replaced by the note); Change record as amended (`8473868`)
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Create** `tests/scripts/test_architecture_docs_changes.py`:

```python
"""Change records and the improvement list (spec 2026-11-17-architecture-docs-design.md, "Change record",
"Improvement list")."""

from __future__ import annotations

import copy

from arch_delta_support import require_node
from test_architecture_docs_area import GAP, RECORDS, L, built, element, heads, para, section

require_node()

GONE = " (not in the current model)"


def lists(added: list = (), changed: list = (), removed: list = ()) -> dict:
    return {"added": list(added), "changed": list(changed), "removed": list(removed)}


def change(**over) -> dict:
    record = {"id": "2026-11-05-more", "date": "2026-11-05", "run": "later-stage", "asked_by": "#1", "summary": "More.",
              "rejected": [], "elements": lists(), "decisions": lists(), "holes": lists(), "contracts": lists(),
              "gap": {"added": [], "removed": []}, "check": {"exit": 0, "summary": "ok", "output": "ok\n"}, "approved": None}
    record.update(over)
    return record


# AC-22: adds an element, adds one a later change removed, changes an element and a decision, removes a contract.
MORE = change(rejected=["A monolith."], elements=lists(["shop.web", "shop.cart"], ["pay"], ["shop.old"]),
              decisions=lists(changed=["D-2"]), contracts=lists(removed=["C-9"]),
              gap={"added": [["shop.api", "ledger"]], "removed": [["shop.cart", "pay"]]},
              check={"exit": 1, "summary": "1 new breach", "output": "New breaches\n  shop.api -> ledger (1 edges)\n"})


def with_change(record: dict, data: dict = RECORDS) -> dict:
    data = copy.deepcopy(data)
    for decision in data["decisions"]:
        if decision["id"] == "D-2":
            decision["rejected"] = ["Two APIs.", "No API."]
        if decision["id"] == "D-0":
            decision["rejected"] = ["A fat web."]
    data["changes"] = [record]
    return data


def change_doc(record: dict = MORE, data: dict = RECORDS, gap: list = GAP) -> dict:
    return built("change.mjs", "m.buildChange(data, gap, data.changes[0], base)", with_change(record, data), gap)


ELEMENT_HEADER = ["Element", "Title", "Description", "Code", "Rules", "Tags"]


def test_change_record_layout() -> None:  # Change record: summary, asked by, run, date, approval; the sections in order; AC-22
    document = change_doc()
    assert document["title"] == "2026-11-05-more"
    assert document["blocks"][0] == {"type": "list", "items": [
        ["Summary: ", "More."], ["Asked by: ", "#1"], ["Run: ", "later-stage"], ["Date: ", "2026-11-05"],
        ["Approval: ", "Not yet approved"]]}
    assert heads(document, 2) == ["Diagram", "What changed", "Choices not taken", "Known gap", "Check"]


def test_change_record_approval() -> None:  # Change record: approval by and date
    document = change_doc(change(approved={"by": "Owner", "date": "2026-11-06"}))
    assert document["blocks"][0]["items"][-1] == ["Approval: ", "approved by Owner on 2026-11-06"]


def test_change_record_diagram() -> None:  # Change record: added and changed elements still in the model framed and marked; AC-22
    diagram = section(change_doc(), "Diagram")
    assert len(diagram) == 1 and diagram[0]["type"] == "diagram"
    text = diagram[0]["text"]
    assert text.startswith('flowchart LR\n  subgraph frame["2026-11-05-more"]\n')
    frame = text.split("\n  end\n")[0]
    assert '["Web #40;added#41;"]' in frame and '["Pay #40;changed#41;"]' in frame
    assert "shop.cart" not in text and "Old" not in text


def test_change_record_marks_an_id_in_both_lists_added() -> None:  # Change record (amended): added wins
    text = section(change_doc(change(elements=lists(["pay"], ["pay", "shop.web"]))), "Diagram")[0]["text"]
    assert '["Pay #40;added#41;"]' in text and '["Web #40;changed#41;"]' in text and "Pay #40;changed" not in text


def test_change_record_with_nothing_to_draw() -> None:  # Change record: no diagram when no added or changed element is current
    document = change_doc(change(elements=lists(["shop.cart"], [], ["pay"])))
    assert section(document, "Diagram") == [para("No element the change added or changed is in the current model.")]


def test_change_record_over_the_arrow_limit() -> None:  # Shared rules: a flowchart over 80 arrows is replaced by the note
    data = {**RECORDS, "allowed": [{"from": "pay", "to": f"x{i:02}", "titles": []} for i in range(81)], "runtime": [],
            "elements": RECORDS["elements"] + [element(f"x{i:02}", f"X{i}") for i in range(81)]}
    document = change_doc(change(elements=lists(changed=["pay"])), data, [])
    assert section(document, "Diagram") == [para("The diagram has more than 80 arrows and is not drawn; the tables list everything.")]


def test_change_record_what_changed() -> None:  # Change record: What changed; AC-22
    blocks = section(change_doc(), "What changed")
    assert [block["text"] for block in blocks if block["type"] == "heading" and block["level"] == 3] == [
        "Elements added", "Elements changed", "Elements removed", "Decisions changed", "Contracts removed"]
    assert blocks[1] == {"type": "table", "header": ELEMENT_HEADER,
                         "rows": [[[L("shop.web", "../areas/front.md")], ["Web"], [""], [""], [""], [""]]]}
    assert blocks[2] == {"type": "list", "items": [["shop.cart" + GONE]]}
    assert blocks[4]["rows"] == [[[L("pay", "../areas/money.md")], ["Pay"], [""], [""], [""], [""]]]
    assert blocks[6] == {"type": "list", "items": [["shop.old"]]}
    assert blocks[8] == {"type": "heading", "level": 4, "text": "D-2"}
    assert blocks[9] == para("One API.")
    assert ["Rejected: ", "Two APIs.; No API."] in blocks[10]["items"]
    assert blocks[10]["items"][-1] == ["Areas: ", L("front", "../areas/front.md"), " (Front)"]
    assert blocks[11:] == [{"type": "heading", "level": 3, "text": "Contracts removed"}, {"type": "list", "items": [["C-9"]]}]


def test_change_record_prints_current_records_in_full_and_gone_ones_as_text() -> None:  # Change record: What changed
    record = change(contracts=lists(["C-7", "C-1"]), holes=lists(changed=["H-9", "H-1", "H-8"]), decisions=lists(["D-8"], [], ["D-1"]))
    blocks = section(change_doc(record), "What changed")
    assert blocks[0:2] == [{"type": "heading", "level": 3, "text": "Decisions added"}, {"type": "list", "items": [["D-8" + GONE]]}]
    assert blocks[2:4] == [{"type": "heading", "level": 3, "text": "Decisions removed"}, {"type": "list", "items": [["D-1"]]}]
    assert blocks[4:6] == [{"type": "heading", "level": 3, "text": "Contracts added"}, {"type": "heading", "level": 4, "text": "C-1: Card API"}]
    assert blocks[7] == {"type": "list", "items": [["C-7" + GONE]]}
    assert blocks[8:11] == [{"type": "heading", "level": 3, "text": "Open questions changed"},
                            {"type": "heading", "level": 4, "text": "H-1"}, para("Why one API?")]
    assert blocks[12] == {"type": "list", "items": [["H-9" + GONE], ["H-8" + GONE]]}
    assert len(blocks) == 13


def test_change_record_shows_an_id_in_two_lists_in_both() -> None:  # Change record (amended): each list as the file gives it
    blocks = section(change_doc(change(elements=lists(["pay"], ["pay"]))), "What changed")
    assert [block["rows"][0][1] for block in blocks if block["type"] == "table"] == [["Pay"], ["Pay"]]


def test_change_record_with_no_ids() -> None:  # Change record: empty sections say so
    document = change_doc(change())
    assert section(document, "What changed") == [para("The change file lists no elements or records.")]
    assert section(document, "Choices not taken") == [para("No choices are recorded as not taken.")]
    assert section(document, "Known gap") == [para("The change added or removed no known-gap entries.")]


def test_change_record_choices_not_taken() -> None:  # Change record: the change's rejected list, then its decisions'; AC-22
    record = change(rejected=["A monolith."], decisions=lists(["D-2", "D-8"], ["D-0", "D-2"], ["D-1"]))
    assert section(change_doc(record), "Choices not taken") == [{"type": "list", "items": [
        ["A monolith."], [L("D-2", "../areas/front.md"), ": ", "Two APIs."], [L("D-2", "../areas/front.md"), ": ", "No API."],
        [L("D-0", "../areas/front.md"), ": ", "A fat web."]]}]


def test_change_record_known_gap() -> None:  # Change record (amended): pairs, ends linked or marked gone, no reason
    assert section(change_doc(), "Known gap") == [{"type": "list", "items": [
        ["Added: ", L("shop.api", "../areas/front.md"), " (API)", " -> ", L("ledger", "../README.md"), " (Ledger)"],
        ["Removed: ", "shop.cart" + GONE, " -> ", L("pay", "../areas/money.md"), " (Pay)"]]}]


def test_change_record_check() -> None:  # Change record: exit, summary, and the output in a code block
    assert section(change_doc(), "Check") == [
        {"type": "list", "items": [["Exit: ", "1"], ["Summary: ", "1 new breach"]]},
        {"type": "code", "text": "New breaches\n  shop.api -> ledger (1 edges)\n"}]


def test_change_record_prints_elements_in_full_in_file_order() -> None:  # Change record: in full, each list as the file gives it
    table = section(change_doc(change(elements=lists(["shop.web", "shop"]))), "What changed")[1]
    assert table["rows"] == [
        [[L("shop.web", "../areas/front.md")], ["Web"], [""], [""], [""], [""]],
        [[L("shop", "../areas/front.md")], ["Shop"], ["Sells things."], ["src/shop, src/lib"], ["BR-1, BR-2"], ["#edge #web"]],
    ]


def test_change_record_at_the_arrow_limit() -> None:  # Shared rules: a flowchart with 80 arrows is still drawn
    data = {**RECORDS, "allowed": [{"from": "pay", "to": f"x{i:02}", "titles": []} for i in range(80)], "runtime": [],
            "elements": RECORDS["elements"] + [element(f"x{i:02}", f"X{i}") for i in range(80)]}
    diagram = section(change_doc(change(elements=lists(changed=["pay"])), data, []), "Diagram")
    assert diagram[0]["type"] == "diagram" and diagram[0]["text"].count(" --> ") == 80
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_changes.py`
Expected: FAIL, 15 failed (`change.mjs` does not exist).

- [ ] **Step 3: GREEN.**

**Create** `skills/shared/scripts/architecture-docs/change.mjs`:

```js
// A change record (spec, What each document holds, Change record): the change's summary, asker, run, date and
// approval; a diagram of the elements it added or changed; what changed; the choices not taken; its known-gap pairs;
// its check. A change file holds only ids, so a record is printed as it stands in the model now.
import { doc, heading, paragraph, list, table, code, diagram, docLink } from './tree.mjs';
import { changeDoc, elementTarget, recordTarget, relative } from './facts.mjs';
import { ELEMENT_HEADER, decisionBlocks, contractBlocks, holeBlocks, elementCells, elementLinks } from './records-doc.mjs';
import { drawing, drawingText, TOO_MANY_ARROWS } from './area-diagram.mjs';

export const GONE = ' (not in the current model)';
const PARTS = ['added', 'changed', 'removed'];
// The record kinds of a change file after its elements, in document order: the change file's key, the heading word,
// the Map of current records in `base`, and how a current record is printed in full.
const KINDS = [
  { key: 'decisions', word: 'Decisions', records: 'decisions', blocks: decisionBlocks },
  { key: 'contracts', word: 'Contracts', records: 'contracts', blocks: contractBlocks },
  { key: 'holes', word: 'Open questions', records: 'holes', blocks: holeBlocks },
];

const orSay = (blocks, text) => (blocks.length > 0 ? blocks : [paragraph(text)]);
const goneText = (id) => `${id}${GONE}`;

const elementRow = (id, ctx) => [[docLink(id, relative(ctx.doc, elementTarget(id, ctx.byElement)))], ...elementCells(ctx.elements.get(id))];

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

// Spec, What changed: added and changed records still in the model in full, in the change file's order, then the gone
// ones as plain text, as for elements; removed ids as plain text.
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
    const records = ctx[kind.records];
    for (const id of ids) if (records.has(id)) blocks.push(...kind.blocks(records.get(id), ctx, 4));
    const gone = ids.filter((id) => !records.has(id));
    if (gone.length > 0) blocks.push(list(gone.map((id) => [goneText(id)])));
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
```

**In** `skills/shared/scripts/architecture-docs/facts.mjs` **replace**:

```js
// What every area and capability document reads, built once per build: `byElement` (areasByElement), `links`
// (linkIndex), `titles` (titlesOf), `elements` and `decisions` (Maps by id).
```

**with**:

```js
// What every area, capability and change document reads, built once per build: `byElement` (areasByElement), `links`
// (linkIndex), `titles` (titlesOf), `elements`, `decisions`, `contracts` and `holes` (Maps by id).
```

**In** `skills/shared/scripts/architecture-docs/facts.mjs` **replace**:

```js
    decisions: new Map(data.decisions.map((decision) => [decision.id, decision])),
```

**with**:

```js
    decisions: new Map(data.decisions.map((decision) => [decision.id, decision])),
    contracts: new Map(data.contracts.map((contract) => [contract.id, contract])),
    holes: new Map(data.holes.map((hole) => [hole.id, hole])),
```

- [ ] **Step 4: run the task's tests, the documents that read `documentBase`, and the safety tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_changes.py tests/scripts/test_architecture_docs_area.py tests/scripts/test_architecture_docs_documents.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (56 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/change.mjs skills/shared/scripts/architecture-docs/facts.mjs tests/scripts/test_architecture_docs_changes.py
git commit -m "feat(#34): the change record: summary and approval, diagram, what changed, choices not taken, known-gap pairs, check"
```

---

### Task 5: the improvement list

**Tier:** standard — complete code given; one new module.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/improvements.mjs`
- Test: `tests/scripts/test_architecture_docs_changes.py`

**Callers that move with this task:** none

**Reviewer looks at:**
1. The cycle group matched loosely — mutation: in `improvements.mjs`, replace `sortedGap.filter((entry) => entry.reason === CYCLE)` with `sortedGap.filter((entry) => entry.reason.startsWith('cycle') || entry.reason.startsWith('between'))` — killed by: `test_improvement_list_groups_in_order_with_counts`
2. `partly-built` dropped — mutation: replace `const NOT_BUILT = ['partly-built', 'planned'];` with `const NOT_BUILT = ['planned'];` — killed by: `test_improvement_list_statuses_and_records_with_no_area`
3. `superseded` counted as not built — mutation: replace the same line with `const NOT_BUILT = ['partly-built', 'planned', 'superseded'];` — killed by: `test_improvement_list_statuses_and_records_with_no_area`
4. Coverage edge nodes ignored — mutation: replace `\n    && !edges.has(element.id));` with `);` — killed by: `test_improvement_list_with_a_coverage_file`
5. External elements kept — mutation: delete ` && element.kind !== 'external'` — killed by: `test_elements_that_own_nothing`
6. Parents kept — mutation: delete ` && !parents.has(element.id)` — killed by: `test_elements_that_own_nothing`
7. Code ignored — mutation: delete `element.code.length === 0 && ` — killed by: `test_elements_that_own_nothing`
8. A known-gap entry's areas from its source only — mutation: replace `areasOf([entry.from, entry.to], ctx.byElement)` with `areasOf([entry.from], ctx.byElement)` — killed by: `test_improvement_list_items`
9. A cycle item without its reason — mutation: replace `  const details = [[entry.reason]];` with `  const details = entry.reason === 'cycle in current code' ? [] : [[entry.reason]];` — killed by: `test_improvement_list_items`
10. Unmapped entries unsorted — mutation: replace `[...(data.coverage?.unmapped ?? [])].sort((x, y) => cmp(x.module, y.module))` with `[...(data.coverage?.unmapped ?? [])]` — killed by: `test_improvement_list_with_a_coverage_file`
11. Known-gap entries unsorted — mutation: replace `const sortedGap = [...gap].sort(byPair);` with `const sortedGap = [...gap];` — killed by: `test_improvement_list_sorts_items`
12. An item with no area without its note — mutation: replace `: ['Not in any area']` with `: []` — killed by: `test_improvement_list_items`
13. An empty group not marked — mutation: replace `entries.length === 0 ? paragraph('None.') : list(entries)` with `list(entries)` — killed by: `test_improvement_list_items`
14. An open question's bound elements dropped — mutation: replace `hole.binds.length > 0 ? [['binds ', ...elementLinks(hole.binds, ctx)]] : []` with `[]` — killed by: `test_improvement_list_items`
15. The no-reason group matched loosely — mutation: replace `decision.reason === null)` with `!decision.reason || decision.status === 'planned')` — killed by: `test_improvement_list_items`
16. An unmapped item given an areas part — mutation: replace `item([entry.module], [[entry.reason]], null, ctx)` with `item([entry.module], [[entry.reason]], [], ctx)` — killed by: `test_improvement_list_with_a_coverage_file`

- Satisfies Spec AC: AC-23 (in the module: the eight groups in order, each with its count and its item; with no coverage file, group 6 is empty and group 8 has no edge nodes); Improvement list as amended (`8473868`; a cycle item shows its reason)
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**Append to** `tests/scripts/test_architecture_docs_changes.py`:

```python


def improvements(data: dict = RECORDS, gap: list = GAP) -> dict:
    return built("improvements.mjs", "m.buildImprovements(data, gap, base)", data, gap)


def items(document: dict, heading: str) -> list:
    blocks = section(document, heading)
    assert len(blocks) == 1
    return blocks[0]["items"] if blocks[0]["type"] == "list" else blocks


FRONT = ["Areas: ", L("front", "areas/front.md"), " (Front)"]
MONEY = ["Areas: ", L("money", "areas/money.md"), " (Money)"]
NOWHERE = ["Not in any area"]
COVERAGE = {"answer": "Most code is mapped.", "baselined": [], "edge_nodes": [{"element": "bank", "run": "baseline"}],
            "counts": {"modules": 9, "groups": 2},
            "unmapped": [{"module": "src/z", "reason": "new code"}, {"module": "src/a", "reason": "generated"}]}


def test_improvement_list_groups_in_order_with_counts() -> None:  # Improvement list (amended): `<group name> (<count>)`; AC-23
    document = improvements()
    assert document["title"] == "Improvement list"
    assert document["blocks"][0] == para("Facts from the architecture model and the known-gap file; nothing here is judged or ranked.")
    assert heads(document, 2) == [
        "Cycles in current code (1)", "Other known breaches (1)", "Open questions (1)", "Decisions not yet fully built (1)",
        "Decisions with no known reason (1)", "Unmapped code (0)", "Elements in no area (2)", "Elements that own nothing (5)"]


def test_improvement_list_items() -> None:  # Improvement list (amended): each item, its details and its areas; AC-23
    document = improvements()
    assert items(document, "Cycles in current code (1)") == [
        [L("shop.api", "areas/front.md"), " (API)", " -> ", L("ledger", "README.md"), " (Ledger)", ": ", "cycle in current code", "; ", "close by 2027-01", ". ", *FRONT]]
    assert items(document, "Other known breaches (1)") == [
        [L("bank", "README.md"), " (Bank)", " -> ", L("pay", "areas/money.md"), " (Pay)", ": ", "between neighbours", ". ", *MONEY]]
    assert items(document, "Open questions (1)") == [
        [L("H-1", "areas/front.md"), ": ", "binds ", L("shop.api", "areas/front.md"), " (API)", ". ", *FRONT]]
    assert items(document, "Decisions not yet fully built (1)") == [[L("D-2", "areas/front.md"), ": ", "status ", "planned", ". ", *FRONT]]
    assert items(document, "Decisions with no known reason (1)") == [[L("D-0", "areas/front.md"), ". ", *FRONT]]
    assert items(document, "Unmapped code (0)") == [para("None.")]
    assert items(document, "Elements in no area (2)") == [
        [L("bank", "README.md"), " (Bank)", ". ", *NOWHERE], [L("ledger", "README.md"), " (Ledger)", ". ", *NOWHERE]]
    assert [item[0]["text"] for item in items(document, "Elements that own nothing (5)")] == [
        "bank", "ledger", "pay.gateway", "shop.api.orders", "shop.web"]
    assert items(document, "Elements that own nothing (5)")[2] == [L("pay.gateway", "areas/money.md"), " (Gateway)", ". ", *MONEY]


def test_improvement_list_with_a_coverage_file() -> None:  # Improvement list: unmapped entries by module; edge nodes own something
    document = improvements({**RECORDS, "coverage": COVERAGE})
    assert items(document, "Unmapped code (2)") == [["src/a", ": ", "generated"], ["src/z", ": ", "new code"]]
    assert [item[0]["text"] for item in items(document, "Elements that own nothing (4)")] == [
        "ledger", "pay.gateway", "shop.api.orders", "shop.web"]


def test_elements_that_own_nothing() -> None:  # Improvement list: no code, no child, kind not external, not an edge node
    data = copy.deepcopy(RECORDS)
    data["elements"] = [element("a", "A", kind="external"), element("b", "B", code=["src/b"]), element("c", "C"), element("c.d", "D"),
                        element("e", "E", kind="system")]
    data["areas"] = []
    document = improvements(data, [])
    assert [item[0]["text"] for item in items(document, "Elements that own nothing (2)")] == ["c.d", "e"]


def test_improvement_list_sorts_items() -> None:  # Improvement list: items sorted by id, by pair or by module
    data = copy.deepcopy(RECORDS)
    data["decisions"] = [dict(data["decisions"][2], id=id_) for id_ in ("D-9", "D-10", "D-3")]
    data["holes"] = [dict(data["holes"][0], id=id_) for id_ in ("H-3", "H-10")]
    gap = [{"from": "shop.web", "to": "bank", "reason": "r", "close_by": None}, {"from": "bank", "to": "shop.web", "reason": "r", "close_by": None},
           {"from": "bank", "to": "pay", "reason": "r", "close_by": None}]
    data["coverage"] = {**COVERAGE, "unmapped": [{"module": "b", "reason": "r"}, {"module": "B", "reason": "r"}, {"module": "a", "reason": "r"}]}
    document = improvements(data, gap)
    assert [item[0]["text"] for item in items(document, "Decisions not yet fully built (3)")] == ["D-10", "D-3", "D-9"]
    assert [item[0]["text"] for item in items(document, "Open questions (2)")] == ["H-10", "H-3"]
    assert [(item[0]["text"], item[3]["text"]) for item in items(document, "Other known breaches (3)")] == [
        ("bank", "pay"), ("bank", "shop.web"), ("shop.web", "bank")]
    assert [item[0] for item in items(document, "Unmapped code (3)")] == ["B", "a", "b"]


def test_improvement_list_statuses_and_records_with_no_area() -> None:  # Improvement list: partly-built and planned; no area
    data = copy.deepcopy(RECORDS)
    data["decisions"] = [dict(data["decisions"][0], id="D-5", status="partly-built", binds=[], reason="R."),
                         dict(data["decisions"][0], id="D-6", status="superseded", superseded_by="D-5", reason="R."),
                         dict(data["decisions"][3], reason=None)]
    data["holes"] = [dict(data["holes"][0], binds=[])]
    document = improvements(data, [])
    assert items(document, "Decisions not yet fully built (1)") == [[L("D-5", "README.md"), ": ", "status ", "partly-built", ". ", *NOWHERE]]
    assert items(document, "Decisions with no known reason (1)") == [[L("P-1", "README.md"), ". ", *NOWHERE]]
    assert items(document, "Open questions (1)") == [[L("H-1", "README.md"), ". ", *NOWHERE]]
    assert items(document, "Cycles in current code (0)") == [para("None.")]
    assert items(document, "Other known breaches (0)") == [para("None.")]
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_changes.py`
Expected: FAIL, 6 failed, 15 passed (`improvements.mjs` does not exist).

- [ ] **Step 3: GREEN.**

**Create** `skills/shared/scripts/architecture-docs/improvements.mjs`:

```js
// The improvement list (spec, What each document holds, Improvement list): facts only, nothing judged or ranked, in
// eight fixed groups, each a heading with its count and its items sorted by id, by pair or by module.
import { cmp } from '../architecture-delta/report.mjs';
import { doc, heading, paragraph, list, docLink } from './tree.mjs';
import { IMPROVEMENTS, areasOf, recordElements, recordTarget, relative } from './facts.mjs';
import { elementLinks, areaLinks } from './records-doc.mjs';

export const IMPROVEMENTS_TITLE = 'Improvement list';
const CYCLE = 'cycle in current code';
const NOT_BUILT = ['partly-built', 'planned'];

const byId = (x, y) => cmp(x.id, y.id);
const byPair = (x, y) => cmp(x.from, y.from) || cmp(x.to, y.to);
const parentOf = (id) => id.slice(0, id.lastIndexOf('.'));

// Spec (amended): an item names its id, pair or module, then its details after `: `, separated by `; `, then its areas,
// or "Not in any area"; `areas` is null for an unmapped module, which has no areas part.
function item(main, details, areas, ctx) {
  const parts = [...main];
  details.forEach((detail, at) => parts.push(at === 0 ? ': ' : '; ', ...detail));
  if (areas !== null) parts.push('. ', ...(areas.length > 0 ? ['Areas: ', ...areaLinks(areas, ctx)] : ['Not in any area']));
  return parts;
}

function gapItem(entry, ctx) {
  const details = [[entry.reason]];
  if (entry.close_by !== null) details.push([`close by ${entry.close_by}`]);
  const main = [...elementLinks([entry.from], ctx), ' -> ', ...elementLinks([entry.to], ctx)];
  return item(main, details, areasOf([entry.from, entry.to], ctx.byElement), ctx);
}

function recordItem(kind, record, details, ctx) {
  const main = [docLink(record.id, relative(ctx.doc, recordTarget(kind, record, ctx.byElement)))];
  return item(main, details, areasOf(recordElements(kind, record), ctx.byElement), ctx);
}

const elementItem = (element, ctx) => item(elementLinks([element.id], ctx), [], ctx.byElement.get(element.id) ?? [], ctx);

// Spec, group 8: no `code`, no child, kind not `external`, and not a coverage edge node.
function ownsNothing(data) {
  const parents = new Set(data.elements.filter((element) => element.id.includes('.')).map((element) => parentOf(element.id)));
  const edges = new Set((data.coverage?.edge_nodes ?? []).map((node) => node.element));
  return data.elements.filter((element) => element.code.length === 0 && !parents.has(element.id) && element.kind !== 'external'
    && !edges.has(element.id));
}

export function buildImprovements(data, gap, base) {
  const ctx = { ...base, doc: IMPROVEMENTS, area: null };
  const sortedGap = [...gap].sort(byPair);
  const decisions = [...data.decisions].sort(byId);
  const groups = [
    ['Cycles in current code', sortedGap.filter((entry) => entry.reason === CYCLE).map((entry) => gapItem(entry, ctx))],
    ['Other known breaches', sortedGap.filter((entry) => entry.reason !== CYCLE).map((entry) => gapItem(entry, ctx))],
    ['Open questions', [...data.holes].sort(byId).map((hole) =>
      recordItem('holes', hole, hole.binds.length > 0 ? [['binds ', ...elementLinks(hole.binds, ctx)]] : [], ctx))],
    ['Decisions not yet fully built', decisions.filter((decision) => NOT_BUILT.includes(decision.status))
      .map((decision) => recordItem('decisions', decision, [['status ', decision.status]], ctx))],
    ['Decisions with no known reason', decisions.filter((decision) => decision.reason === null)
      .map((decision) => recordItem('decisions', decision, [], ctx))],
    ['Unmapped code', [...(data.coverage?.unmapped ?? [])].sort((x, y) => cmp(x.module, y.module))
      .map((entry) => item([entry.module], [[entry.reason]], null, ctx))],
    ['Elements in no area', [...data.elements].sort(byId).filter((element) => (ctx.byElement.get(element.id) ?? []).length === 0)
      .map((element) => elementItem(element, ctx))],
    ['Elements that own nothing', ownsNothing(data).sort(byId).map((element) => elementItem(element, ctx))],
  ];
  const blocks = [paragraph('Facts from the architecture model and the known-gap file; nothing here is judged or ranked.')];
  for (const [name, entries] of groups) {
    blocks.push(heading(2, `${name} (${entries.length})`), entries.length === 0 ? paragraph('None.') : list(entries));
  }
  return doc(IMPROVEMENTS_TITLE, blocks);
}
```

- [ ] **Step 4: run the task's tests and the safety tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_changes.py tests/scripts/test_architecture_docs_safety.py`
Expected: PASS (25 passed).

- [ ] **Step 5: refactor.** None expected; rerun Step 4 if anything changed.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-docs/improvements.mjs tests/scripts/test_architecture_docs_changes.py
git commit -m "feat(#34): the improvement list: eight groups in order, each with its count; items sorted, with details and areas"
```

---

### Task 6: `build` and `check` write and compare the change records and the improvement list

**Tier:** strong — the task that carries change-file, record, coverage and known-gap text into every new Markdown and HTML file, and names output paths after change ids (trust boundary); complete code is given, but the tier stays strong for that boundary.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/build.mjs`
- Test: `tests/scripts/test_architecture_docs_documents.py`, `tests/scripts/test_architecture_docs_tool.py`

**Callers that move with this task:** sweep rows `test_architecture_docs_tool.py:32`, `:47`, `:54`, `:56`, `:57`, `:156`; `test_architecture_docs_documents.py:224` and `:276-282`

**Reviewer looks at:**
1. Change records not built — mutation: in `build.mjs`, replace `  for (const change of data.changes) {` with `  for (const change of []) {` — killed by: `test_build_writes_change_records`
2. Every record built from the first change file — mutation: replace `buildChange(data, gap, change, base)` with `buildChange(data, gap, data.changes[0], base)` — killed by: `test_build_writes_one_record_per_change_file`
3. Change records drawn without the known gap — mutation: replace `buildChange(data, gap, change, base)` with `buildChange(data, [], change, base)` — killed by: `test_build_writes_change_records` (its red known-gap arrow)
4. The improvement list not built — mutation: delete the line `  addDocument(files, IMPROVEMENTS, buildImprovements(data, gap, base));` — killed by: `test_build_writes_the_improvement_list`
5. No deadline check after a change record — mutation: delete the `tick();` after `addDocument(files, changeDoc(change.id), ...)` — killed by: `test_build_checks_the_deadline_after_each_document`
6. No deadline check after the improvement list — mutation: delete the `tick();` after the improvement list's `addDocument` — killed by: `test_build_checks_the_deadline_after_each_document`
7. The improvement list without the known gap — mutation: replace `buildImprovements(data, gap, base)` with `buildImprovements(data, [], base)` — killed by: `test_build_improvement_list_with_one_item_of_each_kind`

**Pinned by:** the whole set stays deterministic and `check` agrees, with and without a change file: `tests/scripts/test_architecture_docs_tool.py::test_build_is_deterministic_and_check_agrees` (no change file) and the new `test_build_with_a_change_file_is_deterministic_and_check_agrees` build twice, compare every file byte for byte, and assert `check` prints `0 missing, 0 changed, 0 extra` (AC-8).

- Satisfies Spec AC: AC-22 and AC-23 through `build` (one item of each improvement kind, with a coverage file); AC-8 (with a change file); AC-9 (a removed change file's two files `extra`, the overview `changed`; a removed area changes the improvement list); AC-12 (change records, the improvement list, coverage text, ids not in the model); AC-13 (the full policy, scripts and marker line on the new pages); AC-17 (the `changes` folder emptied and removed); the threat model's `--timeout` check after each document
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: write RED tests.**

**In** `tests/scripts/test_architecture_docs_documents.py` **replace**:

```python

import json
```

**with**:

```python

import base64
import hashlib
import json
```

**In** `tests/scripts/test_architecture_docs_documents.py` **replace**:

```python
LEDGER = "Ledger#59; #34;x#34; #37;#37;#123;init#125;#37;#37; #40;no area#41;"
```

**with**:

```python
LEDGER = "Ledger#59; #34;x#34; #37;#37;#123;init#125;#37;#37; #40;no area#41;"


def change_file(**over) -> dict:
    lists = {"added": [], "changed": [], "removed": []}
    record = {"id": "2026-11-05-more", "date": "2026-11-05", "run": "later-stage", "asked_by": "#1", "summary": "More.", "rejected": [],
              "elements": lists, "decisions": lists, "holes": lists, "contracts": lists, "gap": {"added": [], "removed": []},
              "check": {"exit": 0, "summary": "ok", "output": "ok\n"}, "approved": None}
    record.update(over)
    return record
```

**In** `tests/scripts/test_architecture_docs_documents.py` **replace**:

```python
    for line in ("extra areas/money.md", "extra areas/money.html", "extra pack/areas/money.md", "changed README.md"):
```

**with**:

```python
    for line in ("extra areas/money.md", "extra areas/money.html", "extra pack/areas/money.md", "changed README.md",
                 "changed improvements.md"):
```

**In** `tests/scripts/test_architecture_docs_documents.py` **replace**:

```python
def test_build_checks_the_deadline_after_each_area_and_capability_document(tmp_path) -> None:  # Threat model: --timeout
```

**with**:

```python
def test_build_checks_the_deadline_after_each_document(tmp_path) -> None:  # Threat model: --timeout
```

**In** `tests/scripts/test_architecture_docs_documents.py` **replace**:

```python
    repo = make_repo(tmp_path, MODEL)
```

**with**:

```python
    repo = make_repo(tmp_path, MODEL)
    write_json(repo / "docs" / "architecture", "changes/2026-11-05-more.json", change_file())
```

**In** `tests/scripts/test_architecture_docs_documents.py` **replace**:

```python
    assert proc.stderr.splitlines()[-1] == "ticks 6"  # model.json, the overview, three areas and one capability
```

**with**:

`````python
    # model.json, the overview, three areas, one capability, one change record and the improvement list
    assert proc.stderr.splitlines()[-1] == "ticks 8"


MORE = change_file(rejected=["A monolith."], elements={"added": ["shop.web", "shop.cart"], "changed": [], "removed": []},
                   decisions={"added": [], "changed": ["D-2"], "removed": []}, contracts={"added": [], "changed": [], "removed": ["C-9"]},
                   gap={"added": [["shop.web", "pay.gateway"]], "removed": [["shop.cart", "bank"]]})


def built_with_change(tmp_path: Path, record: dict = MORE) -> tuple[Path, Path]:
    repo = make_repo(tmp_path, MODEL)
    folder = repo / "docs" / "architecture"
    decisions = json.loads(json.dumps(DECISIONS))
    decisions["decisions"][1]["rejected"] = ["Two APIs."]
    write_json(folder, "decisions/core.json", decisions)
    write_json(folder, "contracts/edge.json", CONTRACTS)
    write_json(folder, "known-gap.json", GAP)
    write_json(folder, f"changes/{record['id']}.json", record)
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    return repo, folder / "generated"


def test_build_writes_change_records(tmp_path) -> None:  # AC-22, AC-13 (change record pages)
    _, out = built_with_change(tmp_path)
    text = (out / "changes" / "2026-11-05-more.md").read_text(encoding="utf-8")
    assert text.startswith(MARKER + "\n\n# 2026\\-11\\-05\\-more\n\n- Summary: More\\.\n- Asked by: \\#1\n")
    assert "\n- Approval: Not yet approved\n" in text
    frame = re.search(r'```mermaid\nflowchart LR\n  subgraph frame\["2026-11-05-more"\]\n(.*?)\n  end\n', text, re.S).group(1)
    assert frame == '    n4["Web #40;added#41;"]'
    assert ("Web #40;added#41;", "-->", "known gap", "Gateway #40;core#41;", "red") in diagram_arrows(text)
    assert "\n### Elements added\n\n| Element | Title |" in text and "| [shop\\.web](../areas/front.md) | Web |" in text
    assert "\n- shop\\.cart \\(not in the current model\\)\n" in text
    assert "\n### Decisions changed\n\n#### D\\-2\n\nDecide D\\-2\\.\n" in text
    assert "\n### Contracts removed\n\n- C\\-9\n" in text
    assert "\n## Choices not taken\n\n- A monolith\\.\n- [D\\-2](../areas/front.md): Two APIs\\.\n" in text
    assert ("\n## Known gap\n\n- Added: [shop\\.web](../areas/front.md) \\(Web\\) \\-&gt; [pay\\.gateway](../areas/core.md) \\(Gateway\\)\n"
            "- Removed: shop\\.cart \\(not in the current model\\) \\-&gt; [bank](../README.md) \\(Bank\\)\n") in text
    assert text.endswith("\n## Check\n\n- Exit: 0\n- Summary: ok\n\n```\nok\n```\n")
    page = (out / "changes" / "2026-11-05-more.html").read_text(encoding="utf-8")
    assert page.startswith(MARKER + "\n") and page.count("<script") == 2
    assert "content=\"default-src 'none'; script-src https://cdn.jsdelivr.net/npm/mermaid@12.2.0" in page
    assert '<a href="../areas/front.html">D-2</a>' in page
    assert "[2026\\-11\\-05\\-more](changes/2026-11-05-more.md)" in (out / "README.md").read_text(encoding="utf-8")


def test_build_writes_the_improvement_list(tmp_path) -> None:  # AC-23 (through build), AC-13 (its page)
    _, out = built_with_change(tmp_path)
    text = (out / "improvements.md").read_text(encoding="utf-8")
    assert text.startswith(MARKER + "\n\n# Improvement list\n\n")
    assert re.findall(r"^## (.*)$", text, re.M) == [
        "Cycles in current code \\(0\\)", "Other known breaches \\(2\\)", "Open questions \\(1\\)", "Decisions not yet fully built \\(0\\)",
        "Decisions with no known reason \\(0\\)", "Unmapped code \\(0\\)", "Elements in no area \\(2\\)", "Elements that own nothing \\(5\\)"]
    assert ("- [shop\\.web](areas/front.md) \\(Web\\) \\-&gt; [pay\\.gateway](areas/core.md) \\(Gateway\\): no relationship\\. "
            "Areas: [core](areas/core.md) \\(Core\\), [front](areas/front.md) \\(Front\\), [money](areas/money.md) \\(Money\\)\n") in text
    assert "- [H\\-1](areas/front.md): binds [shop\\.api](areas/front.md) \\(API\\)\\. Areas: [front](areas/front.md) \\(Front\\)\n" in text
    assert "\n## Unmapped code \\(0\\)\n\nNone\\.\n" in text
    assert "- [bank](README.md) \\(Bank\\)\\. Not in any area\n" in text
    page = (out / "improvements.html").read_text(encoding="utf-8")
    assert page.startswith(MARKER + "\n") and page.count("<script") == 2
    assert '<a href="areas/front.html">H-1</a>' in page
    assert "[the improvement list](improvements.md)" in (out / "README.md").read_text(encoding="utf-8")


def test_build_escapes_hostile_change_and_improvement_text(tmp_path) -> None:  # AC-12 (change records, improvement list)
    hostile = change_file(summary="More [x](javascript:alert(1)) <script> | %%{init}%% " + ESC + "[31m",
                          elements={"added": ["ledger"], "changed": [], "removed": []},
                          rejected=["No <b>bold</b> | ```"], check={"exit": 1, "summary": "Bad " + ESC + "[0m", "output": "Out\n```\n" + ESC + "[31mred\n"})
    _, out = built_with_change(tmp_path, hostile)
    for name in files(out):
        assert ESC not in (out / name).read_text(encoding="utf-8"), name
    text = (out / "changes" / "2026-11-05-more.md").read_text(encoding="utf-8")
    assert "- Summary: More \\[x\\]\\(javascript:alert\\(1\\)\\) &lt;script&gt; \\| %%\\{init\\}%% \n" in text
    assert "- No &lt;b&gt;bold&lt;/b&gt; \\| \\`\\`\\`\n" in text
    assert text.endswith("\n````\nOut\n```\nred\n````\n")
    diagram = re.search(r"```mermaid\n(.*?)\n```", text, re.S).group(1)
    assert '["' + LEDGER.replace("#40;no area#41;", "#40;added#41;") + '"]' in diagram
    assert "%%" not in diagram and ";" not in re.sub(r"#\d+;", "", diagram.replace("\n", " "))
    page = (out / "changes" / "2026-11-05-more.html").read_text(encoding="utf-8")
    assert "<b>" not in page and "&lt;b&gt;bold" in page and page.count("<script") == 2
    improvements = (out / "improvements.md").read_text(encoding="utf-8")
    assert "Red gap \\| &lt;b&gt;; close by 2027 01\\." in improvements
    assert "<b>" not in (out / "improvements.html").read_text(encoding="utf-8")


def test_check_reports_a_removed_change_file(tmp_path) -> None:  # AC-9 (a change record), AC-17 (the changes folder)
    repo, out = built_with_change(tmp_path)
    (repo / "docs" / "architecture" / "changes" / "2026-11-05-more.json").unlink()
    check = run_tool("check", "--repo", repo, script=DOCS_SCRIPT)
    assert check.returncode == 1
    lines = check.stdout.splitlines()
    for line in ("extra changes/2026-11-05-more.html", "extra changes/2026-11-05-more.md", "changed README.md", "changed index.html"):
        assert line in lines
    assert [line for line in lines if line.startswith("extra ")] == ["extra changes/2026-11-05-more.html", "extra changes/2026-11-05-more.md"]
    assert run_tool("build", "--repo", repo, script=DOCS_SCRIPT).returncode == 0
    assert not (out / "changes").exists()
    assert run_tool("check", "--repo", repo, script=DOCS_SCRIPT).returncode == 0



def test_build_writes_one_record_per_change_file(tmp_path) -> None:  # Change record: one per change file, each its own
    repo, out = built_with_change(tmp_path)
    later = change_file(id="2026-11-07-later", date="2026-11-07", summary="Later.")
    write_json(repo / "docs" / "architecture", "changes/2026-11-07-later.json", later)
    assert run_tool("build", "--repo", repo, script=DOCS_SCRIPT).returncode == 0
    assert files(out, "changes/*") == ["changes/2026-11-05-more.html", "changes/2026-11-05-more.md",
                                       "changes/2026-11-07-later.html", "changes/2026-11-07-later.md"]
    assert "\n- Summary: More\\.\n" in (out / "changes" / "2026-11-05-more.md").read_text(encoding="utf-8")
    assert "\n- Summary: Later\\.\n" in (out / "changes" / "2026-11-07-later.md").read_text(encoding="utf-8")
    assert "# 2026\\-11\\-07\\-later\n" in (out / "changes" / "2026-11-07-later.md").read_text(encoding="utf-8")


def test_build_with_a_change_file_is_deterministic_and_check_agrees(tmp_path) -> None:  # AC-8 (change records, improvement list)
    repo, out = built_with_change(tmp_path)
    first = {name: (out / name).read_bytes() for name in files(out)}
    assert run_tool("build", "--repo", repo, script=DOCS_SCRIPT).returncode == 0
    assert {name: (out / name).read_bytes() for name in files(out)} == first
    check = run_tool("check", "--repo", repo, script=DOCS_SCRIPT)
    assert (check.returncode, check.stdout) == (0, "0 missing, 0 changed, 0 extra\n")


def test_build_escapes_hostile_coverage_and_ids_not_in_the_model(tmp_path) -> None:  # AC-12 (coverage text, gone ids)
    hostile_id = "x](javascript:alert(1)) <script> | %%{init}%%"
    record = change_file(elements={"added": [hostile_id], "changed": [], "removed": [hostile_id]},
                         gap={"added": [[hostile_id, "bank"]], "removed": []})
    repo, out = built_with_change(tmp_path, record)
    write_json(repo / "docs" / "architecture", "coverage.json", {
        "answer": "A.", "baselined": [], "edge_nodes": [], "counts": {"modules": 1, "groups": 1},
        "unmapped": [{"module": "src/[x](javascript:alert(1))", "reason": "<b>bad</b> | " + ESC + "[31m"}]})
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    change = (out / "changes" / "2026-11-05-more.md").read_text(encoding="utf-8")
    escaped = "x\\]\\(javascript:alert\\(1\\)\\) &lt;script&gt; \\| %%\\{init\\}%%"
    assert f"\n- {escaped} \\(not in the current model\\)\n" in change
    assert f"\n- Added: {escaped} \\(not in the current model\\) \\-&gt; [bank](../README.md) \\(Bank\\)\n" in change
    assert "](javascript" not in change and "<script>" not in change
    improvements = (out / "improvements.md").read_text(encoding="utf-8")
    assert "\n- src/\\[x\\]\\(javascript:alert\\(1\\)\\): &lt;b&gt;bad&lt;/b&gt; \\|" in improvements
    assert "](javascript" not in improvements and "<b>" not in improvements and ESC not in improvements
    for name in ("changes/2026-11-05-more.html", "improvements.html"):
        page = (out / name).read_text(encoding="utf-8")
        assert "<b>" not in page and "<script>alert" not in page and page.count("<script") == 2, name


def test_build_improvement_list_with_one_item_of_each_kind(tmp_path) -> None:  # AC-23 (through build, with a coverage file)
    repo = make_repo(tmp_path, MODEL)
    folder = repo / "docs" / "architecture"
    decisions = json.loads(json.dumps(DECISIONS))
    decisions["decisions"][2:2] = [decision("D-3", binds=["shop.api"], status="planned"), decision("D-4", binds=["bank"], reason=None)]
    write_json(folder, "decisions/core.json", decisions)
    write_json(folder, "known-gap.json", {"entries": GAP["entries"] + [{"from": "bank", "to": "pay", "reason": "cycle in current code"}]})
    write_json(folder, "changes/2026-11-05-more.json", change_file())
    write_json(folder, "coverage.json", {"answer": "A.", "baselined": [], "edge_nodes": [{"element": "bank", "run": "2026-11-05-more"}],
                                         "counts": {"modules": 1, "groups": 1}, "unmapped": [{"module": "src/z", "reason": "new code"}]})
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    text = (folder / "generated" / "improvements.md").read_text(encoding="utf-8")
    assert re.findall(r"^## (.*)$", text, re.M) == [
        "Cycles in current code \\(1\\)", "Other known breaches \\(2\\)", "Open questions \\(1\\)", "Decisions not yet fully built \\(1\\)",
        "Decisions with no known reason \\(1\\)", "Unmapped code \\(1\\)", "Elements in no area \\(2\\)", "Elements that own nothing \\(4\\)"]
    assert ("\n- [bank](README.md) \\(Bank\\) \\-&gt; [pay](areas/core.md) \\(Pay\\): cycle in current code\\. "
            "Areas: [core](areas/core.md) \\(Core\\)\n") in text
    assert "\n- [D\\-3](areas/front.md): status planned\\. Areas: [front](areas/front.md) \\(Front\\)\n" in text
    assert "\n- [D\\-4](README.md)\\. Not in any area\n" in text
    assert "\n- src/z: new code\n" in text
    assert "[bank]" not in text.split("## Elements that own nothing")[1]


def test_new_pages_carry_the_full_policy(tmp_path) -> None:  # AC-13 (change record and improvement list pages)
    _, out = built_with_change(tmp_path)
    script = "mermaid.initialize({ startOnLoad: true, securityLevel: 'strict' });"
    digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
    url = "https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js"
    policy = f"default-src 'none'; script-src {url} 'sha256-{digest}'; style-src 'unsafe-inline'; img-src data:"
    for name in ("changes/2026-11-05-more.html", "improvements.html"):
        lines = (out / name).read_text(encoding="utf-8").split("\n")
        assert lines[0] == MARKER, name
        assert f'<meta http-equiv="Content-Security-Policy" content="{policy}">' in lines, name
        assert (f'<script src="{url}" integrity="sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp" '
                'crossorigin="anonymous"></script>') in lines, name
        assert f"<script>{script}</script>" in lines and sum(line.count("<script") for line in lines) == 2, name
`````

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_docs_documents.py`
Expected: FAIL, 10 failed, 8 passed (no change record or improvement list is written; the removed-area test now also expects `changed improvements.md`; the AC-8 test with a change file passes already and guards the GREEN step).

- [ ] **Step 3: GREEN.**

**In** `skills/shared/scripts/architecture-docs/build.mjs` **replace**:

```js
import { areaDoc, capabilityDoc, documentBase } from './facts.mjs';
```

**with**:

```js
import { IMPROVEMENTS, areaDoc, capabilityDoc, changeDoc, documentBase } from './facts.mjs';
```

**In** `skills/shared/scripts/architecture-docs/build.mjs` **replace**:

```js
import { buildCapability } from './capability.mjs';
```

**with**:

```js
import { buildCapability } from './capability.mjs';
import { buildChange } from './change.mjs';
import { buildImprovements } from './improvements.mjs';
```

**In** `skills/shared/scripts/architecture-docs/build.mjs` **replace**:

```js
  }
  return files;
```

**with**:

```js
  }
  for (const change of data.changes) {
    addDocument(files, changeDoc(change.id), buildChange(data, gap, change, base));
    tick();
  }
  addDocument(files, IMPROVEMENTS, buildImprovements(data, gap, base));
  tick();
  return files;
```

- [ ] **Step 4: move the callers.**

**In** `tests/scripts/test_architecture_docs_tool.py` **replace**:

```python
    assert (first.returncode, first.stdout) == (0, "wrote 4 files, removed 0\n"), first.stderr
```

**with**:

```python
    assert (first.returncode, first.stdout) == (0, "wrote 6 files, removed 0\n"), first.stderr
```

**In** `tests/scripts/test_architecture_docs_tool.py` **replace**:

```python
    assert (missing.returncode, missing.stdout) == (1, "missing README.md\nmissing index.html\nmissing pack/README.md\nmissing pack/model.json\n4 missing, 0 changed, 0 extra\n")
```

**with**:

```python
    assert (missing.returncode, missing.stdout) == (1, "missing README.md\nmissing improvements.html\nmissing improvements.md\nmissing index.html\nmissing pack/README.md\nmissing pack/model.json\n6 missing, 0 changed, 0 extra\n")
```

**In** `tests/scripts/test_architecture_docs_tool.py` **replace**:

```python
    assert (stale.returncode, stale.stdout) == (1, "changed README.md\nextra areas/old.md\nchanged index.html\nchanged pack/README.md\nchanged pack/model.json\n0 missing, 4 changed, 1 extra\n")
```

**with**:

```python
    assert (stale.returncode, stale.stdout) == (1, "changed README.md\nextra areas/old.md\nchanged improvements.html\nchanged improvements.md\nchanged index.html\nchanged pack/README.md\nchanged pack/model.json\n0 missing, 6 changed, 1 extra\n")
```

**In** `tests/scripts/test_architecture_docs_tool.py` **replace**:

```python
    assert rebuilt.stdout == "wrote 4 files, removed 1\n"
    assert sorted(snapshot(out_of(repo))) == ["README.md", "index.html", "pack/README.md", "pack/model.json"]
```

**with**:

```python
    assert rebuilt.stdout == "wrote 6 files, removed 1\n"
    assert sorted(snapshot(out_of(repo))) == ["README.md", "improvements.html", "improvements.md", "index.html", "pack/README.md", "pack/model.json"]
```

**In** `tests/scripts/test_architecture_docs_tool.py` **replace**:

```python
    assert sorted(snapshot(out_of(repo))) == ["README.md", "index.html", "pack/README.md", "pack/model.json"]
```

**with**:

```python
    assert sorted(snapshot(out_of(repo))) == ["README.md", "improvements.html", "improvements.md", "index.html", "pack/README.md", "pack/model.json"]
```

- [ ] **Step 5: run the full suite.**

Run: `uv run pytest -q`
Expected: PASS (709 passed, 1 skipped).

- [ ] **Step 6: refactor.** None expected; rerun Step 5 if anything changed.

- [ ] **Step 7: commit.**

```bash
git add skills/shared/scripts/architecture-docs/build.mjs tests/scripts/test_architecture_docs_documents.py tests/scripts/test_architecture_docs_tool.py
git commit -m "feat(#34): build and check write and compare the change records and the improvement list"
```

---

## Verification evidence

- Dry run: one scratch copy of main at `637bc43` plus the amendment `8473868`; the code built once there, with the alignment check's fixes as commits on top; full suite 676 passed, 1 skipped before and 709 passed, 1 skipped after.
- Plan blocks: applying this plan's blocks in order to the baseline gives the dry run's final files byte for byte; replaying the tasks in that order in the dry-run copy gave each task's RED and GREEN counts above.
- Mutations: every "Reviewer looks at" item above (45) was applied by exact byte replacement in the dry run and killed by its named test.
- Diagrams: every `mermaid` block of the change records, the area documents and the capability documents built from the Task 6 fixtures (23 blocks, including a hostile title framed and marked) parses under Mermaid 12.2.0; a broken block is refused.
