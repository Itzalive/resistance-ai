# Architecture Model Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The delta tool reads, validates and exports the decision, hole, contract, change and coverage records in a model folder.

**Architecture:** This repository has no architecture model. Two new modules beside the existing ones: `records-shape.mjs` holds the record tables and the shape pass; `records.mjs` reads the folders and runs every pass, returning the records or throwing one `record-error` with every line. The entry script calls `readRecords` right after the model loads, before any other input; `report.mjs` prints the records in `export` (format 3). `errors.mjs` gains `cleanText`, the cleaning without the length cut.

**Tech Stack:** Node ESM (standard library only for the new code), pytest calling the tool and its modules as subprocesses.

**Spec:** `docs/superpowers/specs/2026-11-17-architecture-model-records-design.md` — decisions applied: none (no decision register). AC-5 was corrected while planning: its example put the duplicate line on the wrong file for the spec's own folder order.

**Open decisions:** none

**Size:** 7 tasks, 2 entry paths (`export`, `check`), 702 lines (reported, not a target)

**Trust boundary:** unchanged in kind. The model folder is already read as untrusted input; the record files are new files read from it, printed only through the existing cleaning (`clean`) and the new `cleanText`, and interpreted nowhere else.

### Risk & Confidence Assessment

**Confidence:** 90% — the passes are mechanical once the tables exist; the ordering rules for error lines are the most detailed part of the spec.

**Complexity Risk:** Medium — the error-line order (path, pass, record position, field order, unknown keys last) and "what a shape problem leaves in" interact across five passes.

**Environmental Risk:** Low — Node and `node_modules/likec4` are installed in this worktree; the suite passed (365) before this branch.

**Main failure modes:** error lines in an order the spec does not give (caught by the exact-order tests in Tasks 3 and 4); a reference counted as a duplicate id (caught by `test_references_are_not_ids`); record text cut at 200 characters in `export` (caught by `test_record_text_is_cleaned_without_a_cut`).

**Unknown variables:**
- Whether `fs.readdirSync(..., { withFileTypes: true })` reports a Windows junction inside a record folder as a directory. Not blocking: `walkModelDir` refuses links before records are read (`walk.mjs`).

---

## Messages

Every `record-error` detail is `<path>: <field path>: <message>`. The messages, used by the code and asserted by the tests:

| Problem | Message |
|---|---|
| Misnamed file in a record folder | `not a valid file name here` |
| Folder inside a record folder | `folders are not allowed here` |
| `decisions`, `contracts` or `changes` is a file | `must be a folder` |
| `coverage.json` is a folder | `must be a file` |
| Not valid JSON | `not valid JSON` |
| Not an object | `must be a JSON object` |
| Required field missing | `required` |
| Field not in the tables | `unknown field` |
| Wrong type: text | `must be a non-empty string` |
| Wrong type: text or null | `must be a non-empty string or null` |
| Wrong type: id (record or element) | `must be a string` |
| Wrong type: list | `must be a list` |
| Wrong type: object | `must be an object` |
| Wrong type: object or null | `must be an object or null` |
| Wrong type: count | `must be a whole number of 0 or more` |
| Wrong type: exit | `must be a whole number` |
| Wrong type: gap pair | `must be a pair of two non-empty strings` |
| List needs one item | `needs at least one item` |
| Record id form | `not a valid record id` |
| Duplicate record id | `duplicate id <id>, first in <path>` |
| Change id is not its file name | `must equal the file name <name>` |
| Empty element id | `must not be empty` |
| Element id not in the model | `<id> is not a model element` |
| Reference names no decision | `<id> names no decision` |
| `superseded_by` is the record's own id | `names its own id` |
| Coverage `run` names no change file | `<id> names no change file` |
| Same id twice in one list | `<id> is listed twice` |
| List out of order | `not sorted by id: <id> comes after <previous id>` |
| `superseded_by` with another status | `only allowed when status is superseded` |
| `superseded_by` missing | `required when status is superseded` |
| Value outside its list | `must be one of <values joined by ", ">` |
| Not a real date | `not a real date` |
| Change `date` not the start of its name | `must be the start of the file name` |
| `check.exit` other than 0 or 1 | `must be 0 or 1` |

## Caller and test sweep

Searched: `skills/`, `tests/`, `scripts/` with `grep -rn "exportJson\|loadRepoModel\|readOptional" skills tests --include=*.mjs --include=*.py` and `grep -n "format\|list(data)" tests/scripts/*.py`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `loadRepoModel` returns `records` too | `skills/shared/scripts/architecture-delta.mjs:90` `main` | caller | 5 | none: `loaded` is passed on |
| `exportJson(model)` → `exportJson(model, records)` | `skills/shared/scripts/architecture-delta.mjs:94` | caller | 6 | `exportJson(loaded.model, loaded.records)` |
| `export` shape: format 3, new keys | `tests/scripts/test_architecture_delta_export.py:22` | assert | 6 | `assert list(data) == ["format", "elements", "allowed", "runtime", "groups", "decisions", "holes", "contracts", "changes", "coverage"]` |
| same | `tests/scripts/test_architecture_delta_export.py:23` | assert | 6 | `assert data["format"] == 3` |
| same | `tests/scripts/test_architecture_delta_export.py:44` | assert | 6 | `assert json.loads(proc.stdout) == {"format": 3, "elements": [], "allowed": [], "runtime": [], "groups": [], "decisions": [], "holes": [], "contracts": [], "changes": [], "coverage": None}` |
| same | `tests/scripts/test_architecture_delta_export.py:182` | assert | 6 | `assert json.loads(proc.stdout)["format"] == 3` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py:155` | assert | 6 | `assert list(data)[:4] == ["format", "elements", "allowed", "runtime"]` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py:156` | assert | 6 | `assert data["format"] == 3` |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | Task 1 item 1, Task 2 items 1–3, Task 3 items 1–3; focused tests `uv run pytest -q tests/scripts/test_architecture_delta_records.py tests/scripts/test_architecture_delta_errors.py` |
| C2 | 7 | 4–7 | Task 4 items 1–4, Task 5 items 1–2, Task 6 items 1–2, Task 7 item 1; full suite `uv run pytest -q` (Task 5 changes every run) |

---

### Task 1: `cleanText` cleans without the length cut

**Tier:** fast — complete code.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/errors.mjs`
- Test: `tests/scripts/test_architecture_delta_errors.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- line feeds kept, other controls removed — mutation: use `CONTROLS` (which removes `\n`) in `cleanText` — killed by: `test_clean_text_keeps_line_feeds_and_length`

- Satisfies Spec AC: AC-12 (the cleaning half)
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append to `tests/scripts/test_architecture_delta_errors.py`:

```python
def test_clean_text_keeps_line_feeds_and_length() -> None:
    from arch_delta_support import call
    text = "a" * 300 + "\n" + "\u001b[31mred\u001b[0m" + "\u0007"
    assert call("errors.mjs", "cleanText", text)["value"] == "a" * 300 + "\nred"


def test_clean_text_drops_carriage_returns_and_bidi_controls() -> None:
    from arch_delta_support import call
    assert call("errors.mjs", "cleanText", "x\r\ny‮z\t")["value"] == "x\nyz"


def test_clean_still_cuts_at_200() -> None:
    from arch_delta_support import call
    out = call("errors.mjs", "clean", "a" * 300)["value"]
    assert out == "a" * 199 + "…"
```

- [ ] **Step 2:** Run `uv run pytest -q tests/scripts/test_architecture_delta_errors.py -k clean`. Expected: the two `clean_text` tests FAIL (`cleanText` is not a function); `test_clean_still_cuts_at_200` passes.

- [ ] **Step 3: GREEN.** In `errors.mjs`, after `MAX_POINTS`, add:

```js
const TEXT_CONTROLS = /[\u0000-\u0009\u000b-\u001f\u007f-\u009f‪-‮⁦-⁩]/g;

// Record text: escape sequences and control characters removed, line feeds kept, no length cut.
export function cleanText(value) {
  return String(value).replace(ANSI, '').replace(TEXT_CONTROLS, '');
}
```

- [ ] **Step 4:** Run `uv run pytest -q tests/scripts/test_architecture_delta_errors.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/errors.mjs tests/scripts/test_architecture_delta_errors.py && git commit -m "feat(#31): cleanText for record text"`

### Task 2: the record tables and the shape pass

**Tier:** standard — interface given; the table drives every later pass.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/records-shape.mjs`
- Create: `tests/scripts/test_architecture_delta_records.py`

**Callers that move with this task:** none (new module).

**Interface.** `records-shape.mjs` exports:
- `TABLES`: for each kind (`decisions`, `contracts`, `change`, `coverage`) an ordered list of field specs `{ name, type, required, minOne?, of?, fields?, id? }`. `type` is one of `text`, `textOrNull`, `string` (any string: ids, and `status`, `evidence`, `run` and `date`, whose values are checked in pass 5), `list` (items by `of`), `object` (nested `fields`), `objectOrNull`, `count` (whole number ≥ 0), `exit` (whole number), `pair`. `id` is `'record'` or `'element'` for fields and list items holding ids. The tables follow the spec's Records section field for field and in its order, including `capabilities` (contract, optional list of text) and coverage's `baselined`/`edge_nodes` objects with `run`.
- `shapeProblems(kind, data)`: `data` is a parsed JSON object; returns `[{ field, message }]` for pass 2b in order: by field in table order, recursing into lists by position and into objects by their table, with unknown keys of each object after its table fields in file order. A missing required field gives `required`; an unknown key `unknown field`; a wrong type the message in the Messages table; an empty list with `minOne`, `needs at least one item`. Values of the right type are not checked further here (ids, enums and dates are later passes). Field paths: keys joined with `.`, list items `[i]`.

**Reviewer looks at:**
- unknown keys come after table fields — mutation: report unknown keys first — killed by: `test_shape_orders_unknown_keys_after_table_fields`
- `reason` and `compatibility` accept `null` — mutation: make `textOrNull` reject `null` — killed by: `test_valid_files_have_no_shape_problems`
- `minOne` only where the spec says (`bound`, `obligations`) — mutation: drop `minOne` from `bound` — killed by: `test_shape_reports_types_minimums_and_nested_paths`

- Satisfies Spec AC: AC-8 (shape part)
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_delta_records.py`:

```python
"""Architecture model records: reading, validation and export (issue #31, A3a)."""

from __future__ import annotations

import json
from pathlib import Path

from arch_delta_support import call, make_repo, require_node, run_tool, error_lines

require_node()

SHOP_IDS = ["shop", "shop.checkout", "shop.orders", "shop.orders.api", "shop.payments", "shop.payments.card"]


def decision(id_: str, **over) -> dict:
    record = {"id": id_, "decision": "Use one store.", "reason": "Simpler.", "rejected": [], "binds": ["shop.orders"],
              "status": "current", "evidence": "spec", "sources": ["docs/x.md"]}
    record.update(over)
    return record


def hole(id_: str, **over) -> dict:
    record = {"id": id_, "what": "No reason recorded.", "binds": [], "evidence": "search"}
    record.update(over)
    return record


def contract(id_: str, **over) -> dict:
    record = {"id": id_, "name": "Orders API", "owner": "shop.orders", "bound": ["shop.checkout"],
              "obligations": ["Every order has an id."], "compatibility": None}
    record.update(over)
    return record


def lists() -> dict:
    return {"added": [], "changed": [], "removed": []}


def change(id_: str = "2026-11-16-baseline", **over) -> dict:
    record = {"id": id_, "date": id_[:10], "run": "baseline", "asked_by": "#1", "summary": "Baseline.", "rejected": [],
              "elements": {"added": ["shop"], "changed": [], "removed": []}, "decisions": lists(), "holes": lists(),
              "contracts": lists(), "gap": {"added": [], "removed": []},
              "check": {"exit": 0, "summary": "0 new, 0 stale, 0 known", "output": "0 new, 0 stale, 0 known\n"},
              "approved": None}
    record.update(over)
    return record


def coverage(**over) -> dict:
    record = {"answer": "Whole repository.", "baselined": [{"prefix": "shop", "run": "2026-11-16-baseline"}],
              "edge_nodes": [], "counts": {"modules": 3, "groups": 2}, "unmapped": []}
    record.update(over)
    return record


def dfile(*decisions: dict, holes: tuple = (), title: str = "Orders") -> dict:
    return {"title": title, "decisions": list(decisions), "holes": list(holes)}


def cfile(*contracts: dict, title: str = "Boundaries") -> dict:
    return {"title": title, "contracts": list(contracts)}


def model_folder(tmp_path: Path, files: dict) -> tuple[Path, Path]:
    """A repo with the shop model and the given record files (dict or raw text), keyed by path in the model folder."""
    repo = make_repo(tmp_path)
    folder = repo / "docs" / "architecture"
    for rel, content in files.items():
        target = folder / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
    return repo, folder


def shape(kind: str, data: object) -> list[str]:
    result = call("records-shape.mjs", "shapeProblems", kind, data)
    assert result["ok"], result
    return [f"{p['field']}: {p['message']}" for p in result["value"]]


def test_valid_files_have_no_shape_problems() -> None:
    assert shape("decisions", dfile(decision("D-1"), decision("D-2", reason=None, note="n"), holes=(hole("H-1"),))) == []
    assert shape("contracts", cfile(contract("C-1", notes=["x"], decisions=["D-1"], capabilities=["Pay"]))) == []
    assert shape("change", change(approved={"by": "owner", "date": "2026-11-16"})) == []
    assert shape("coverage", coverage(edge_nodes=[{"element": "shop", "run": "2026-11-16-baseline"}],
                                      unmapped=[{"module": "shop.x", "reason": "shared prefix"}])) == []


def test_shape_orders_unknown_keys_after_table_fields() -> None:  # AC-8
    data = dfile(decision("D-1", colour="red"), decision("D-2"), holes=(hole("H-1", what=["x"]),))
    del data["decisions"][1]["reason"]
    assert shape("decisions", data) == [
        "decisions[0].colour: unknown field",
        "decisions[1].reason: required",
        "holes[0].what: must be a non-empty string",
    ]


def test_shape_reports_types_minimums_and_nested_paths() -> None:
    assert shape("contracts", cfile(contract("C-1", bound=[], obligations=["ok", ""], compatibility=5))) == [
        "contracts[0].bound: needs at least one item",
        "contracts[0].obligations[1]: must be a non-empty string",
        "contracts[0].compatibility: must be a non-empty string or null",
    ]
    assert shape("change", change(gap={"added": [["a"]], "removed": []}, check={"exit": 1.5, "summary": "s", "output": "o"},
                                  approved=7, extra=1)) == [
        "gap.added[0]: must be a pair of two non-empty strings",
        "check.exit: must be a whole number",
        "approved: must be an object or null",
        "extra: unknown field",
    ]
    assert shape("coverage", coverage(counts={"modules": -1, "groups": 2}, baselined=[{"prefix": "shop"}])) == [
        "baselined[0].run: required",
        "counts.modules: must be a whole number of 0 or more",
    ]


def test_shape_reports_wrong_container_types() -> None:
    assert shape("decisions", {"title": "", "decisions": {}, "holes": [5]}) == [
        "title: must be a non-empty string",
        "decisions: must be a list",
        "holes[0]: must be an object",
    ]
```

- [ ] **Step 2:** Run `uv run pytest -q tests/scripts/test_architecture_delta_records.py`. Expected: FAIL (module not found) for all four.
- [ ] **Step 3: GREEN.** Write `records-shape.mjs` to the interface above. Comment line at the top: `// The record tables of the architecture model folder, and the shape pass (pass 2b) over one parsed file.`
- [ ] **Step 4:** Run `uv run pytest -q tests/scripts/test_architecture_delta_records.py tests/scripts/test_architecture_delta_safety.py`. Expected: PASS.
- [ ] **Step 5:** Refactor duplicated type checks into one function per type; rerun Step 4.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/records-shape.mjs tests/scripts/test_architecture_delta_records.py && git commit -m "feat(#31): record tables and the shape pass"`

### Task 3: reading the record folders (passes 1 and 2)

**Tier:** standard — interface given; folder handling and line order.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/records.mjs`
- Test: `tests/scripts/test_architecture_delta_records.py` (append)

**Callers that move with this task:** none (new module; not wired yet).

**Interface.** `readRecords(modelDir, elementIds, tick = () => {})`:
- Reads `decisions/`, `contracts/`, `changes/` (each absent = empty) and `coverage.json` (absent = `null`) under `modelDir` with `fs.readdirSync(dir, { withFileTypes: true })` and `fs.readFileSync`. Entries whose name starts with `.` inside the three folders are skipped.
- Pass 1: names checked with `/^[a-z0-9]+(-[a-z0-9]+)*\.json$/` (decisions, contracts) and `/^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(-[a-z0-9]+)*\.json$/` (changes). A directory entry inside a record folder, a record folder that is a file, a `coverage.json` that is a directory: the Messages table. A misnamed file is not read.
- Pass 2a: `JSON.parse`; failure gives `not valid JSON`, a non-object (array, null, scalar) `must be a JSON object`; such a file is not read further. Pass 2b: `shapeProblems`.
- Calls `tick()` after reading each record file.
- Paths in lines use `/`; files are visited sorted by path in UTF-16 order; a folder-level problem uses the folder path (`decisions`) with field path `-`. Problems for one file keep pass order; the final list is sorted by path with a stable sort.
- No problems: returns `{ groups, decisions, holes, contracts, changes, coverage }` where `groups` is `[{ kind, group, title }]`, each record is the parsed object plus `group` (the file name without `.json`) for decisions, holes and contracts, `changes` the parsed change objects, `coverage` the parsed object or `null`. `groups` and records come in folder order (files by path, then position); export sorts.
- Any problem: throws `new ToolError('record-error', lines)` with lines `<path>: <field path>: <message>`.
- This task leaves passes 3–5 as a single function call that returns no problems; Task 4 fills it.

**Reviewer looks at:**
- misnamed file not read — mutation: parse misnamed files too — killed by: `test_misnamed_file_is_reported_once_and_not_read`
- line order across files is by path — mutation: report in readdir order without sorting — killed by: `test_problems_are_listed_by_path`
- folder-level problems — mutation: treat `decisions` as a file as absent — killed by: `test_record_folder_that_is_a_file_and_coverage_that_is_a_folder`

- Satisfies Spec AC: AC-1 (reader half), AC-10 (layout half), AC-14, AC-17 (layout half)
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
def read(folder: Path, ids: list[str] = SHOP_IDS) -> dict:
    return call("records.mjs", "readRecords", str(folder), ids)


def problems(result: dict) -> list[str]:
    assert result["ok"] is False and result["token"] == "record-error", result
    return result["details"]


def test_absent_folders_are_empty(tmp_path) -> None:  # AC-1
    _, folder = model_folder(tmp_path, {})
    assert read(folder) == {"ok": True, "value": {"groups": [], "decisions": [], "holes": [], "contracts": [],
                                                   "changes": [], "coverage": None}}


def test_valid_records_are_returned_with_their_group(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"decisions/orders.json": dfile(decision("D-1"), holes=(hole("H-1"),)),
                                        "contracts/app.json": cfile(contract("C-1")),
                                        "changes/2026-11-16-baseline.json": change(), "coverage.json": coverage()})
    value = read(folder)["value"]
    assert value["groups"] == [{"kind": "contracts", "group": "app", "title": "Boundaries"},
                               {"kind": "decisions", "group": "orders", "title": "Orders"}]
    assert value["decisions"] == [{**decision("D-1"), "group": "orders"}]
    assert value["holes"] == [{**hole("H-1"), "group": "orders"}]
    assert value["contracts"] == [{**contract("C-1"), "group": "app"}]
    assert value["changes"] == [change()] and value["coverage"] == coverage()


def test_misnamed_file_is_reported_once_and_not_read(tmp_path) -> None:  # AC-10, AC-17
    _, folder = model_folder(tmp_path, {"decisions/Memory.json": "{not json", "decisions/.gitkeep": "",
                                        "contracts/old/x.json": cfile(contract("C-1")),
                                        "changes/2026-11-16.json": change()})
    assert problems(read(folder)) == [
        "changes/2026-11-16.json: -: not a valid file name here",
        "contracts/old: -: folders are not allowed here",
        "decisions/Memory.json: -: not a valid file name here",
    ]


def test_record_folder_that_is_a_file_and_coverage_that_is_a_folder(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"decisions": "x", "coverage.json/x.json": "{}"})
    assert problems(read(folder)) == ["coverage.json: -: must be a file", "decisions: -: must be a folder"]


def test_bad_json_is_reported_once_and_others_still_checked(tmp_path) -> None:  # AC-14
    _, folder = model_folder(tmp_path, {"decisions/a.json": "{oops", "decisions/b.json": dfile(decision("D-1", colour="x")),
                                        "contracts/c.json": "[1]"})
    assert problems(read(folder)) == [
        "contracts/c.json: -: must be a JSON object",
        "decisions/a.json: -: not valid JSON",
        "decisions/b.json: decisions[0].colour: unknown field",
    ]


def test_problems_are_listed_by_path(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"decisions/zeta.json": dfile(decision("D-1", status=5)),
                                        "decisions/alpha.json": dfile(decision("D-2", evidence=[]))})
    assert problems(read(folder)) == ["decisions/alpha.json: decisions[0].evidence: must be a string",
                                      "decisions/zeta.json: decisions[0].status: must be a string"]
```

- [ ] **Step 2:** Run `uv run pytest -q tests/scripts/test_architecture_delta_records.py -k "absent or valid_records or misnamed or folder_that or bad_json or by_path"`. Expected: FAIL (module not found).
- [ ] **Step 3: GREEN.** Write `records.mjs` to the interface. Comment line: `// Reads and validates the record files of an architecture model folder.`
- [ ] **Step 4:** Run `uv run pytest -q tests/scripts/test_architecture_delta_records.py tests/scripts/test_architecture_delta_safety.py`. Expected: PASS.
- [ ] **Step 5:** Refactor folder walking into one function per record folder kind; rerun Step 4.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/records.mjs tests/scripts/test_architecture_delta_records.py && git commit -m "feat(#31): read record folders (layout and shape passes)"`

### Task 4: ids, links, order and values (passes 3 to 5)

**Tier:** standard — interface given; the integrity rules.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/records.mjs`
- Test: `tests/scripts/test_architecture_delta_records.py` (append)

**Callers that move with this task:** none.

**Interface.** After passes 1–2 for every file, build: the set of element ids (argument); the set of decision ids left in (string id matching `/^[A-Za-z0-9][A-Za-z0-9.-]*$/`); the set of change names (well-named files in `changes/`, without `.json`). Then for each file in path order run, pass by pass, over records by position and fields in table order:
- Pass 3: record id form; duplicate (a map from id to the first path, filled in this folder order; a later occurrence gives the duplicate line at its own `id` path); change `id` equals its name; element ids that are empty strings; record-id references (`superseded_by`, contract `decisions`, change `decisions`/`holes`/`contracts` lists) checked for form only.
- Pass 4: element ids exist (skipping wrong types and ids reported in pass 3); `superseded_by` equal to own id gives `names its own id`, else must be in the decision set; contract `decisions` entries must be in the decision set; coverage `run` must be in the change names; the same id twice in `binds`, `bound` or a contract's `decisions` gives `<id> is listed twice` at the second occurrence.
- Pass 5: list order (at record `i` among records left in, compared with the previous record left in, message at `<list>[i].id`, before that record's other pass 5 fields); `superseded_by` rule; enums (`status`: `current, partly-built, planned, superseded`; decision `evidence`: `checked, code, spec`; hole `evidence`: `checked, code, spec, search`; `run`: `baseline, epic, later-stage`); `date` and `approved.date` real dates (`YYYY-MM-DD` and the date round-trips through `Date.UTC`); change `date` equals the first 10 characters of its name; `check.exit` is 0 or 1.
- A record whose `id` is missing, not a string or breaks the form is left out of passes 4 and 5.

**Reviewer looks at:**
- references are not duplicates — mutation: add `superseded_by` targets to the duplicate map — killed by: `test_references_are_not_ids`
- duplicate line sits on the later occurrence in folder order — mutation: report at the first occurrence — killed by: `test_duplicate_id_across_files`
- a misnamed file's ids stay out of the id space — mutation: build the id map before pass 1 filtering — killed by: `test_misnamed_file_does_not_create_a_duplicate`
- order position — mutation: compare with `list[i+1]` — killed by: `test_order_problem_is_at_the_first_record_out_of_order`

- Satisfies Spec AC: AC-3 (reader half), AC-4, AC-5, AC-6, AC-7, AC-9, AC-10 (date half), AC-11, AC-15, AC-16, AC-17
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
def test_binds_naming_no_element(tmp_path) -> None:  # AC-3
    _, folder = model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-1", binds=["shop.orders", "shop.nope"]))})
    assert problems(read(folder)) == ["decisions/a.json: decisions[0].binds[1]: shop.nope is not a model element"]


def test_contract_owner_and_bound_problems_in_one_run(tmp_path) -> None:  # AC-4
    _, folder = model_folder(tmp_path, {"contracts/a.json": cfile(contract("C-1", owner="ghost"), contract("C-2", bound=[]))})
    assert problems(read(folder)) == ["contracts/a.json: contracts[1].bound: needs at least one item",
                                      "contracts/a.json: contracts[0].owner: ghost is not a model element"]


def test_duplicate_id_across_files(tmp_path) -> None:  # AC-5
    _, folder = model_folder(tmp_path, {"decisions/a.json": dfile(decision("X-1")), "contracts/b.json": cfile(contract("X-1"))})
    assert problems(read(folder)) == ["decisions/a.json: decisions[0].id: duplicate id X-1, first in contracts/b.json"]


def test_order_problem_is_at_the_first_record_out_of_order(tmp_path) -> None:  # AC-6
    _, folder = model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-2"), decision("D-1"), decision("D-3"))})
    assert problems(read(folder)) == ["decisions/a.json: decisions[1].id: not sorted by id: D-1 comes after D-2"]


def test_supersession_rules(tmp_path) -> None:  # AC-7
    files = {"decisions/a.json": dfile(decision("D-1", status="superseded"), decision("D-2", superseded_by="D-1"),
                                       decision("D-3", status="superseded", superseded_by="D-9"), holes=(hole("H-1"),)),
             "contracts/b.json": cfile(contract("C-1", decisions=["H-1"]))}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == [
        "contracts/b.json: contracts[0].decisions[0]: H-1 names no decision",
        "decisions/a.json: decisions[2].superseded_by: D-9 names no decision",
        "decisions/a.json: decisions[0].superseded_by: required when status is superseded",
        "decisions/a.json: decisions[1].superseded_by: only allowed when status is superseded",
    ]


def test_values_outside_their_lists(tmp_path) -> None:  # AC-9, AC-10
    files = {"decisions/a.json": dfile(decision("D-1", status="done", evidence="memory")),
             "changes/2026-02-30-x.json": change("2026-02-30-x", run="nightly", check={"exit": 2, "summary": "s", "output": "o"}),
             "changes/2026-11-16-y.json": change("2026-11-16-y", date="2026-11-15")}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == [
        "changes/2026-02-30-x.json: date: not a real date",
        "changes/2026-02-30-x.json: run: must be one of baseline, epic, later-stage",
        "changes/2026-02-30-x.json: check.exit: must be 0 or 1",
        "changes/2026-11-16-y.json: date: must be the start of the file name",
        "decisions/a.json: decisions[0].status: must be one of current, partly-built, planned, superseded",
        "decisions/a.json: decisions[0].evidence: must be one of checked, code, spec",
    ]


def test_change_history_is_not_looked_up(tmp_path) -> None:  # AC-11
    _, folder = model_folder(tmp_path, {"changes/2026-11-16-baseline.json": change(
        elements={"added": [], "changed": [], "removed": ["gone.element"]}, gap={"added": [["gone.a", "gone.b"]], "removed": []})})
    assert read(folder)["ok"] is True


def test_coverage_links(tmp_path) -> None:  # AC-15
    _, folder = model_folder(tmp_path, {"coverage.json": coverage(edge_nodes=[{"element": "ghost", "run": "2026-11-16-baseline"}])})
    assert problems(read(folder)) == ["coverage.json: baselined[0].run: 2026-11-16-baseline names no change file",
                                      "coverage.json: edge_nodes[0].element: ghost is not a model element",
                                      "coverage.json: edge_nodes[0].run: 2026-11-16-baseline names no change file"]


def test_self_supersession_and_duplicates_but_not_cycles(tmp_path) -> None:  # AC-16
    files = {"decisions/a.json": dfile(decision("D-1", status="superseded", superseded_by="D-1"),
                                       decision("D-2", binds=["shop", "shop"]),
                                       decision("D-3", status="superseded", superseded_by="D-4"),
                                       decision("D-4", status="superseded", superseded_by="D-3"))}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["decisions/a.json: decisions[0].superseded_by: names its own id",
                                      "decisions/a.json: decisions[1].binds[1]: shop is listed twice"]


def test_misnamed_file_does_not_create_a_duplicate(tmp_path) -> None:  # AC-17
    _, folder = model_folder(tmp_path, {"decisions/Memory.json": dfile(decision("M-1")), "decisions/memory.json": dfile(decision("M-1")),
                                        "decisions/.gitkeep": ""})
    assert problems(read(folder)) == ["decisions/Memory.json: -: not a valid file name here"]


def test_references_are_not_ids(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("D-1"), decision("D-2", status="superseded", superseded_by="D-1")),
             "contracts/b.json": cfile(contract("C-1", decisions=["D-1"])),
             "changes/2026-11-16-baseline.json": change(decisions={"added": ["D-1", "D-2"], "changed": [], "removed": []})}
    _, folder = model_folder(tmp_path, files)
    assert read(folder)["ok"] is True


def test_record_id_forms_and_change_id(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("_bad"), decision("D-1", binds=[""])),
             "changes/2026-11-16-baseline.json": change(id_="2026-11-16-other", date="2026-11-16")}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["changes/2026-11-16-baseline.json: id: must equal the file name 2026-11-16-baseline",
                                      "decisions/a.json: decisions[0].id: not a valid record id",
                                      "decisions/a.json: decisions[1].binds[0]: must not be empty"]


def test_underscored_element_ids_are_accepted(tmp_path) -> None:
    model = "model {\n  my_part = component 'P'\n}\n"
    repo = make_repo(tmp_path, model)
    folder = repo / "docs" / "architecture"
    (folder / "decisions").mkdir()
    (folder / "decisions" / "a.json").write_text(json.dumps(dfile(decision("D-1", binds=["my_part"]))), encoding="utf-8")
    assert read(folder, ["my_part"])["ok"] is True
```

Note for `test_supersession_rules`: in folder order, `contracts/b.json` sorts before `decisions/a.json`; within `decisions/a.json`, pass 4 (links: `decisions[2]`) comes before pass 5 (status rule: `decisions[0]`, `decisions[1]`).

Note for `test_values_outside_their_lists`: change `2026-02-30-x` is well-named (pass 1 checks digits only), so its date fails pass 5; within that file pass 5 follows the table order `date`, `run`, `check`.

- [ ] **Step 2:** Run `uv run pytest -q tests/scripts/test_architecture_delta_records.py`. Expected: FAIL for the tests that need passes 3–5; `test_change_history_is_not_looked_up`, `test_references_are_not_ids`, `test_underscored_element_ids_are_accepted` and `test_misnamed_file_does_not_create_a_duplicate` already pass and pin behaviour that must still hold after.
- [ ] **Step 3: GREEN.** Implement passes 3–5 to the interface.
- [ ] **Step 4:** Run `uv run pytest -q tests/scripts/test_architecture_delta_records.py`. Expected: PASS.
- [ ] **Step 5:** Refactor the three passes into one walker over table fields with a per-pass check function; rerun Step 4.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/records.mjs tests/scripts/test_architecture_delta_records.py && git commit -m "feat(#31): record ids, links, order and values"`

### Task 5: both commands validate records first

**Tier:** standard — the placement decides which error a caller sees.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta.mjs` (`loadRepoModel`)
- Test: `tests/scripts/test_architecture_delta_records.py` (append)

**Callers that move with this task:** sweep row 1 (no edit).

**Change.** In `loadRepoModel`, after `const loaded = await loadModel(LikeC4, model.path); deadline.check();` add `const records = readRecords(model.path, loaded.elements.map((element) => element.id), deadline.check);` and return `{ repo, modelDir: model.path, located, model: loaded, records }`. Import `readRecords` from `./architecture-delta/records.mjs`.

**Reviewer looks at:**
- records read before `--deps` — mutation: move the call into `runCheck` after the deps file is read — killed by: `test_record_errors_come_before_other_inputs`
- `check` stops on records — mutation: catch `record-error` in `check` — killed by: `test_check_exits_2_on_bad_records_even_when_clean`

- Satisfies Spec AC: AC-3 (both commands), AC-13, AC-18
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
BAD = {"decisions/a.json": dfile(decision("D-1", binds=["shop.nope"]))}
BAD_LINE = "error: record-error: decisions/a.json: decisions[0].binds[0]: shop.nope is not a model element"


def test_export_and_check_report_record_errors(tmp_path) -> None:  # AC-3
    repo, _ = model_folder(tmp_path, BAD)
    deps = repo / "deps.json"
    deps.write_text(json.dumps({"edges": []}), encoding="utf-8")
    for args in (("export", "--repo", repo), ("check", "--repo", repo, "--deps", deps)):
        proc = run_tool(*args)
        assert proc.returncode == 2 and proc.stdout == ""
        assert error_lines(proc) == [BAD_LINE]


def test_check_exits_2_on_bad_records_even_when_clean(tmp_path) -> None:  # AC-13
    repo, _ = model_folder(tmp_path, BAD)
    deps = repo / "deps.json"
    deps.write_text(json.dumps({"edges": [["shop.orders.x", "shop.checkout.y"]]}), encoding="utf-8")
    assert run_tool("check", "--repo", repo, "--deps", deps).returncode == 2


def test_record_errors_come_before_other_inputs(tmp_path) -> None:  # AC-18
    repo, _ = model_folder(tmp_path, BAD)
    proc = run_tool("check", "--repo", repo, "--deps", repo / "missing.json")
    assert proc.returncode == 2
    assert error_lines(proc) == [BAD_LINE]
```

- [ ] **Step 2:** Run `uv run pytest -q tests/scripts/test_architecture_delta_records.py -k "report_record_errors or even_when_clean or before_other"`. Expected: FAIL (exit 0, or `bad-input` for the missing deps file).
- [ ] **Step 3: GREEN.** Make the change above.
- [ ] **Step 4:** Run `uv run pytest -q tests/scripts`. Expected: PASS (every existing test: their model folders hold no record files).
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta.mjs tests/scripts/test_architecture_delta_records.py && git commit -m "feat(#31): export and check validate records before other inputs"`

### Task 6: `export` prints the records (format 3)

**Tier:** standard — interface given; cleaning rules.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/report.mjs` (`exportJson`)
- Modify: `skills/shared/scripts/architecture-delta.mjs:94`
- Modify: `tests/scripts/test_architecture_delta_export.py:22,23,44,182`; `tests/scripts/test_architecture_delta_runtime_links.py:155,156`
- Test: `tests/scripts/test_architecture_delta_records.py` (append)

**Callers that move with this task:** sweep rows 2–8.

**Interface.** `exportJson(model, records)` returns `format: 3`, the existing three keys, then `groups` (sorted by `kind`, then `group`, with `clean` on `group`, `cleanText` on `title`), `decisions`, `holes`, `contracts` (each sorted by raw `id` with `cmp`), `changes` (sorted by `id`), `coverage` (object or `null`). Each record object keeps its own keys in file order, `group` last. Cleaning walks each record: a key in `id`, `superseded_by`, `binds`, `owner`, `bound`, `decisions`, `elements`, `holes`, `contracts`, `gap`, `element`, `run`, `group` makes every string under it cleaned with `clean`; every other string with `cleanText`. Numbers, `null` and booleans pass through.

**Reviewer looks at:**
- record text not cut — mutation: use `clean` for text — killed by: `test_record_text_is_cleaned_without_a_cut`
- records sorted by id across groups and `group` last — mutation: keep file order — killed by: `test_export_prints_records_sorted_with_group_last`

- Satisfies Spec AC: AC-1, AC-2, AC-12
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
def export(repo: Path) -> dict:
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_export_without_records(tmp_path) -> None:  # AC-1
    data = export(model_folder(tmp_path, {})[0])
    assert data["format"] == 3
    assert [data[k] for k in ("groups", "decisions", "holes", "contracts", "changes")] == [[], [], [], [], []]
    assert data["coverage"] is None


def test_export_prints_records_sorted_with_group_last(tmp_path) -> None:  # AC-2
    files = {"decisions/orders.json": dfile(decision("D-3"), holes=(hole("H-1"),)),
             "decisions/app.json": dfile(decision("D-1", note="n"), title="App"),
             "contracts/app.json": cfile(contract("C-1")),
             "changes/2026-11-16-baseline.json": change(), "coverage.json": coverage()}
    data = export(model_folder(tmp_path, files)[0])
    assert data["groups"] == [{"kind": "contracts", "group": "app", "title": "Boundaries"},
                              {"kind": "decisions", "group": "app", "title": "App"},
                              {"kind": "decisions", "group": "orders", "title": "Orders"}]
    assert [d["id"] for d in data["decisions"]] == ["D-1", "D-3"]
    assert list(data["decisions"][0]) == [*decision("D-1", note="n"), "group"]
    assert "note" not in data["decisions"][1] and data["decisions"][1]["group"] == "orders"
    assert data["holes"] == [{**hole("H-1"), "group": "orders"}]
    assert data["contracts"] == [{**contract("C-1"), "group": "app"}]
    assert data["changes"] == [change()] and data["coverage"] == coverage()


def test_record_text_is_cleaned_without_a_cut(tmp_path) -> None:  # AC-12
    reason = "r" * 250 + "\u001b[31m" + "\n" + "s" * 250
    data = export(model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-1", reason=reason))})[0])
    assert data["decisions"][0]["reason"] == "r" * 250 + "\n" + "s" * 250
```

- [ ] **Step 2:** Run `uv run pytest -q tests/scripts/test_architecture_delta_records.py -k "export_"` and `-k cleaned_without`. Expected: FAIL (`format` is 2; keys missing).
- [ ] **Step 3: GREEN.** Implement `exportJson(model, records)`; change `architecture-delta.mjs:94` to `exportJson(loaded.model, loaded.records)`; make the six literal edits from the sweep table.
- [ ] **Step 4:** Run `uv run pytest -q tests/scripts`. Expected: PASS.
- [ ] **Step 5:** No refactor beyond keeping the cleaning walker in one function.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/report.mjs skills/shared/scripts/architecture-delta.mjs tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_runtime_links.py tests/scripts/test_architecture_delta_records.py && git commit -m "feat(#31): export prints records (format 3)"`

### Task 7: documents point at the record format

**Tier:** fast — docs only.

**Files:**
- Modify: `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md` (the amendment note after line 3; the token list in "Errors")
- Modify: `docs/superpowers/specs/2026-11-16-architecture-delta-runtime-links-design.md` (after its work-item line)
- Modify: `skills/defining-architecture/ARCH_STANDARDS.md` (delta tool flags)

**Callers that move with this task:** none.

**Reviewer looks at:**
- the token list names `record-error` — checked by the grep in Step 3.

**Pinned by:** `tests/scripts/test_defining_architecture_contract.py` reads `ARCH_STANDARDS.md`; Step 3 runs it.

- Satisfies Spec AC: none (the spec's Scope)
- **Test retention:** no new test (docs-only branch)

- [ ] **Step 1: RED.** `grep -c "record-error" docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md skills/defining-architecture/ARCH_STANDARDS.md; grep -c "format. is now 3\|records-design" docs/superpowers/specs/2026-11-16-architecture-delta-runtime-links-design.md` Expected: `0`, `0`, `0`.
- [ ] **Step 2: GREEN.**
  - In the 2026-11-09 spec, add after the existing amendment note: `> Amended by \`2026-11-17-architecture-model-records-design.md\` (#31): the tool also reads and validates the record files in the model folder, \`export\` prints them (format 3), record text is cleaned without the 200-character cut, and \`record-error\` is an exit-2 token.` In its "Errors" paragraph change `` `timeout` and `internal`. `` to `` `timeout`, `record-error` and `internal`. ``
  - In the runtime-links spec, add after its `Work item:` line: `> \`export\` is now format 3: \`2026-11-17-architecture-model-records-design.md\` (#31) adds the record lists after \`runtime\`.`
  - In `ARCH_STANDARDS.md`, after the line beginning `` - Only a relationship of kind `uses` ``, add: `` - `export` also prints the model's records (decisions, holes, contracts, changes, coverage). A problem in a record file is `record-error`, exit 2, from both `export` and `check`. ``
- [ ] **Step 3:** `grep -c "record-error" docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md skills/defining-architecture/ARCH_STANDARDS.md; grep -c "format 3" docs/superpowers/specs/2026-11-16-architecture-delta-runtime-links-design.md; uv run pytest -q tests/scripts/test_defining_architecture_contract.py tests/test_repo_layout.py` Expected: `2`, `1`, `1`, then PASS.
- [ ] **Step 4:** `git add docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md docs/superpowers/specs/2026-11-16-architecture-delta-runtime-links-design.md skills/defining-architecture/ARCH_STANDARDS.md && git commit -m "docs(#31): tool spec, runtime-links spec and standards point at the record format"`
- [ ] **Step 5:** Full suite: `uv run pytest -q`. Expected: PASS.
