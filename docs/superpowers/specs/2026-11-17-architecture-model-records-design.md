# Architecture model records

Work item: #31, part A3a (A3 of #37). Amends `2026-11-09-architecture-delta-tool-design.md` and `2026-11-16-architecture-delta-runtime-links-design.md`.

## Why

A run of `defining-architecture` records decisions, open questions, shared contracts and what the run changed. Today they go into a hand-written `architecture.md` that nothing validates, so a reason can go on naming an element that no longer exists and nobody is told. Only a person can read the file reliably, and its sections are parsed by pattern when a document is generated from it (`docs/field-reports/2026-11-16-defining-architecture-first-run.md`, F2, F9, F12).

## What this work item owns

The data files that hold those records in the model folder, and the delta tool reading, validating and exporting them. It does not own the skill's steps or the other skills that read the model (#31 part A3b), any generated document (#32 to #34), or converting an existing model (#36).

## Layout

| Path in the model folder | Holds |
|---|---|
| `decisions/<group>.json` | The decisions and the holes (open questions, unexplained structure, contradictions) for one subject |
| `contracts/<group>.json` | The shared contracts for one boundary or subject |
| `changes/<date>-<name>.json` | One run: what it changed, choices not taken, its check result, its approval |
| `coverage.json` | What a baseline covered and which modules are deliberately unmapped |

`*.c4`, `c4.c4` and `known-gap.json` are unchanged. A model folder no longer has an `architecture.md`.

1. **A group is a file.** Its name, without `.json`, is the group. A decisions or contracts file name matches `^[a-z0-9]+(-[a-z0-9]+)*\.json$`, so the group is lower-case ASCII letters and digits in hyphen-separated parts (`memory`, `app-and-server`). Nothing depends on which group a record is in.
2. **A change file's name** matches `^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(-[a-z0-9]+)*\.json$`: its `date`, a hyphen, and a name of the same form as a group (`2026-11-16-baseline.json`).
3. **One record id space.** Decision, hole and contract ids are unique across the whole folder, so a record can move between files without breaking a link. A record id matches `^[A-Za-z0-9][A-Za-z0-9.-]*$` (ASCII). Change files have their own ids, their file names, which are unique because they are file names; a change id never clashes with a record id.
4. **Element ids are LikeC4's.** Wherever a record names an element (`binds`, `owner`, `bound`, `edge_nodes`, and a change's `elements` and `gap`), the value is any non-empty string; it is not held to rule 3, because LikeC4 allows other characters in its ids.
5. **Links point from a record to elements.** Elements carry no list of their decisions; "which records bind this element" is answered by reading the records.
6. **Each list is sorted by id on its own:** `decisions` and `holes` in a decisions file, `contracts` in a contracts file. Ids are compared as raw strings in UTF-16 code-unit order, the order the tool already uses for its output.
7. **Absent means empty.** A missing `decisions`, `contracts` or `changes` folder, or a missing `coverage.json`, is valid. The record reader ignores any file or folder whose name starts with `.` (such as `.gitkeep`) inside `decisions/`, `contracts/` and `changes/`. The model-folder walk is unchanged and still counts and checks every file.

## Records

Every file is one JSON object. Every field below is required unless marked optional. "Text" means a non-empty string. "Element id" means the id of an element in the loaded model. A list may be empty unless it says "at least one".

**Decisions file:** `title` (text), `decisions` (list), `holes` (list).

| Decision field | Value |
|---|---|
| `id` | an id |
| `decision` | text |
| `reason` | text, or `null` when no reason is recorded |
| `rejected` | list of text: alternatives not taken |
| `binds` | list of element ids; empty means the whole system |
| `status` | `current`, `partly-built`, `planned` or `superseded` |
| `superseded_by` | the id of a decision; present exactly when `status` is `superseded` |
| `evidence` | `checked` (against the code), `code` (stated in a code comment) or `spec` (stated in a document, not re-checked) |
| `sources` | list of text: paths or references |
| `note` | optional text |

| Hole field | Value |
|---|---|
| `id` | an id |
| `what` | text |
| `binds` | list of element ids |
| `evidence` | `checked`, `code`, `spec`, or `search` (a source was looked for and not found) |
| `note` | optional text |

**Contracts file:** `title` (text), `contracts` (list).

| Contract field | Value |
|---|---|
| `id` | an id |
| `name` | text |
| `owner` | an element id |
| `bound` | list of element ids, at least one |
| `obligations` | list of text, at least one |
| `compatibility` | text, or `null` when none is stated |
| `notes` | optional list of text |
| `decisions` | optional list of decision ids |
| `capabilities` | optional list of text: the epic capabilities that depend on it |

**Change file:**

| Field | Value |
|---|---|
| `id` | the file's name without `.json` |
| `date` | a real calendar date, `YYYY-MM-DD`, equal to the start of the file name |
| `run` | `baseline`, `epic` or `later-stage` |
| `asked_by` | text: the work item or stage that asked |
| `summary` | text |
| `rejected` | list of text: choices this run did not take |
| `elements`, `decisions`, `holes`, `contracts` | each an object with lists `added`, `changed` and `removed`; element ids for `elements`, record ids for the others |
| `gap` | an object with lists `added` and `removed`, each item a pair of two non-empty strings `[from, to]` |
| `check` | an object: `exit` (0 or 1), `summary` (text), `output` (text) |
| `approved` | `null`, or an object: `by` (text) and `date` (a real `YYYY-MM-DD` date) |

Ids in a change file are history. They are checked for form only (rule 3 for record ids, rule 4 for element ids), never looked up in today's model, because a run may have removed what it names.

**Coverage file:** `answer` (text); `baselined` (list of objects: `prefix`, text, and `run`, a change id); `edge_nodes` (list of objects: `element`, an element id, and `run`, a change id); `counts` (object: `modules` and `groups`, each a whole number of 0 or more); `unmapped` (list of objects: `module` and `reason`, both text). `run` names the change file of the run that added the entry: it equals the name, without `.json`, of a file in `changes/` that passes pass 1.

## What the tool checks

`export` and `check` both read and validate the records immediately after the model has loaded, before any other input (`--deps`, the gap file, `--scope`, `--shards`) is read. When the records have any problem the command stops there with exit 2, whatever `check` would otherwise have found, and no other input is read. A plan or review never runs on a model whose records point at something that is not there. The deadline is checked after reading each record file, as it is after each input file.

The tool reads only `decisions/*.json`, `contracts/*.json`, `changes/*.json` and `coverage.json`. Other files in the model folder are ignored by the record reader, as today, and so are files and folders inside the three record folders whose name starts with `.` (layout rule 7).

**Passes.** Each file goes through five passes in this order. A file that fails pass 1 or 2a is not read further.

1. **Layout.** A file in `decisions/`, `contracts/` or `changes/` whose name breaks layout rule 1 or 2; a folder inside one of them; a `decisions`, `contracts` or `changes` path that is a file; a `coverage.json` that is a folder. A misnamed file is reported and not read, so its ids never enter the id space.
2. **Shape.** (a) The file is not valid JSON, or not an object. (b) A required field is missing, a field is not in the tables, a value has the wrong type, or a list that needs at least one item has none.
3. **Ids.** A record id that breaks layout rule 3; the same value in the `id` field of two decision, hole or contract records anywhere in the folder; a change file whose `id` is not its file name; an element id that is an empty string.
4. **Links.** An element id in `binds`, `owner`, `bound` or `edge_nodes` that is not an element; a `superseded_by`, or an entry in a contract's `decisions`, that names no decision; `superseded_by` naming the record's own id; a coverage `run` that names no change file; the same id twice in one `binds` or `bound` list, or in a contract's `decisions` list.
5. **Order and values.** A list not sorted by id; `superseded_by` present when `status` is not `superseded`, or missing when it is; a `status`, `evidence` or `run` value outside its list; a `date` that is not a real `YYYY-MM-DD` date; a change file whose `date` is not the start of its name; a `check.exit` other than 0 or 1.

**References are not ids.** Record ids in a change file's lists, in `superseded_by` and in a contract's `decisions` are references to records, not records. They are checked for form, and `superseded_by` and a contract's `decisions` for links, but they never count as a second occurrence of an id.

**What a shape problem leaves in.** A record whose `id` is missing, not a string or breaks rule 3 is left out of the id, link and order checks. Any other shape problem leaves the record in. A field whose value has the wrong type is skipped by passes 3 to 5 (it is not form-checked, link-checked or value-checked); the items of a list that have the right type are checked. An element id or a record-id reference reported in pass 3 is not link-checked. A chain of `superseded_by` links may form a cycle; that is allowed.

The tool does not check that a reason is true, that a source exists, or that an element has any record.

**How it fails.** Exit 2, nothing on stdout, and on stderr one line per problem:

`error: record-error: <path>: <field path>: <what is wrong>`

- `<path>` is relative to the model folder, with `/` as separator on every platform (`decisions/memory.json`). A folder problem uses the folder's path (`decisions`).
- `<field path>` names where in the file: keys joined with `.`, list positions as `[i]` counted from 0 in the order the file holds them (`decisions[3].binds[0]`). A missing field gets the path it would have; an unknown key, its own path; a problem with the file or folder as a whole, `-`; an order problem, `<list>[i].id` for the smallest `i` whose id is less than the id at `i-1`, among the records left in; a change file's id mismatch, `id`.
- A duplicate record id gives one line for each occurrence after the first, in folder order, at that occurrence's `id` path, naming the path of the first occurrence. Folder order is the files' paths sorted in UTF-16 code-unit order, then position in the file.
- Lines are sorted by path in UTF-16 code-unit order. Within one file they come in pass order; within a pass, by record position, then in the order the fields appear in the tables above, with unknown keys after the table fields in file order. Folder-level lines sort with their folder path.
- Every problem is reported in one run. Lines are cleaned and cut as all error lines are.

A record problem is always `record-error`, including a file that is not valid JSON; record files are not read with the gap file's reader, so they never give `bad-input` or `file-size`. `known-gap.json` keeps its own validation and its `bad-input` errors.

## What `export` prints

`format` is 3. After `elements`, `allowed` and `runtime`, the object has:

- `groups`: one entry per decisions or contracts file, `{ "kind": "decisions" | "contracts", "group": …, "title": … }`, sorted by kind, then group.
- `decisions`, `holes`, `contracts`: every record from every file, each with its fields as written plus `group`, sorted by id.
- `changes`: every change record as written, sorted by id.
- `coverage`: the coverage object as written, or `null` when there is no `coverage.json`.

Each record object keeps its own keys in the order the file holds them, with `group` added last. Optional fields left out of a record stay out. Ids, element ids (including the pairs in a change's `gap`) and group names are cleaned like every other id the tool prints. All other text in a record keeps line feeds and every visible character, with no length cut; escape sequences and every other control character are removed. `check`'s output does not change.

## Compatibility

A model folder with none of the new files exports and checks as before, apart from `format` 3 and the empty new lists. A folder that still holds an `architecture.md` is not affected by it: the tool ignores the file. A folder that already uses a `decisions`, `contracts` or `changes` subfolder for something else, such as `.c4` files, now fails pass 1; no known model does. Converting the one existing model is #36.

## Scope

- A new tool module that reads and validates the records, beside the existing ones; the existing loader and report modules wired to it; a text-cleaning function without the length cut in the errors module.
- Tests beside the existing delta tool tests, building their model folders in the test as the existing tests do.
- The 2026-11-09 delta tool spec: a note pointing here for the inputs, the `export` shape, the exception to its Cleaning rule for record text, and `record-error` added to its list of exit-2 tokens. The runtime-links spec: a note that `format` is now 3.
- `ARCH_STANDARDS.md`, delta tool flags: one line saying `export` also prints the records and that a record problem is `record-error`. The rest of the skill's text is A3b.
- Required check that is not an acceptance criterion: every existing delta tool test passes, and the only edits to them are in the `export` tests, for `format` 3 and the new keys.

**Out of scope:** writing or converting records; generating documents; the skill's steps, standards and rubric beyond the one line; the other skills that name `architecture.md`; a check that sources exist.

## Threat Model (CIA)

| Pillar | Vector | Defence and proof |
|---|---|---|
| Confidentiality | A record file is used to read something outside the repository. | The tool reads only the fixed paths in the layout, inside the model folder, which is resolved inside `--repo` (`paths.mjs` `resolveInside`) and walked for links before anything is read (`walk.mjs` `walkModelDir` refuses any link). |
| Integrity | Record text printed by `export` holds terminal escape sequences or control characters that change what a reader sees. | The escape and control-character patterns already used by `clean` (`skills/shared/scripts/architecture-delta/errors.mjs`, `ANSI`, `CONTROLS`) are applied to all record text, keeping only line feeds. AC-12. |
| Integrity | A record names an element that no longer exists, so a document gives a reason for something that is gone. | Link checks, pass 4 of "What the tool checks"; exit 2. AC-3, AC-4, AC-15. |
| Integrity | Hostile JSON: a `__proto__` key, or the same key twice. | Unknown keys are refused, as `inputs.mjs` `onlyKeys` does for the gap file. Lookup tables built from record ids use `Object.create(null)` or `Map`, as `parseShards` does (`inputs.mjs`). A key given twice is resolved by `JSON.parse` to its last value; that is accepted, since the file is repository content. |
| Integrity | Two branches each add a record with the same id; the merge holds both. | One id space checked across the folder; exit 2. AC-5. |
| Availability | Very many or very large record files. | The model-folder limits are checked before anything is read (2,000 files, 50 MB in total: `walk.mjs`), which also bounds every record file; the deadline is checked after each record file. Validation is one pass per file plus set lookups. |
| Least privilege | None added. | The tool reads only inside the model folder, which `walk.mjs` has already checked for links; the source test (no `child_process`, no `worker_threads`, no `fs` write) and the no-network test run unchanged (`tests/scripts/test_architecture_delta_safety.py`). |
| Supply chain | None added. | JSON only; no new dependency (`package.json`). |

## Acceptance criteria

- **AC-1** Given a model with no `decisions`, `contracts` or `changes` folder and no `coverage.json`, when `export` runs, then it exits 0, `format` is 3, `groups`, `decisions`, `holes`, `contracts` and `changes` are empty lists, and `coverage` is `null`.
- **AC-2** Given valid decisions, contracts, change and coverage files in two groups, when `export` runs, then every record appears in its list with its fields as written and its `group`, sorted by id; `groups` lists each file with its title; and an optional field left out of a record is absent from the output.
- **AC-3** Given a decision whose `binds` names an element not in the model, when `export` runs, and again when `check` runs, then each exits 2 with an `error: record-error:` line naming the file, the field path and the id.
- **AC-4** Given one contract whose `owner` is not an element and another whose `bound` is empty, when `export` runs, then both problems are reported in the same run.
- **AC-5** Given id `X-1` on a decision in `decisions/a.json` and on a contract in `contracts/b.json`, when `export` runs, then it exits 2 with exactly one line for it, at the second occurrence in folder order naming the first (`contracts/b.json` sorts before `decisions/a.json`): `error: record-error: decisions/a.json: decisions[0].id: duplicate id X-1, first in contracts/b.json`.
- **AC-6** Given two decisions out of id order in one file, when `export` runs, then it exits 2 naming that file.
- **AC-7** Given a decision with status `superseded` and no `superseded_by`, one with `superseded_by` and status `current`, one whose `superseded_by` names no decision, and a contract whose `decisions` names a hole, when `export` runs, then each is reported.
- **AC-8** Given a decisions file whose `decisions[0]` has an unknown field `colour`, whose `decisions[1]` has no `reason`, and whose `holes[0].what` is a list, when `export` runs, then the lines name the field paths `decisions[0].colour`, `decisions[1].reason` and `holes[0].what`, in that order.
- **AC-9** Given a `status`, an `evidence` and a `run` value outside their lists, a change `date` of `2026-02-30`, and a `check.exit` of 2, when `export` runs, then each is reported.
- **AC-10** Given a file `Memory.json` in `decisions/`, a folder inside `contracts/`, and a change file whose `date` is not the start of its name, when `export` runs, then each is reported.
- **AC-11** Given a change file whose `elements.removed` lists an id that is not in the model, when `export` runs, then it exits 0.
- **AC-12** Given a reason of 500 visible characters holding an escape sequence and a line feed, when `export` runs, then the printed reason has all 500 visible characters and the line feed, and no escape sequence.
- **AC-13** Given a model whose records are invalid and code with no breach, when `check` runs, then it exits 2, not 0.
- **AC-14** Given one decisions file that is not valid JSON and another with an unknown field, when `export` runs, then the first is reported once with field path `-`, and the second's problem is reported too.
- **AC-15** Given a coverage file whose `edge_nodes[0].element` names an element not in the model and whose `baselined[0].run` names no change file, when `export` runs, then both are reported.
- **AC-16** Given a decision whose `superseded_by` is its own id, a decision whose `binds` lists one element twice, and two superseded decisions that name each other, when `export` runs, then the first two are reported and the cycle is not.
- **AC-17** Given a misnamed file `decisions/Memory.json` that holds a decision with id `M-1`, a well-named file holding another decision `M-1`, and a `decisions/.gitkeep`, when `export` runs, then the misnamed file is reported once with field path `-`, no duplicate id is reported, and `.gitkeep` is not mentioned.
- **AC-18** Given a model whose records are invalid and a `--deps` path that does not exist, when `check` runs, then the error lines are `record-error` lines and none is `bad-input`.

## Future work (downstream cost)

| Item | Priority | Effort | Where |
|---|---|---|---|
| The skill writes and reads these files; its steps are rewritten; the other skills stop naming `architecture.md` | P1 | L | #31 A3b |
| Model pack and architecture book generated from `export` | P1 | M | #32, #33 |
| Change document generated from a change file | P1 | S | #34 |
| A writer tool that creates records and change files, so a run need not hand-write JSON | P2 | M | #34 or later |
| Convert the downstream baseline | P1 | S | #36 |
| A check that each source path exists | P3 | S | Only if stale sources become a problem |

## Assumptions surface

| # | Assumption | Status |
|---|---|---|
| A1 | LikeC4 ignores JSON files in the folder it loads, including invalid ones. | VERIFIED: scratch run, a model folder with a malformed `decisions/memory.json` and `coverage.json` exported with exit 0. |
| A2 | The gap file's reader refuses unknown keys, and the same pattern serves the record files, which get their own reader so a record problem is always `record-error`. | VERIFIED: `inputs.mjs` `onlyKeys`, `readJson`. |
| A3 | Output cleaning removes escape sequences and control characters, including the line feed, and cuts at 200 code points. | VERIFIED: `errors.mjs` `ANSI`, `CONTROLS` (`\u0000-\u001f`), `MAX_POINTS`. |
| A4 | The model folder is walked for links, config files and size before LikeC4 loads it. | VERIFIED: `walk.mjs` `walkModelDir`, called from `loadRepoModel` in `architecture-delta.mjs`. |
| A5 | `export` prints `format` 2 with `elements`, `allowed`, `runtime`; existing export tests pin that shape. | VERIFIED: `report.mjs` `exportJson`; `tests/scripts/test_architecture_delta_export.py` lines 22, 23, 44, 182. |
| A6 | Exactly one model exists in the old layout. | VERIFIED by the owner (2026-11-16). |
| A7 | The owner chose JSON, several files grouped by subject, one file per run, and no converter in the engine. | VERIFIED: owner decisions of 2026-11-17, recorded on #31. |
| A8 | The owner accepts two fields added after the record design was approved: a `run` on each coverage entry, and an optional `capabilities` list on a contract. | VERIFIED: owner confirmed on 2026-11-17. |
