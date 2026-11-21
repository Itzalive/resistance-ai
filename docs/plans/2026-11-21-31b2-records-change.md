# Architecture Records `change` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new tool `skills/shared/scripts/architecture-records.mjs` whose `change` command drafts a run's change file from the before copy and the current model, refuses to replace an approved one, and with `--compare` reports whether the draft is current.

**Architecture:** This repository has no architecture model. The tool reuses the delta tool's loader (`load.mjs` `loadRepoModel`), its `check` run (moved, unchanged, into `architecture-delta/check.mjs`), its `export` shape (`report.mjs` `exportJson`) and a change-file validator exported from `records.mjs`. New modules in `skills/shared/scripts/architecture-records/`: `args.mjs` (flags), `change.mjs` (the change object, pure), `writer.mjs` (the only module that writes). The `cycles` command is plan 2b.

**Tech Stack:** Node ESM (no new dependency), pytest via `uv run`.

**Spec:** `docs/superpowers/specs/2026-11-21-defining-architecture-records-design.md` ("The helper tool": the intro, "Delta modules the helper reuses", "`change`"; Threat Model; AC-1 to AC-9) — decisions applied: none. Plan 2a of the four plans; the spec's plan 2 is split into 2a (`change`) and 2b (`cycles`) by the sizing rule (two entry paths and more than eight tasks together).

**Open decisions:** none

**Size:** 8 tasks, 1 entry path (`architecture-records.mjs change`), lines reported in the self-review commit (reported, not a target)

**Trust boundary:** changed — see Trust-boundary table.

### Risk & Confidence Assessment

**Confidence:** 90% — every piece reuses a tested delta function; the new logic is set differences and one guarded write.

**Complexity Risk:** Medium — driving variable: the writer's conditional replace (a draft may be replaced, an approved file never), with a temporary file and rename.

**Environmental Risk:** Low — the tests build repositories in `tmp_path` and run the tool as a subprocess, as the delta and docs tests do.

**Main failure modes:** the `check` move changes the delta tool's output (pinned by the existing check tests); a change id is used in a path before its name is validated (path traversal; Task 6 validates first); an approved file replaced (Task 5); the change file's text differs in line endings on Windows (written by Node, LF).

**Unknown variables:**
- LikeC4 loading a second model folder in one process (the before copy). Expected to work, since `loadModel` builds a fresh workspace per call; proven by Task 6's AC-1 test.

---

## Caller and test sweep

Searched: `skills/`, `tests/`, `scripts/`, `agents/` with `grep -rn "runCheck\|architecture-delta.mjs\|CHANGE_FILE\|isRealDate" skills tests scripts agents`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `runCheck` moves from `architecture-delta.mjs` to `architecture-delta/check.mjs` | `architecture-delta.mjs` `main` | caller | 1 | `import { runCheck } from './architecture-delta/check.mjs';` |
| same | `tests/scripts/arch_delta_support.py` `copy_engine` copies the whole `architecture-delta/` folder | test helper | — | none: `check.mjs` is copied with it |
| same | `tests/scripts/test_architecture_delta_safety.py` scans `LIB/*.mjs` | assert | — | none: `check.mjs` writes nothing and spawns nothing |
| `records.mjs` exports `changeFileProblems` | none | — | 2 | new export |
| `arch_delta_support.py` gains `RECORDS_SCRIPT`, `RECORDS_LIB` | the new records tests | test helper | 3 | two lines, below |

## Trust-boundary table

| Producer or reader | Where it is used | Text it receives | Untrusted source | Task | Proving test |
|---|---|---|---|---|---|
| `--name`, `--date` | a file path `changes/<date>-<name>.json` | flag text | the run's caller | 6 | `test_change_refuses_bad_values_and_writes_nothing[name]` (a name with `_`), `[long]`; the name pattern allows only `[a-z0-9-]` |
| `--before` | a folder loaded as a model | flag text | the run's caller | 6 | `test_before_must_be_inside_the_repo_and_apart_from_the_model` |
| `--summary`, `--asked-by`, `--rejected` | record text, later printed by `export` and the documents | flag text | the run's caller | 6 | `test_flag_text_is_cleaned_by_export` (AC-7) |
| `writeChange` | replaces `changes/<id>.json` | an existing file | an earlier run | 5 | `test_writer_never_replaces_an_approved_file` |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 5 | 5 | Task 5 items 1–3 (strong); focused tests `uv run pytest -q tests/scripts/test_architecture_records_writer.py` |

Tasks 1–4 and 6–8 are standard or fast tier; under the owner's rule no mutation checkpoint reviewer is sent for them, and the code review and survivability of the whole change check their items.

---

### Task 1: the delta `check` run moves into `architecture-delta/check.mjs`

**Tier:** fast — a verbatim move with complete edits.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/check.mjs`
- Modify: `skills/shared/scripts/architecture-delta.mjs`

**Callers that move with this task:** `architecture-delta.mjs` `main` (sweep row 1).

**Reviewer looks at:**
- the moved run is the one `check` uses — mutation: in `check.mjs` drop `known` breaches from the text report by passing `gap: []` to `compare` — killed by: `tests/scripts/test_architecture_delta_check.py::test_known_new_and_stale`

**Pinned by:** `tests/scripts/test_architecture_delta_check.py::test_known_new_and_stale` (asserts the new, stale and known lists), `::test_text_report_lists_every_heading_in_order_and_counts_each_kind` (the text output), `::test_input_errors_end_to_end` (the `--deps` and `--gap` errors); `tests/scripts/test_architecture_delta_records.py::test_record_errors_come_before_other_inputs` (records first). No new test: the move changes no behaviour.

- Satisfies Spec AC: none directly ("Delta modules the helper reuses")
- **Test retention:** none added

- [ ] **Step 1: RED.** No new test. Confirm the pins pass before the move:

Run: `uv run pytest -q tests/scripts/test_architecture_delta_check.py tests/scripts/test_architecture_delta_records.py`
Expected: all pass.

- [ ] **Step 2: GREEN.** Create `skills/shared/scripts/architecture-delta/check.mjs`:

```js
// The delta `check` run: compares the code's dependency edges with a loaded model. Shared by the delta tool and
// the records tool, so both print exactly the same report.
import path from 'node:path';
import { ToolError } from './errors.mjs';
import { readOptional } from './load.mjs';
import { resolveInside } from './paths.mjs';
import { readJson, parseDeps, parseGap, parseShards } from './inputs.mjs';
import { compare } from './match.mjs';
import { checkJson, checkText } from './report.mjs';

export async function runCheck(args, deadline, loaded) {
  const { repo, modelDir, located, model } = loaded;
  const ids = model.elements.map((element) => element.id);
  const deps = resolveInside(repo, args.deps, '--deps');
  if (!deps.exists) throw new ToolError('bad-input', '--deps file not found');
  const edges = parseDeps(readJson(deps.path, '--deps'));
  deadline.check();
  const gap = readOptional(repo, args.gap, path.join(modelDir, 'known-gap.json'), '--gap', (data) => parseGap(data, ids)) ?? [];
  deadline.check();
  const shards = args.shards === null ? null : readOptional(repo, args.shards, null, '--shards', (data) => parseShards(data, ids));
  deadline.check();
  if (args.scope !== null) {
    const known = new Set(ids);
    const unknown = args.scope.filter((id) => !known.has(id));
    if (unknown.length > 0) throw new ToolError('unknown-scope', unknown.map((id) => `${id} is not a model element`));
  }
  const result = compare(model, edges, { separator: args.separator, gap, scope: args.scope, shards, tick: deadline.check });
  const report = checkJson(result, located);
  const output = args.format === 'json' ? `${JSON.stringify(report, null, 2)}\n` : checkText(report);
  return { output, exitCode: result.exitCode };
}
```

Replace the whole of `skills/shared/scripts/architecture-delta.mjs` with:

```js
#!/usr/bin/env node
// Architecture delta: compares a LikeC4 C4 model with a repository's code dependencies.
// Reads files only; never writes a file or runs another program.
import { parseArgs } from './architecture-delta/args.mjs';
import { startDeadline, loadRepoModel, runCli } from './architecture-delta/load.mjs';
import { runCheck } from './architecture-delta/check.mjs';
import { exportJson } from './architecture-delta/report.mjs';

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  const loaded = await loadRepoModel(args, deadline);
  const result = args.command === 'export'
    ? { output: `${JSON.stringify(exportJson(loaded.model, loaded.records), null, 2)}\n`, exitCode: 0 }
    : await runCheck(args, deadline, loaded);
  deadline.stop();
  return result;
}

runCli(main);
```

- [ ] **Step 3: run the pins and every delta test.**

Run: `uv run pytest -q tests/scripts/ -k architecture_delta`
Expected: all pass, none edited.

- [ ] **Step 4: commit.**

```bash
git add skills/shared/scripts/architecture-delta.mjs skills/shared/scripts/architecture-delta/check.mjs
git commit -m "refactor(#31): the delta check run moves into architecture-delta/check.mjs, unchanged"
```

---

### Task 2: `records.mjs` exports a change-file validator

**Tier:** fast — complete code.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/records.mjs` (append one export)
- Test: `tests/scripts/test_architecture_delta_records.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- a bad file name stops before the shape is read — mutation: drop the early `return` after the name problem — killed by: `test_change_file_problems_name_first`
- the date must be real and start the name — mutation: skip `valuePass` — killed by: `test_change_file_problems_values`

- Satisfies Spec AC: supports AC-5 (`bad-input` for a bad name, a 65-character id, a false date, empty text)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append to `tests/scripts/test_architecture_delta_records.py`:

```python
def valid_change(**over) -> dict:
    record = {"id": "2026-11-21-first", "date": "2026-11-21", "run": "epic", "asked_by": "#1", "summary": "S.",
              "rejected": [], "elements": {"added": [], "changed": [], "removed": []},
              "decisions": {"added": [], "changed": [], "removed": []},
              "holes": {"added": [], "changed": [], "removed": []},
              "contracts": {"added": [], "changed": [], "removed": []},
              "gap": {"added": [], "removed": []}, "check": {"exit": 0, "summary": "ok", "output": "ok\n"},
              "approved": None}
    record.update(over)
    return record


def test_change_file_problems_name_first() -> None:
    out = call("records.mjs", "changeFileProblems", "2026-11-21-Bad_Name.json", {"anything": 1})
    assert out == {"ok": True, "value": ["changes/2026-11-21-Bad_Name.json: -: not a valid file name here"]}
    long_name = "2026-11-21-" + "n" * 54 + ".json"
    assert call("records.mjs", "changeFileProblems", long_name, valid_change())["value"] == [
        f"changes/{long_name}: -: not a valid file name here"]


def test_change_file_problems_values() -> None:
    assert call("records.mjs", "changeFileProblems", "2026-11-21-first.json", valid_change())["value"] == []
    bad = valid_change(id="2026-02-30-first", date="2026-02-30", summary="", run="weekly", rejected=[""])
    out = call("records.mjs", "changeFileProblems", "2026-02-30-first.json", bad)["value"]
    assert out == [
        "changes/2026-02-30-first.json: summary: must be a non-empty string",
        "changes/2026-02-30-first.json: rejected[0]: must be a non-empty string",
        "changes/2026-02-30-first.json: date: not a real date",
        "changes/2026-02-30-first.json: run: must be one of baseline, epic, later-stage",
    ]
```

Add `call` to that file's `from arch_delta_support import ...` line if it is not there.

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_records.py -k change_file_problems`
Expected: 2 failed (`ok` is false: `m.changeFileProblems is not a function`).

- [ ] **Step 3: GREEN.** Append to `skills/shared/scripts/architecture-delta/records.mjs`:

```js
// One change file checked on its own, as the records reader checks it (passes 1, 2b, 3 and 5; pass 4 does not apply
// to a change file). Returns the problem lines, empty when the file is valid; a bad name is the only line.
export function changeFileProblems(fileName, data) {
  const at = `changes/${fileName}`;
  if (!CHANGE_FILE.test(fileName)) return [`${at}: -: not a valid file name here`];
  const out = [];
  for (const found of shapeProblems('change', data)) out.push(`${at}: ${found.field}: ${found.message}`);
  const file = { at, kind: 'change', name: fileName.slice(0, -'.json'.length), data };
  const add = (field, message) => out.push(`${at}: ${field}: ${message}`);
  idPass(file, add, new Map());
  valuePass(file, add);
  return out;
}
```

- [ ] **Step 4: run GREEN and the whole records file.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_records.py`
Expected: all pass.

- [ ] **Step 5: commit.**

```bash
git add skills/shared/scripts/architecture-delta/records.mjs tests/scripts/test_architecture_delta_records.py
git commit -m "feat(#31): records.mjs checks one change file on its own"
```

---

### Task 3: the records tool's flags

**Tier:** fast — complete code.

**Files:**
- Create: `skills/shared/scripts/architecture-records/args.mjs`
- Modify: `tests/scripts/arch_delta_support.py` (two constants)
- Test: `tests/scripts/test_architecture_records_args.py`

**Callers that move with this task:** `arch_delta_support.py` (sweep row 5).

**Reviewer looks at:**
- `--rejected` repeats and keeps its order — mutation: keep only the last `--rejected` — killed by: `test_rejected_repeats_in_order`
- `--asked-by` and `--summary` are required only without `--compare` — mutation: require them always — killed by: `test_compare_needs_no_text_flags`
- an unknown flag is a usage error — mutation: skip the `FLAGS` check — killed by: `test_usage_errors[unknown flag]`

- Satisfies Spec AC: supports AC-5 and AC-9
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** In `tests/scripts/arch_delta_support.py`, after the `DOCS_LIB` line, add:

```python
RECORDS_SCRIPT = ENGINE / "skills" / "shared" / "scripts" / "architecture-records.mjs"
RECORDS_LIB = ENGINE / "skills" / "shared" / "scripts" / "architecture-records"
```

Create `tests/scripts/test_architecture_records_args.py`:

```python
"""Flags of the architecture records tool (spec 2026-11-21-defining-architecture-records-design.md, "`change`")."""

from __future__ import annotations

import pytest

from arch_delta_support import RECORDS_LIB, call, require_node

require_node()

BASE = ["change", "--repo", ".", "--deps", "d.json", "--name", "first", "--date", "2026-11-21", "--run", "epic"]
TEXT = ["--asked-by", "#1", "--summary", "S."]


def parse(*argv: str) -> dict:
    return call("args.mjs", "parseArgs", list(argv), lib=RECORDS_LIB)


def test_defaults_and_values() -> None:
    out = parse(*BASE, *TEXT)
    assert out == {"ok": True, "value": {
        "command": "change", "repo": ".", "model": "docs/architecture", "before": None, "deps": "d.json",
        "separator": ".", "name": "first", "date": "2026-11-21", "run": "epic", "askedBy": "#1", "summary": "S.",
        "rejected": [], "compare": False, "timeout": 60}}


def test_rejected_repeats_in_order() -> None:
    out = parse(*BASE, *TEXT, "--rejected", "B.", "--rejected", "A.")
    assert out["value"]["rejected"] == ["B.", "A."]


def test_compare_needs_no_text_flags() -> None:
    out = parse(*BASE, "--compare")
    assert out["ok"] is True
    assert (out["value"]["compare"], out["value"]["askedBy"], out["value"]["summary"]) == (True, None, None)


def test_empty_text_values_are_left_to_the_validator() -> None:
    out = parse(*BASE, "--asked-by", "", "--summary", "")
    assert (out["value"]["askedBy"], out["value"]["summary"]) == ("", "")


@pytest.mark.parametrize(("argv", "detail"), [
    (["cycles-ish"], "unknown subcommand cycles-ish; use change"),
    ([*BASE, *TEXT, "--colour", "x"], "unknown flag for change: --colour"),
    ([*BASE, *TEXT, "--name", "again"], "--name given twice"),
    ([*BASE, *TEXT, "--compare", "--compare"], "--compare given twice"),
    ([*BASE[:-2], *TEXT], "--run is required"),
    ([*BASE, "--summary", "S."], "--asked-by is required without --compare"),
    ([*BASE, *TEXT, "--before"], "--before needs a value"),
    ([*BASE, *TEXT, "--timeout", "601"], "--timeout must be a whole number from 0 to 600"),
    ([*BASE, *TEXT, "--separator", ""], "--separator must not be empty"),
], ids=["subcommand", "unknown flag", "twice", "switch twice", "required", "text required", "no value", "timeout",
        "separator"])
def test_usage_errors(argv: list, detail: str) -> None:
    out = parse(*argv)
    assert (out["ok"], out["token"], out["details"]) == (False, "usage", [detail])
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_args.py`
Expected: 13 failed (the module does not exist; `call` fails to import it, so `ok` is false or the snippet exits non-zero).

- [ ] **Step 3: GREEN.** Create `skills/shared/scripts/architecture-records/args.mjs`:

```js
// Command-line parsing for the architecture records tool. Every problem is a `usage` error.
import { ToolError } from '../architecture-delta/errors.mjs';

const FLAGS = {
  change: ['--repo', '--model', '--before', '--deps', '--separator', '--name', '--date', '--run', '--asked-by',
    '--summary', '--rejected', '--timeout'],
};
const SWITCHES = { change: ['--compare'] };
const REQUIRED = { change: ['--repo', '--deps', '--name', '--date', '--run'] };
const MAX_TIMEOUT = 600;
const usage = (detail) => new ToolError('usage', detail);

export function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (!Object.hasOwn(FLAGS, command ?? '')) {
    throw usage(`unknown subcommand ${command ?? '(none)'}; use ${Object.keys(FLAGS).join(' or ')}`);
  }
  const opts = {};
  const switches = new Set();
  const rejected = [];
  for (let i = 0; i < rest.length;) {
    const flag = rest[i];
    if (SWITCHES[command].includes(flag)) {
      if (switches.has(flag)) throw usage(`${flag} given twice`);
      switches.add(flag);
      i += 1;
      continue;
    }
    if (!FLAGS[command].includes(flag)) throw usage(`unknown flag for ${command}: ${flag}`);
    const value = rest[i + 1];
    if (value === undefined || value.startsWith('--')) throw usage(`${flag} needs a value`);
    if (flag === '--rejected') rejected.push(value);
    else if (Object.hasOwn(opts, flag)) throw usage(`${flag} given twice`);
    else opts[flag] = value;
    i += 2;
  }
  for (const flag of REQUIRED[command]) if (opts[flag] === undefined) throw usage(`${flag} is required`);
  const compare = switches.has('--compare');
  for (const flag of ['--asked-by', '--summary']) {
    if (!compare && opts[flag] === undefined) throw usage(`${flag} is required without --compare`);
  }
  for (const flag of ['--model', '--before', '--separator']) if (opts[flag] === '') throw usage(`${flag} must not be empty`);
  const timeoutText = opts['--timeout'] ?? '60';
  if (!/^\d+$/.test(timeoutText) || Number(timeoutText) > MAX_TIMEOUT) {
    throw usage(`--timeout must be a whole number from 0 to ${MAX_TIMEOUT}`);
  }
  return {
    command,
    repo: opts['--repo'],
    model: opts['--model'] ?? 'docs/architecture',
    before: opts['--before'] ?? null,
    deps: opts['--deps'],
    separator: opts['--separator'] ?? '.',
    name: opts['--name'],
    date: opts['--date'],
    run: opts['--run'],
    askedBy: opts['--asked-by'] ?? null,
    summary: opts['--summary'] ?? null,
    rejected,
    compare,
    timeout: Number(timeoutText),
  };
}
```

- [ ] **Step 4: run GREEN.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_args.py`
Expected: 13 passed.

- [ ] **Step 5: commit.**

```bash
git add skills/shared/scripts/architecture-records/args.mjs tests/scripts/arch_delta_support.py tests/scripts/test_architecture_records_args.py
git commit -m "feat(#31): architecture-records flags for change"
```

---

### Task 4: the change object

**Tier:** standard — set differences with exact ordering rules; complete code given.

**Files:**
- Create: `skills/shared/scripts/architecture-records/change.mjs`
- Test: `tests/scripts/test_architecture_records_change_object.py`

**Callers that move with this task:** none.

**Reviewer looks at:**
- an element whose relationships changed is `changed` — mutation: compare only the element objects, not their links — killed by: `test_relationship_change_marks_both_ends`
- a record moved between groups is not `changed` — mutation: keep `group` in the compared record — killed by: `test_moved_record_is_unchanged`
- key order never counts — mutation: compare `JSON.stringify` instead of `canonical` — killed by: `test_moved_record_is_unchanged` (its after record has its keys in another order)
- lists are sorted in UTF-16 order — mutation: drop the `.sort(cmp)` on `added` — killed by: `test_lists_and_gap_pairs_are_sorted`

- Satisfies Spec AC: AC-1 and AC-2 (the lists; the file and the command are Task 6)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_records_change_object.py`:

```python
"""The change object (spec 2026-11-21-defining-architecture-records-design.md, "`change`": elements, records, gap,
check, the rest)."""

from __future__ import annotations

from arch_delta_support import RECORDS_LIB, call, require_node

require_node()

EMPTY = {"elements": [], "allowed": [], "runtime": [], "decisions": [], "holes": [], "contracts": []}
FLAGS = {"name": "first", "date": "2026-11-21", "run": "epic", "askedBy": "#1", "summary": "S.", "rejected": ["B.", "A."]}
CHECK = {"output": "Known breaches\n  b -> a (1 edges)\n\n0 new, 0 stale, 1 known (likec4 1.60.0 from plugin)\n",
         "exitCode": 0}


def element(id_: str, title: str = "T") -> dict:
    return {"id": id_, "kind": "component", "tags": [], "code": [id_], "rules": [], "title": title, "description": None}


def link(from_: str, to: str) -> dict:
    return {"from": from_, "to": to, "titles": []}


def build(before: dict, after: dict, before_gap: list = (), after_gap: list = ()) -> dict:
    out = call("change.mjs", "buildChange", {"before": before, "after": after, "beforeGap": list(before_gap),
                                             "afterGap": list(after_gap), "check": CHECK, "flags": FLAGS}, lib=RECORDS_LIB)
    assert out["ok"], out
    return out["value"]


def test_keys_and_fixed_fields() -> None:
    value = build(EMPTY, EMPTY)
    assert list(value) == ["id", "date", "run", "asked_by", "summary", "rejected", "elements", "decisions", "holes",
                           "contracts", "gap", "check", "approved"]
    assert (value["id"], value["date"], value["run"], value["asked_by"], value["summary"]) == (
        "2026-11-21-first", "2026-11-21", "epic", "#1", "S.")
    assert value["rejected"] == ["B.", "A."]
    assert value["check"] == {"exit": 0, "summary": "0 new, 0 stale, 1 known (likec4 1.60.0 from plugin)",
                              "output": CHECK["output"]}
    assert value["approved"] is None
    assert list(value["elements"]) == ["added", "changed", "removed"]
    assert list(value["gap"]) == ["added", "removed"]


def test_relationship_change_marks_both_ends() -> None:
    before = {**EMPTY, "elements": [element("a"), element("b"), element("c")], "allowed": [link("a", "b")]}
    after = {**EMPTY, "elements": [element("a"), element("b"), element("c")], "allowed": [link("a", "b"), link("c", "b")]}
    assert build(before, after)["elements"] == {"added": [], "changed": ["b", "c"], "removed": []}
    runtime = {**before, "runtime": [{"from": "a", "to": "c", "kind": "http", "titles": []}]}
    assert build(before, runtime)["elements"] == {"added": [], "changed": ["a", "c"], "removed": []}


def test_moved_record_is_unchanged() -> None:
    record = {"id": "D-1", "decision": "X.", "reason": None, "group": "a"}
    moved = {"group": "b", "reason": None, "decision": "X.", "id": "D-1"}
    edited = {"id": "D-2", "decision": "Y.", "reason": "New.", "group": "a"}
    before = {**EMPTY, "decisions": [record, {"id": "D-2", "decision": "Y.", "reason": "Old.", "group": "a"}]}
    after = {**EMPTY, "decisions": [moved, edited]}
    assert build(before, after)["decisions"] == {"added": [], "changed": ["D-2"], "removed": []}


def test_empty_before_adds_everything() -> None:  # AC-2
    after = {**EMPTY, "elements": [element("a")], "holes": [{"id": "H-1", "what": "?", "group": "a"}],
             "contracts": [{"id": "C-1", "name": "API", "group": "x"}]}
    value = build(EMPTY, after, after_gap=[{"from": "a", "to": "b", "reason": "r", "close_by": None}])
    assert value["elements"]["added"] == ["a"]
    assert value["holes"]["added"] == ["H-1"]
    assert value["contracts"]["added"] == ["C-1"]
    assert value["gap"] == {"added": [["a", "b"]], "removed": []}


def test_lists_and_gap_pairs_are_sorted() -> None:
    after = {**EMPTY, "elements": [element("b"), element("Z"), element("a")]}
    assert build(EMPTY, after)["elements"]["added"] == ["Z", "a", "b"]
    gap = [{"from": "b", "to": "a", "reason": "r", "close_by": None}, {"from": "a", "to": "c", "reason": "r", "close_by": None},
           {"from": "a", "to": "b", "reason": "r", "close_by": None}]
    assert build(EMPTY, EMPTY, before_gap=gap)["gap"] == {"added": [], "removed": [["a", "b"], ["a", "c"], ["b", "a"]]}


def test_changed_reason_is_not_a_gap_change() -> None:
    before_gap = [{"from": "a", "to": "b", "reason": "old", "close_by": None}]
    after_gap = [{"from": "a", "to": "b", "reason": "new", "close_by": "F-1"}]
    assert build(EMPTY, EMPTY, before_gap, after_gap)["gap"] == {"added": [], "removed": []}
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_change_object.py`
Expected: 6 failed (the module does not exist).

- [ ] **Step 3: GREEN.** Create `skills/shared/scripts/architecture-records/change.mjs`:

```js
// The change object of one run (spec 2026-11-21, "`change`"): what the run added, changed and removed, from the
// `export` of the before model and of the current model. Pure: reads and writes nothing.
import { cmp } from '../architecture-delta/report.mjs';

// A text of a value with object keys sorted, so key order never counts when two values are compared.
export function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return `{${Object.keys(value).sort(cmp).map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export const EMPTY_EXPORT = { elements: [], allowed: [], runtime: [], decisions: [], holes: [], contracts: [] };

// Added, changed and removed ids between two maps of id -> canonical text, each sorted in UTF-16 order.
function diff(before, after) {
  const sorted = (ids) => ids.sort(cmp);
  return {
    added: sorted([...after.keys()].filter((id) => !before.has(id))),
    changed: sorted([...after.keys()].filter((id) => before.has(id) && before.get(id) !== after.get(id))),
    removed: sorted([...before.keys()].filter((id) => !after.has(id))),
  };
}

// Each element's export object together with the `allowed` and `runtime` entries it is an end of.
function elementTexts(exported) {
  const links = new Map(exported.elements.map((element) => [element.id, []]));
  const add = (list, entry) => {
    for (const end of new Set([entry.from, entry.to])) links.get(end)?.push(canonical({ list, entry }));
  };
  for (const entry of exported.allowed) add('allowed', entry);
  for (const entry of exported.runtime) add('runtime', entry);
  return new Map(exported.elements.map((element) => [element.id,
    canonical({ element, links: links.get(element.id).sort(cmp) })]));
}

// Records by id, compared without `group`: a record moved to another file is not changed.
function recordTexts(records) {
  return new Map(records.map(({ group, ...record }) => [record.id, canonical(record)]));
}

function gapDiff(before, after) {
  const pairs = (entries) => new Map(entries.map((entry) => [`${entry.from}\u0000${entry.to}`, [entry.from, entry.to]]));
  const b = pairs(before);
  const a = pairs(after);
  const sorted = (list) => list.sort((x, y) => cmp(x[0], y[0]) || cmp(x[1], y[1]));
  return {
    added: sorted([...a].filter(([key]) => !b.has(key)).map(([, pair]) => pair)),
    removed: sorted([...b].filter(([key]) => !a.has(key)).map(([, pair]) => pair)),
  };
}

const lastLine = (output) => output.split('\n').filter((line) => line !== '').at(-1) ?? '';

// `before` and `after` are `export` objects; the gaps are known-gap entries; `check` is the delta check run's
// { output, exitCode }; `flags` holds name, date, run, askedBy, summary and rejected. Keys in the records table order.
export function buildChange({ before, after, beforeGap, afterGap, check, flags }) {
  return {
    id: `${flags.date}-${flags.name}`,
    date: flags.date,
    run: flags.run,
    asked_by: flags.askedBy,
    summary: flags.summary,
    rejected: [...flags.rejected],
    elements: diff(elementTexts(before), elementTexts(after)),
    decisions: diff(recordTexts(before.decisions), recordTexts(after.decisions)),
    holes: diff(recordTexts(before.holes), recordTexts(after.holes)),
    contracts: diff(recordTexts(before.contracts), recordTexts(after.contracts)),
    gap: gapDiff(beforeGap, afterGap),
    check: { exit: check.exitCode, summary: lastLine(check.output), output: check.output },
    approved: null,
  };
}
```

- [ ] **Step 4: run GREEN.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_change_object.py`
Expected: 6 passed.

- [ ] **Step 5: commit.**

```bash
git add skills/shared/scripts/architecture-records/change.mjs tests/scripts/test_architecture_records_change_object.py
git commit -m "feat(#31): the change object - added, changed and removed elements, records and gap pairs"
```

---

### Task 5: the writer

**Tier:** strong — a conditional write: a draft may be replaced, an approved change file never.

**Files:**
- Create: `skills/shared/scripts/architecture-records/writer.mjs`
- Test: `tests/scripts/test_architecture_records_writer.py`

**Callers that move with this task:** none.

**Reviewer looks at:**
- an approved file is never replaced — mutation: test `current.approved === undefined` instead of `!== null` — killed by: `test_writer_never_replaces_an_approved_file`
- a draft is replaced through a temporary file — mutation: write straight to the target with `flag: 'wx'` — killed by: `test_writer_replaces_a_draft`
- left-over temporary files are removed — mutation: skip the clean-up loop — killed by: `test_writer_removes_left_over_temporary_files`
- a failed step is `out-error` — mutation: drop the `attempt` around `mkdirSync` — killed by: `test_writer_failure_is_out_error`

- Satisfies Spec AC: AC-6 (with Task 6)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_records_writer.py`:

```python
"""The records tool's writer (spec 2026-11-21-defining-architecture-records-design.md, "`change`": the write)."""

from __future__ import annotations

import json

from arch_delta_support import RECORDS_LIB, call, require_node, unique

require_node()

TEXT = '{\n  "id": "2026-11-21-first"\n}\n'


def write(model_dir, text: str = TEXT) -> dict:
    return call("writer.mjs", "writeChange", str(model_dir), "2026-11-21-first", text, lib=RECORDS_LIB)


def model(tmp_path):
    folder = tmp_path / unique("model")
    folder.mkdir()
    return folder


def test_writer_creates_the_folder_and_writes_lf(tmp_path) -> None:
    folder = model(tmp_path)
    assert write(folder) == {"ok": True, "value": None}
    assert (folder / "changes" / "2026-11-21-first.json").read_bytes() == TEXT.encode()


def test_writer_replaces_a_draft(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").mkdir()
    (folder / "changes" / "2026-11-21-first.json").write_text(json.dumps({"approved": None}), encoding="utf-8")
    assert write(folder)["ok"] is True
    assert (folder / "changes" / "2026-11-21-first.json").read_text(encoding="utf-8") == TEXT
    assert sorted(p.name for p in (folder / "changes").iterdir()) == ["2026-11-21-first.json"]


def test_writer_never_replaces_an_approved_file(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").mkdir()
    target = folder / "changes" / "2026-11-21-first.json"
    target.write_text(json.dumps({"approved": {"by": "owner", "date": "2026-11-21"}}), encoding="utf-8")
    before = target.read_bytes()
    out = write(folder)
    assert (out["ok"], out["token"], out["details"]) == (
        False, "out-error", ["changes/2026-11-21-first.json is approved and is never replaced"])
    assert target.read_bytes() == before
    assert sorted(p.name for p in (folder / "changes").iterdir()) == ["2026-11-21-first.json"]


def test_writer_refuses_a_file_with_no_approved_field(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").mkdir()
    target = folder / "changes" / "2026-11-21-first.json"
    target.write_text("{}", encoding="utf-8")
    assert write(folder)["token"] == "out-error"
    assert target.read_text(encoding="utf-8") == "{}"


def test_writer_removes_left_over_temporary_files(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").mkdir()
    (folder / "changes" / ".architecture-records-17-3").write_text("x", encoding="utf-8")
    (folder / "changes" / ".gitkeep").write_text("", encoding="utf-8")
    assert write(folder)["ok"] is True
    assert sorted(p.name for p in (folder / "changes").iterdir()) == [".gitkeep", "2026-11-21-first.json"]


def test_writer_failure_is_out_error(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").write_text("not a folder", encoding="utf-8")
    out = write(folder)
    assert (out["ok"], out["token"]) == (False, "out-error")
    assert out["details"][0].startswith("could not create changes: ")
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_writer.py`
Expected: 6 failed (the module does not exist).

- [ ] **Step 3: GREEN.** Create `skills/shared/scripts/architecture-records/writer.mjs`:

```js
// The only module of the records tool that changes files: it writes one change file into <model>/changes.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from '../architecture-delta/errors.mjs';

// A temporary name the records reader ignores (it starts with `.`, records layout rule 7).
export const TEMP = /^\.architecture-records-[0-9]+-[0-9]+$/;
let counter = 0;

function attempt(what, rel, action) {
  try {
    return action();
  } catch (err) {
    if (err instanceof ToolError) throw err;
    throw new ToolError('out-error', `could not ${what} ${rel}: ${err?.code ?? err?.message ?? String(err)}`);
  }
}

// Spec, `change`: writes `changes/<id>.json` with `text` through a temporary file and a rename. An existing file of
// that id is replaced only when its `approved` is null (a draft); anything else is `out-error` and nothing changes.
// Left-over temporary files in `changes/` are removed first. `id` must already be a valid change id.
export function writeChange(modelDir, id, text) {
  const dir = path.join(modelDir, 'changes');
  const rel = `changes/${id}.json`;
  const target = path.join(dir, `${id}.json`);
  attempt('create', 'changes', () => fs.mkdirSync(dir, { recursive: true }));
  if (fs.existsSync(target)) {
    const current = attempt('read', rel, () => JSON.parse(fs.readFileSync(target, 'utf8')));
    if (current === null || typeof current !== 'object' || current.approved !== null) {
      throw new ToolError('out-error', `${rel} is approved and is never replaced`);
    }
  }
  for (const name of attempt('list', 'changes', () => fs.readdirSync(dir))) {
    if (TEMP.test(name)) attempt('remove', `changes/${name}`, () => fs.unlinkSync(path.join(dir, name)));
  }
  const temp = path.join(dir, `.architecture-records-${process.pid}-${counter}`);
  counter += 1;
  attempt('write', rel, () => fs.writeFileSync(temp, text, { encoding: 'utf8', flag: 'wx' }));
  attempt('replace', rel, () => fs.renameSync(temp, target));
}
```

- [ ] **Step 4: run GREEN.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_writer.py`
Expected: 6 passed.

- [ ] **Step 5: commit.**

```bash
git add skills/shared/scripts/architecture-records/writer.mjs tests/scripts/test_architecture_records_writer.py
git commit -m "feat(#31): the records writer - a draft change file is replaced, an approved one never"
```

---

### Task 6: the `change` command

**Tier:** standard — wiring of tested parts; complete code given.

**Files:**
- Create: `skills/shared/scripts/architecture-records.mjs`
- Test: `tests/scripts/test_architecture_records_change.py`

**Callers that move with this task:** none.

**Reviewer looks at:**
- the name is validated before it reaches a path — mutation: move the `nameProblems` check after `writeChange` — killed by: `test_change_refuses_bad_values_and_writes_nothing[name]`
- the before copy is loaded, not ignored — mutation: always use `EMPTY_EXPORT` — killed by: `test_change_lists_what_the_run_changed`
- `--before` inside or containing the model folder is refused — mutation: drop the `isInside(modelDir, before.path)` half — killed by: `test_before_must_be_inside_the_repo_and_apart_from_the_model[contains]`
- a `check` that fails stops the command — mutation: catch the `runCheck` error and write anyway — killed by: `test_change_refuses_bad_values_and_writes_nothing[check]`

- Satisfies Spec AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6 (with Task 5), AC-7, AC-8
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_records_change.py`:

```python
"""The architecture records tool, `change` (spec 2026-11-21-defining-architecture-records-design.md, "The helper
tool", "`change`")."""

from __future__ import annotations

import json
import shutil

import pytest

from arch_delta_support import RECORDS_SCRIPT, error_lines, make_repo, require_node, run_tool, unique, write_json

require_node()


def component(name: str, title: str) -> str:
    return f"    {name} = component '{title}' {{\n      metadata {{\n        code 'shop.{name}'\n      }}\n    }}\n"


def shop(parts: str, links: str) -> str:
    return f"model {{\n  shop = system 'Shop' {{\n{parts}{links}  }}\n}}\n"


BEFORE_MODEL = shop(component("a", "A") + component("b", "B") + component("c", "C"), "    a -> b\n")
AFTER_MODEL = shop(component("a", "A2") + component("b", "B") + component("d", "D"), "    a -> b\n    d -> b\n")
DEPS = [["shop.a.m", "shop.b.m"], ["shop.b.m", "shop.a.m"]]


def decision(id_: str, binds: list, reason: str = "Because.") -> dict:
    return {"id": id_, "decision": f"Decision {id_}.", "reason": reason, "rejected": [], "binds": binds,
            "status": "current", "evidence": "checked", "sources": ["src"]}


D1 = decision("D-1", ["shop.a"])
D2 = decision("D-2", ["shop.b"])
H1 = {"id": "H-1", "what": "Why does b call a?", "binds": ["shop.b"], "evidence": "search"}
C1 = {"id": "C-1", "name": "API", "owner": "shop.a", "bound": ["shop.b"], "obligations": ["O."], "compatibility": None}
KEYS = ["id", "date", "run", "asked_by", "summary", "rejected", "elements", "decisions", "holes", "contracts", "gap",
        "check", "approved"]


def change_repo(tmp_path):
    """A repository whose before copy is in build/before and whose model is the run's draft."""
    repo = make_repo(tmp_path, BEFORE_MODEL)
    folder = repo / "docs" / "architecture"
    write_json(folder / "decisions" / "x.json", {"title": "X", "decisions": [D1, D2], "holes": []})
    write_json(folder / "contracts" / "api.json", {"title": "API", "contracts": [C1]})
    shutil.copytree(folder, repo / "build" / "before")
    (folder / "model.c4").write_text(AFTER_MODEL, encoding="utf-8")
    write_json(folder / "decisions" / "x.json", {"title": "X", "decisions": [decision("D-1", ["shop.a"], "Changed.")],
                                                 "holes": [H1]})
    write_json(folder / "decisions" / "y.json", {"title": "Y", "decisions": [D2], "holes": []})
    (folder / "contracts" / "api.json").unlink()
    write_json(folder / "known-gap.json", {"entries": [{"from": "shop.b", "to": "shop.a", "reason": "b reads a."}]})
    write_json(repo / "build" / "deps.json", {"edges": DEPS})
    return repo


def change(repo, *extra: str, name: str = "first", before: str | None = "build/before", text: bool = True):
    args = ["change", "--repo", repo, "--deps", "build/deps.json", "--name", name, "--date", "2026-11-21",
            "--run", "epic"]
    if text:
        args += ["--asked-by", "#1", "--summary", "Did a thing."]
    if before is not None:
        args += ["--before", before]
    return run_tool(*args, *extra, script=RECORDS_SCRIPT)


def written(repo, name: str = "first") -> dict:
    return json.loads((repo / "docs" / "architecture" / "changes" / f"2026-11-21-{name}.json").read_text(encoding="utf-8"))


def test_change_lists_what_the_run_changed(tmp_path) -> None:  # AC-1
    repo = change_repo(tmp_path)
    proc = change(repo, "--rejected", "Keep c.")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "wrote changes/2026-11-21-first.json\n"
    data = written(repo)
    assert list(data) == KEYS
    assert data["elements"] == {"added": ["shop.d"], "changed": ["shop.a", "shop.b"], "removed": ["shop.c"]}
    assert data["decisions"] == {"added": [], "changed": ["D-1"], "removed": []}
    assert data["holes"] == {"added": ["H-1"], "changed": [], "removed": []}
    assert data["contracts"] == {"added": [], "changed": [], "removed": ["C-1"]}
    assert data["gap"] == {"added": [["shop.b", "shop.a"]], "removed": []}
    assert (data["run"], data["asked_by"], data["summary"], data["rejected"]) == ("epic", "#1", "Did a thing.", ["Keep c."])
    raw = (repo / "docs" / "architecture" / "changes" / "2026-11-21-first.json").read_bytes()
    assert b"\r" not in raw
    assert raw.startswith(b'{\n  "id": "2026-11-21-first",\n')
    assert raw.endswith(b"\n}\n")


def test_change_without_before_adds_everything(tmp_path) -> None:  # AC-2
    repo = change_repo(tmp_path)
    proc = change(repo, before=None)
    assert proc.returncode == 0, proc.stderr
    data = written(repo)
    assert data["elements"]["added"] == ["shop", "shop.a", "shop.b", "shop.d"]
    assert data["decisions"]["added"] == ["D-1", "D-2"]
    assert data["holes"]["added"] == ["H-1"]
    assert data["gap"]["added"] == [["shop.b", "shop.a"]]


def test_change_quotes_the_delta_check(tmp_path) -> None:  # AC-3
    repo = change_repo(tmp_path)
    write_json(repo / "build" / "deps.json", {"edges": [*DEPS, ["shop.d.m", "shop.a.m"]]})
    proc = change(repo)
    assert proc.returncode == 0, proc.stderr
    delta = run_tool("check", "--repo", repo, "--deps", "build/deps.json")
    assert delta.returncode == 1
    data = written(repo)
    assert data["check"] == {"exit": 1, "summary": delta.stdout.rstrip("\n").splitlines()[-1], "output": delta.stdout}


def test_written_change_exports_as_a_draft(tmp_path) -> None:  # AC-4
    repo = change_repo(tmp_path)
    assert change(repo).returncode == 0
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    [record] = json.loads(proc.stdout)["changes"]
    assert (record["id"], record["approved"]) == ("2026-11-21-first", None)


@pytest.mark.parametrize(("extra", "name"), [
    ([], "Bad_Name"),
    ([], "n" * 54),
    (["--rejected", ""], "first"),
], ids=["name", "long", "rejected"])
def test_change_refuses_bad_values_and_writes_nothing(tmp_path, extra: list, name: str) -> None:  # AC-5
    repo = change_repo(tmp_path)
    proc = change(repo, *extra, name=name)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: bad-input: changes/")
    assert not (repo / "docs" / "architecture" / "changes").exists()


@pytest.mark.parametrize(("flag", "value", "line"), [
    ("--date", "2026-02-30", "error: bad-input: changes/2026-02-30-first.json: date: not a real date"),
    ("--summary", "", "error: bad-input: changes/2026-11-21-first.json: summary: must be a non-empty string"),
    ("--asked-by", "", "error: bad-input: changes/2026-11-21-first.json: asked_by: must be a non-empty string"),
], ids=["date", "summary", "asked-by"])
def test_change_refuses_bad_text_and_dates(tmp_path, flag: str, value: str, line: str) -> None:  # AC-5
    repo = change_repo(tmp_path)
    args = ["change", "--repo", repo, "--deps", "build/deps.json", "--name", "first", "--run", "epic",
            "--before", "build/before"]
    values = {"--date": "2026-11-21", "--asked-by": "#1", "--summary": "S.", flag: value}
    proc = run_tool(*args, *[part for pair in values.items() for part in pair], script=RECORDS_SCRIPT)
    assert proc.returncode == 2
    assert line in error_lines(proc)
    assert not (repo / "docs" / "architecture" / "changes").exists()


def test_change_accepts_a_64_character_id(tmp_path) -> None:  # AC-5
    repo = change_repo(tmp_path)
    proc = change(repo, name="n" * 53)
    assert proc.returncode == 0, proc.stderr
    assert written(repo, "n" * 53)["id"] == "2026-11-21-" + "n" * 53


def test_change_stops_when_check_fails(tmp_path) -> None:  # AC-5
    repo = change_repo(tmp_path)
    (repo / "build" / "deps.json").write_text("{not json", encoding="utf-8")
    proc = change(repo)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: bad-input: --deps is not valid JSON")
    assert not (repo / "docs" / "architecture" / "changes").exists()


def test_change_replaces_its_draft_but_never_an_approved_file(tmp_path) -> None:  # AC-6
    repo = change_repo(tmp_path)
    assert change(repo).returncode == 0
    assert change(repo, "--rejected", "Second thoughts.").returncode == 0
    assert written(repo)["rejected"] == ["Second thoughts."]
    target = repo / "docs" / "architecture" / "changes" / "2026-11-21-first.json"
    data = written(repo)
    data["approved"] = {"by": "owner", "date": "2026-11-21"}
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    before = target.read_bytes()
    proc = change(repo)
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: out-error: changes/2026-11-21-first.json is approved and is never replaced"]
    assert target.read_bytes() == before


def test_flag_text_is_cleaned_by_export(tmp_path) -> None:  # AC-7
    repo = change_repo(tmp_path)
    esc = chr(27)
    args = ["change", "--repo", repo, "--deps", "build/deps.json", "--name", "first", "--date", "2026-11-21",
            "--run", "epic", "--asked-by", "#1", "--summary", f"{esc}[31mred{esc}[0m{chr(10)}line"]
    assert run_tool(*args, script=RECORDS_SCRIPT).returncode == 0
    [record] = json.loads(run_tool("export", "--repo", repo).stdout)["changes"]
    assert record["summary"] == f"red{chr(10)}line"


@pytest.mark.parametrize(("before", "token"), [
    ("outside", "outside-repo"),
    ("build/nothing", "bad-input"),
    ("docs/architecture", "bad-input"),
    ("docs/architecture/old", "bad-input"),
    ("docs", "bad-input"),
], ids=["outside", "missing", "model", "inside", "contains"])
def test_before_must_be_inside_the_repo_and_apart_from_the_model(tmp_path, before: str, token: str) -> None:  # AC-8
    repo = change_repo(tmp_path)
    (repo / "docs" / "architecture" / "old").mkdir()
    if before == "outside":
        elsewhere = tmp_path / unique("elsewhere")
        elsewhere.mkdir()
        before = str(elsewhere)
    proc = change(repo, before=before)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith(f"error: {token}: --before")
    assert not (repo / "docs" / "architecture" / "changes").exists()
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_change.py`
Expected: 19 failed (the script does not exist: Node exits 1 with "Cannot find module").

- [ ] **Step 3: GREEN.** Create `skills/shared/scripts/architecture-records.mjs`:

```js
#!/usr/bin/env node
// Architecture records: drafts the change file of a defining-architecture run.
// Changes files only through architecture-records/writer.mjs; never runs another program or uses the network.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError, clean } from './architecture-delta/errors.mjs';
import { startDeadline, loadRepoModel, readOptional, runCli } from './architecture-delta/load.mjs';
import { resolveInside, isInside } from './architecture-delta/paths.mjs';
import { readJson, parseGap } from './architecture-delta/inputs.mjs';
import { exportJson } from './architecture-delta/report.mjs';
import { runCheck } from './architecture-delta/check.mjs';
import { changeFileProblems } from './architecture-delta/records.mjs';
import { parseArgs } from './architecture-records/args.mjs';
import { buildChange, canonical, EMPTY_EXPORT } from './architecture-records/change.mjs';
import { writeChange } from './architecture-records/writer.mjs';

// The known-gap entries of a loaded model folder, read as the delta `check` reads them.
function readGap(loaded) {
  const ids = loaded.model.elements.map((element) => element.id);
  return readOptional(loaded.repo, null, path.join(loaded.modelDir, 'known-gap.json'), '--gap', (data) => parseGap(data, ids)) ?? [];
}

// Spec, `change`: --before resolves inside --repo (otherwise `outside-repo`), exists, and is apart from the model folder.
function locateBefore(repo, modelDir, value) {
  const before = resolveInside(repo, value, '--before');
  if (!before.exists || !fs.statSync(before.path).isDirectory()) throw new ToolError('bad-input', '--before directory not found');
  if (isInside(before.path, modelDir) || isInside(modelDir, before.path)) {
    throw new ToolError('bad-input', '--before must not be, contain or lie inside the model folder');
  }
  return before.path;
}

async function runChange(args, deadline) {
  const loaded = await loadRepoModel(args, deadline);
  const id = `${args.date}-${args.name}`;
  // The name is checked before it is used in any path.
  const nameProblems = changeFileProblems(`${id}.json`, {});
  if (nameProblems.length === 1 && nameProblems[0].endsWith(': -: not a valid file name here')) {
    throw new ToolError('bad-input', nameProblems);
  }
  const rel = `changes/${id}.json`;
  const existingPath = path.join(loaded.modelDir, 'changes', `${id}.json`);
  const existing = fs.existsSync(existingPath) ? readJson(existingPath, rel) : null;
  if (args.compare && existing === null) return { output: `missing ${clean(rel)}\n`, exitCode: 1 };
  const flags = {
    name: args.name,
    date: args.date,
    run: args.run,
    askedBy: args.askedBy ?? existing?.asked_by,
    summary: args.summary ?? existing?.summary,
    rejected: args.compare && args.rejected.length === 0 ? existing.rejected : args.rejected,
  };
  let before = EMPTY_EXPORT;
  let beforeGap = [];
  if (args.before !== null) {
    const prior = await loadRepoModel({ repo: loaded.repo, model: locateBefore(loaded.repo, loaded.modelDir, args.before) }, deadline);
    before = exportJson(prior.model, prior.records);
    beforeGap = readGap(prior);
  }
  deadline.check();
  const check = await runCheck({ deps: args.deps, gap: null, shards: null, scope: null, separator: args.separator, format: 'text' },
    deadline, loaded);
  const change = buildChange({ before, after: exportJson(loaded.model, loaded.records), beforeGap, afterGap: readGap(loaded), check, flags });
  const problems = changeFileProblems(`${id}.json`, change);
  if (problems.length > 0) throw new ToolError('bad-input', problems);
  if (args.compare) {
    const same = canonical(change) === canonical(existing);
    return { output: `${same ? 'same' : 'differs'} ${clean(rel)}\n`, exitCode: same ? 0 : 1 };
  }
  writeChange(loaded.modelDir, id, `${JSON.stringify(change, null, 2)}\n`);
  return { output: `wrote ${clean(rel)}\n`, exitCode: 0 };
}

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  const result = await runChange(args, deadline);
  deadline.stop();
  return result;
}

runCli(main);
```

- [ ] **Step 4: run GREEN and the earlier records tests.**

Run: `uv run pytest -q tests/scripts/ -k architecture_records`
Expected: all pass.

- [ ] **Step 5: commit.**

```bash
git add skills/shared/scripts/architecture-records.mjs tests/scripts/test_architecture_records_change.py
git commit -m "feat(#31): architecture-records change - drafts a run's change file from the before copy and the model"
```

---

### Task 7: `change --compare`

**Tier:** fast — the code is in Task 6 (`--compare` paths); this task adds its tests.

**Files:**
- Test: `tests/scripts/test_architecture_records_change.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- compare writes nothing — mutation: fall through to `writeChange` when the object differs — killed by: `test_compare_reports_same_differs_and_missing` (the folder snapshot)
- missing comes before the text flags — mutation: move the `missing` return below `changeFileProblems(…, change)` — killed by: `test_compare_reports_same_differs_and_missing` (no text flags given: the validator would give `bad-input`)

- Satisfies Spec AC: AC-9
- **Test retention:** **Permanent**

- [ ] **Step 1: RED, then GREEN.** Append:

```python
def snapshot(repo) -> dict:
    folder = repo / "docs" / "architecture" / "changes"
    return {p.name: p.read_bytes() for p in sorted(folder.iterdir())}


def test_compare_reports_same_differs_and_missing(tmp_path) -> None:  # AC-9
    repo = change_repo(tmp_path)
    assert change(repo, "--rejected", "Keep c.").returncode == 0
    files = snapshot(repo)
    same = change(repo, "--compare", text=False)
    assert (same.returncode, same.stdout) == (0, "same changes/2026-11-21-first.json\n"), same.stderr
    folder = repo / "docs" / "architecture"
    (folder / "model.c4").write_text(AFTER_MODEL.replace("    a -> b\n", "    a -> b\n    b -> d\n"), encoding="utf-8")
    differs = change(repo, "--compare", text=False)
    assert (differs.returncode, differs.stdout) == (1, "differs changes/2026-11-21-first.json\n"), differs.stderr
    missing = change(repo, "--compare", name="other", text=False)
    assert (missing.returncode, missing.stdout) == (1, "missing changes/2026-11-21-other.json\n"), missing.stderr
    assert snapshot(repo) == files
```

Run: `uv run pytest -q tests/scripts/test_architecture_records_change.py -k compare`
Expected: 1 passed. This task's test is written after the code it checks (Task 6 holds the `--compare` paths), so RED is shown by mutation instead: apply the first "Reviewer looks at" mutation, run the test, see it fail, revert.

- [ ] **Step 2: commit.**

```bash
git add tests/scripts/test_architecture_records_change.py
git commit -m "test(#31): change --compare reports same, differs and missing, and writes nothing"
```

---

### Task 8: the records tool's least privilege

**Tier:** fast — complete code.

**Files:**
- Test: `tests/scripts/test_architecture_records_safety.py`

**Callers that move with this task:** none.

**Reviewer looks at:**
- only the writer changes files — mutation: add `fs.writeFileSync('x', '')` to `change.mjs` — killed by: `test_only_the_writer_changes_files`
- no spawning or network — mutation: add `import cp from 'node:child_process';` to `args.mjs` — killed by: `test_records_tool_never_spawns_or_uses_the_network`

- Satisfies Spec AC: none (Scope's required check)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED, then GREEN.** Create `tests/scripts/test_architecture_records_safety.py`:

```python
"""Least privilege of the architecture records tool (spec 2026-11-21-defining-architecture-records-design.md, Scope
and Threat Model)."""

from __future__ import annotations

import re

from arch_delta_support import RECORDS_LIB, RECORDS_SCRIPT

CHANGES_FILES = re.compile(
    r"(?<!stdout\.)(?<!stderr\.)\bwrite(Sync)?\s*\("
    r"|\b(writeFile|appendFile|mkdir|rmdir|rm|unlink|rename|copyFile|cp|createWriteStream|symlink|link|truncate"
    r"|chmod|chown|utimes|mkdtemp|writev|ftruncate|futimes|lutimes|lchown|lchmod|fchmod|fchown)(Sync)?\s*\("
)


def sources() -> list:
    return [RECORDS_SCRIPT, *sorted(RECORDS_LIB.glob("*.mjs"))]


def test_only_the_writer_changes_files() -> None:
    checked = [source for source in sources() if source.name != "writer.mjs"]
    assert len(checked) >= 4
    for source in checked:
        assert not CHANGES_FILES.search(source.read_text(encoding="utf-8")), source


def test_records_tool_never_spawns_or_uses_the_network() -> None:
    forbidden = re.compile(r"child_process|worker_threads|fs/promises|node:(http|https|net|tls|dgram)\b")
    for source in sources():
        assert not forbidden.search(source.read_text(encoding="utf-8")), source


def test_files_are_opened_only_for_reading() -> None:
    for source in sources():
        assert not re.search(r"\bfs\.open\s*\(|\bopen\s*\(|openSync\(", source.read_text(encoding="utf-8")), source
```

Run: `uv run pytest -q tests/scripts/test_architecture_records_safety.py`
Expected: 3 passed. RED is shown by each "Reviewer looks at" mutation in turn (apply, run, see it fail, revert).

- [ ] **Step 2: run the full suite.**

Run: `uv run pytest -q` (about 3 minutes)
Expected: all pass.

- [ ] **Step 3: commit.**

```bash
git add tests/scripts/test_architecture_records_safety.py
git commit -m "test(#31): the records tool writes only through its writer and never spawns or uses the network"
```
