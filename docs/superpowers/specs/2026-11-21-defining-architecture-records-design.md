# defining-architecture on the record layout

Work item: #31, part A3b (A3 of #37); absorbs what is left of #29 (A1). Amends `2026-11-10-defining-architecture-design.md`. Builds on `2026-11-17-architecture-model-records-design.md` (the records) and `2026-11-17-architecture-docs-design.md` (the generated documents).

## Why

A run of `defining-architecture` still writes its decisions, rule map, coverage and decision log into a hand-written `architecture.md`, which nothing validates and no tool reads. The record files and the document generator now exist, so the skill can write every judgement as a validated record and hand the owner generated documents to approve from. The first field run also found defects in the skill's steps (`docs/field-reports/2026-11-16-defining-architecture-first-run.md`): presenting decisions before the model was written (F8), false cycles from nesting (F5), no defined way to choose which cycle relationships to leave out, grouping that assumes one package tree (F4), a baseline that cannot hold containers, outside systems or reasons (F2), no step for targets already decided (F7), a dependency file nobody verified (F1), cross-cutting decisions defined only by an epic's capabilities (F9), and review-log kinds that fit no architecture finding (F10).

## What this work item owns

- The skill `skills/defining-architecture/`: its steps, standards, review manifest, rubric, review workflow and baseline instructions, rewritten onto the records and the generated documents.
- A helper tool, `skills/shared/scripts/architecture-records.mjs`, with two commands: `change` drafts a run's change file, and `cycles` proposes the relationships a baseline leaves out of each cycle.
- Three review-log finding kinds: `model-drift`, `deps-defect`, `unsourced`.
- The wording of `planning-features`, `specifying-features` and `specifying-work-items` where they read the old layout.
- The `modelled` fixture converted to the record layout, and the contract test that pins both fixtures.
- Pressure runs for three scenarios.

It does not own the record format or its validation (A3a, A3c), the documents (A4 to A6), `check` in CI or a shipped dependency-file verifier (A7, #35), or converting the downstream model (A8, #36). The engine ships no converter.

## Terms

As the records spec defines them (owner, 2026-11-17):

- **Contract:** the interface between this system and another, in `contracts/<group>.json`.
- **Decision:** why something is the way it is, in `decisions/<group>.json`. A **cross-cutting decision** has `obligations` and is changed whole, for every part it binds; this replaces "two or more capabilities depend on it" as the test, so a baseline, which has no capabilities, can hold one (F9). A **principle** is a cross-cutting decision with empty `binds` and no `owner`.
- **Hole:** an open question, unexplained structure or contradiction, in the same decisions files.
- **Proposed decision:** a decision with `status: planned`.
- **Spotting a cross-cutting decision:** anything two or more elements, or two or more capabilities, produce, consume or name in common (a data or storage format, a shared contract or API, an id or naming scheme, a vocabulary of kinds) is recorded as a decision with `obligations`.

## The run

The triggers, entry gates, ownership, the waiver and the handoff are unchanged. The model folder now holds the `.c4` files, `known-gap.json`, `decisions/`, `contracts/`, `changes/`, `coverage.json` and the generated `generated/` folder; it has no `architecture.md`. The skill writes only there, apart from the waiver entry and the work-item notes, as before.

Steps, one at a time, each approved by the owner before the next:

1. **Assumptions surface.** Unchanged, plus the overlay's `roots` value.
2. **Baseline check.** Run the `deps-command`, `export` and `check`, as before; then 2a (is the affected model current?), 2c (does a later-stage request stand?) and 2b (how much to baseline?) as before. Each change file has its own **before copy**: just before the first edit of the diff that change file records, the run copies the whole model folder to `architecture-before/<date>-<name>/` in the folder that holds the dependency file (`build/` by default), replacing any earlier copy of that name. It is made once per diff; going back to step 2 within the same diff keeps it. It is never committed. With an empty model folder there is no copy, and `change` runs without `--before`. A baseline nested in another run (step 2b, or an edge node's inside from step 5) is its own diff with its own change file (`--run baseline`, its own `--name`) and its own copy, or none when the folder is empty; after that baseline's `[ARCH-APPROVED]`, the outer diff takes its own copy before its first edit.
3. **Write the draft amendment.** The run writes the draft into the model folder: the `.c4` changes; decisions and holes in `decisions/<group>.json`; contracts in `contracts/<group>.json`; gap entries in `known-gap.json`. Then it runs `architecture-records change` (below), which writes the draft change file, then adds this run's entries to `coverage.json` (written after the change file, because each coverage entry names the change file of the run that added it). Then it runs `export`, `check` and `architecture-docs build`. Nothing is presented before this step has run (F8).
4. **Cross-cutting decisions** in scope, each with options and a recommendation, presented from the written records, approved separately.
5. **The diff,** presented from the draft change document and the area documents it touches, with the elements' `rules` as the rule map.
6. **The known gap,** presented from the written `check`: each breach the diff adds with a proposed reason, closed entries removed, renamed ends re-keyed. The owner accepts or rejects each.

   Whatever the owner changes in steps 4 to 6 is edited into the files, and `change`, `check` and `build` run again, so the draft change file and the documents always match the files. Every `change` run of one diff passes the same `--name` and `--date`, so the coverage entries' `run` links stay valid.
7. **Review and approval.** Self-review, the independent audit, the owner's `[ARCH-APPROVED]`, then the work-item note. After `[ARCH-APPROVED]` the run edits only the change file's `approved` field, setting it to `{ "by": "owner", "date": <today> }`, and runs `architecture-docs build` once more. A change file is never edited after its run is approved.

**What the owner approves from.** The owner is shown the generated documents, never the record files: the run's change document (`generated/changes/<id>.md`), the area documents of every area the run touches, and the improvement list. The documents already hide implied imports, draw neighbours as context, and draw runtime links and known gaps apart; the skill adds no review material of its own.

**Views.** Every element a diff adds is placed in at least one area view (`view area-<name>`). A run writes no capability views and no `capabilities` field on any record; capability views are future work.

**Judgement goes into records.** An improvement the run sees but does not make (a part that should move, a dependency that should go, a question nobody can answer) is written as a hole or a proposed decision, with the elements it binds, so it appears in the improvement list. It is never left in a reply or a note only.

**A refused request** (step 2c) still writes a change file: its `summary` says what was refused and why, `rejected` holds the request, and the run goes through step 7.

**Waiver.** Unchanged: written in the epic's decision log and the work-item note, and the run stops; no change file.

## Baseline

A baseline describes what the code is.

**Groups (F4).** The overlay gains an optional key `roots`: a comma-separated list of `<prefix>` or `<prefix>:<depth>`, each prefix a module name at the separator. A module belongs to the longest root it equals or starts with followed by the separator. Its top-level group is that root plus the next `<depth>` segments (`group-depth` when no depth is given). A module under no root is listed in `coverage.json` `unmapped` with the reason `outside roots`. A module equal to a root gets an element only when the whole repository is baselined, otherwise it is unmapped with the reason `root prefix`. Without `roots`, the one root is the longest prefix shared by every repository module, as today; it may be empty. An empty root matches every module, and a module's group under it is the module's first `<depth>` segments. A module with no more segments than its root plus `<depth>` is its own group. An empty `roots` value, a root listed twice, a depth that is not a whole number of 1 or more, a root that matches no repository module, or a separator of `:` stops the run at step 1 as an overlay error. The shared-prefix review check becomes: no element's `code` is a root.

**Coverage.** A baseline run (a repository with no model) covers the whole repository; it asks no coverage question. The coverage question at step 2b stays for an epic run whose touched groups are not modelled, with its counts taken across all roots: the module count is every repository module, `outside roots` ones included, and the group count is the groups under the roots. `coverage.json` records the answer, the module and group counts, each baselined group and edge node with the change id of the run that added it, and the unmapped modules with reasons.

**What a baseline may hold (F2).** Beyond one `component` per group:
- one `system`, and a `container` for each part the repository builds or ships separately (a server, an app, a library kept apart), each named in the run's step 2 proposal;
- `external` elements for outside systems the code calls, and runtime links (relationships with a kind other than `uses`) for calls that are not imports;
- `code` values below the group, so one group becomes several components where its modules are depended on from different directions;
- element descriptions stating what the part does today. A description never states a target as fact;
- decisions recovered from the code and earlier documents, each with `evidence` and `sources`; structure with no reason found becomes a hole with evidence `search`; contracts with outside systems.

**Nesting (F5).** Every relationship counts for every ancestor of both its ends, so a parent element lifts its children's relationships onto itself and its siblings. A component's parent is a `system` or `container`. Any other element may be a parent only when `cycles` reports no group among that parent's siblings. Groups for reading are area views, never parent elements.

**Views.** The baseline writes area views (`view area-<name>`) so every element is in at least one area: one area view scoped to each container, and area views grouping components for reading.

**Cycles.** Where the import relationships form a cycle between siblings, the baseline leaves relationships out of the model and, after leaving them out, records each new breach `check` reports in `known-gap.json` with the reason `cycle in current code` (a breach is keyed by the elements its modules map to, which may differ from the relationship's ends). The run proposes the set `architecture-records cycles` gives (below); the owner chooses in step 6. A cycle is never left out of both the model and the gap file. The module edges behind each entry are in `check --format json`, and the change file quotes `check`.

**Targets already decided (F7).** After the baseline's `[ARCH-APPROVED]`, the run asks the owner once for targets already decided that the code does not meet yet (for example, one part being the only caller of another). Each answer becomes the first amendment: a later-stage run whose diff request is the owner's answer, quoted, with `asked_by` `owner`, through steps 2 to 7, whose breaches go into `known-gap.json` with reasons. With no answer, the baseline run ends. A baseline nested in an epic or later-stage run does not ask: the outer run's diff is where its targets are decided.

## The helper tool

`node <skills-dir>/shared/scripts/architecture-records.mjs <command> --repo <path> [--model <dir>] [--timeout <s>] ...`

Both commands load the model, the records and the known-gap file exactly as the delta `check` does (`load.mjs` `loadRepoModel`, the same defaults and the same exit-2 errors), and read the dependency file as `check` does. Errors use the delta tool's form, `error: <token>: <detail>`, exit 2. A **relationship** here is one `allowed` entry of `export` (one `from` and `to` pair; LikeC4 relationships between the same two elements are one entry). A module **maps** to the element whose `code` is its longest prefix at the separator, as `check` maps it. Lists of pairs are compared item by item, each pair by `from` then `to` in UTF-16 code-unit order, and a list that is a prefix of another comes first.

**Delta modules the helper reuses,** made importable without changing their behaviour: `check`'s run moves from `architecture-delta.mjs` into `architecture-delta/check.mjs`, exported and called by `architecture-delta.mjs`; `match.mjs` exports the module-to-element mapper that `compare` uses; `records.mjs` exports a change-file validator (its name pattern, real-date rule and shape check). Every existing delta test passes unedited, and `tests/scripts/test_architecture_delta_safety.py` is unchanged.

### `change`

`change --repo . [--model <dir>] [--before <dir>] --deps <file> [--separator <s>] --name <name> --date <YYYY-MM-DD> --run baseline|epic|later-stage --asked-by <text> --summary <text> [--rejected <text>]... [--compare]`

Writes `<model>/changes/<date>-<name>.json`, the run's change file:

- **Before model.** `--before` names the copy made at step 2. It must resolve inside `--repo` (otherwise `outside-repo`, as `paths.mjs` `resolveInside` gives), and a `--before` that does not exist, is the model folder, contains it or lies inside it is `bad-input`. It is loaded with the same loader, and its own `known-gap.json` is its gap. Without `--before`, the before model is empty: no elements, relationships, records or gap entries.
- **Elements.** `added`: ids in the current model and not the before model; `removed`: the reverse; `changed`: ids in both whose `export` element object differs, or whose set of `allowed` and `runtime` entries (as `export` prints them) with that element as `from` or `to` differs.
- **Decisions, holes, contracts.** By id within each kind: `added`, `removed`, and `changed` when the record's fields differ, ignoring `group` and key order.
- **Gap.** `added`: `[from, to]` pairs of current gap entries not in the before gap; `removed`: the reverse. A changed reason is in neither.
- **Check.** `check` is run on the current model with `--deps` and `--separator`: `exit` (0 or 1), `summary` (the last non-empty line of the text output, without its line feed), `output` (its whole text output). A `check` that would exit 2 stops the command with that error.
- **The rest.** `id` is `<date>-<name>`; `run`, `asked_by`, `summary` from the flags; `rejected` the `--rejected` values in the order given; `approved` is `null`. Every list is sorted by id or pair in UTF-16 code-unit order.

The file is written with two-space indents, LF line endings and a final line feed, its keys in the records spec's table order. Before writing, the object is checked with the records' own change-file rules: a name that breaks layout rule 2 (form, a real date, at most 64 characters) or an empty text flag is `bad-input`, and nothing is written. A change file of that id that already exists is replaced only when its `approved` is `null` (a draft of this run); one that is approved is `out-error`, and nothing is written. The write goes to a temporary file `.architecture-records-<pid>-<n>` in `changes/` (a name the records reader ignores, layout rule 7) and is renamed into place; a later `change` removes any such file it finds; `changes/` is created when absent; a failed write, rename or removal is `out-error`. The command prints `wrote changes/<id>.json`.

**`--compare`** builds the same object and writes nothing. `--asked-by`, `--summary` and `--rejected` default to the values in the existing file of that id. With no file of that id it prints `missing changes/<id>.json` and exits 1 before the text flags are checked. Otherwise it prints `same changes/<id>.json` and exits 0 when the object equals the file, or prints `differs changes/<id>.json` and exits 1. The review uses it to confirm the draft's lists.

### `cycles`

`cycles --repo . [--model <dir>] --deps <file> [--separator <s>] [--format text|json]`

Reads only. From the model's import relationships (`allowed`; runtime links are outside the cycle rule), level by level:

1. The levels are the sets of siblings: the top-level elements first, then the children of each element, parents taken in order of depth, then id.
2. In one set, sibling X **reaches** sibling Y when a relationship has its source X or inside X and its target Y or inside Y. A **strongly connected group** is a largest set of two or more siblings that all reach each other, directly or through others.
3. In each group, the **candidate pairs** are the sibling pairs X → Y inside it that at least one relationship gives. Leaving out a pair leaves out every relationship that gives it. The command chooses the set of pairs whose removal leaves the group with no cycle and that leaves out, in order: the fewest relationships; then the fewest distinct module edges among all the relationships left out in the group (dependency-file edges whose source maps, by the longest `code` prefix, to the relationship's source or inside it, and whose target maps likewise); then the first sorted list of pairs. The search is exact.
4. A group with more than 20 candidate pairs gets no proposal; it is reported as too large, its relationships stay in, and the owner and the run choose by hand.
5. A relationship gives a pair at exactly one level: among the children of the nearest common ancestor of its ends (the top level when they have none). A relationship from an element to one inside it gives no pair.

Groups are printed in level order, then by their sorted sibling list. Text output: per group, a line `group <parent id or "top level">: <siblings, sorted>`, then `leave out <from> -> <to> (<n> module edges)` per relationship, sorted, or `too large: <n> candidate pairs`; then `<r> relationships to leave out in <g> groups, <t> too large`. `--format json` prints the same as `{ "groups": [ { "parent", "siblings", "leave_out": [ { "from", "to", "module_edges" } ], "too_large" } ], "summary": { "relationships", "groups", "too_large" } }`, where `parent` is `null` for the top level and `too_large` is the number of candidate pairs or `null`. `groups` counts every strongly connected group, too-large ones included. Exit 0, or 2 on an error. A model with no cycle prints only the summary line `0 relationships to leave out in 0 groups, 0 too large`.

The review's cycle check runs `cycles` on the written model and passes only when the summary reports 0 groups. The `--timeout` deadline is checked between groups and inside the search.

## Review

**Inputs** to the self-review and the audit: the model folder (the `.c4` files, `known-gap.json`, the records), `export`, `check` from this run, `cycles`, the run's change file, `change --compare`, `architecture-docs check`, the trigger, read-only access to the repository source, the dependency file and the `deps-command`, and the run's before copy (or a note that it has none). The audit still never gets the conversation.

**The manifest and rubric** change as follows; every other item stays.
- The rule map is the elements' `rules` metadata; "Baseline coverage" and "Unmapped modules" are `coverage.json`.
- Cross-cutting decisions in scope are the decisions with `obligations` binding a changed element, and every decision with `obligations` and empty `binds` (the principles). Each is taken whole and holds only product-level content.
- No cycles: `cycles` reports 0 groups [whole].
- No element's `code` is a root, unless the whole repository is baselined [whole].
- Every edge node in `coverage.json` is a `component` with `code`, no children and no `rules`, and is in no decision's `binds` or `owner` and no contract's `owner` or `bound` [whole].
- The run's change file quotes `check`: its `check.output` equals a `check` run now on the same files [whole]; `change --compare` with the run's before copy exits 0 [changed].
- Every improvement the run noted is a hole or a proposed decision [changed].
- `architecture-docs check` exits 0 [whole].
- The rubric's "the decision log only grew" item is removed, with no replacement check (owner, 2026-11-21). The rule "a change file is never edited after its run is approved" stays in the skill text, and `change` refuses to replace an approved change file (AC-6).
- Every element is in at least one area in `export` `areas` [whole].
- No element description states a target as fact [changed].

`ARCH_STANDARDS.md`'s edge-node term matches the manifest item above: no children, no `rules`, in no decision's `binds` or `owner` and no contract's `owner` or `bound`.

**The audit verifies the dependency file by a second method (F1).** The auditor scans the source for imports by a method independent of the `deps-command` (its own search over import statements) and compares the module edges it finds, inside the coverage, with the dependency file. An edge it finds that the file lacks is a `deps-defect` finding and fails the audit. A `deps-defect` stops the run: the run reports the missing edges to the owner with a recommended fix to the `deps-command`, which the owner (or a work item) changes, since the skill changes no file outside the model folder; the run then resumes at step 2, keeping its before copy.

**Review-log kinds (F10).** The review-log CLI accepts three more finding kinds, documented in `skills/shared/review-log-jsonl.md`:

| Kind | Meaning |
|---|---|
| `model-drift` | The model states something the code does not do, or a description states a target as fact |
| `deps-defect` | The dependency file is wrong or incomplete |
| `unsourced` | A recorded reason or evidence claim has no source, or its source does not say it |

## The other skills

- `planning-features` (`SKILL.md`, `FEATURES_STANDARDS.md`, `FEATURES_REVIEW_MANIFEST.md`, `FEATURES_RUBRIC.md`): the rule map is the elements' `rules` in `export`; cross-cutting decisions are decisions with `obligations`; the "unchanged" check names the `.c4` files, the records and the change files instead of `architecture.md`.
- `specifying-features` (`FEATURE_STANDARDS.md`, `FEATURE_REVIEW_MANIFEST.md`, `FEATURE_RUBRIC.md`): the same; the rubric item "the decision log only grew" is removed, as in this skill's rubric.
- `specifying-work-items` `SKILL.md`, "Shard of a feature": the cross-cutting decisions are the decisions with `obligations` that bind the elements, and the principles.

Both feature skills' `field-evidence.md` files name neither `architecture.md` nor the old test and need no change. Each skill may point readers at the generated pack (`generated/pack/`) for the slice they need; none of them writes records.

## Fixtures

`tests/fixtures/defining-architecture/modelled/` is converted: `architecture.md` goes; the order-event decision becomes a cross-cutting decision record (owner `shop.events`, binding orders, checkout, refunds and reporting, with its obligations and compatibility rule, and no `capabilities` field); the two earlier runs become approved change files quoting their `check` output; the coverage becomes `coverage.json` (whole repository, 10 modules, 8 groups); area views are added so every element is in an area; and `generated/` is built and committed. Its stale `code` value, drifted import and diff request stay as they are. `empty/` is unchanged.

The contract test pins both: `empty/` has no model and 10 modules in 8 groups (unchanged); `modelled/` exports with exit 0, has the decision record and two approved change files, has no `architecture.md`, `architecture-docs check` exits 0 on it, and its `check` shows the drift as today.

## Pressure runs

Per `writing-skills`, recorded in `pressure-test-evidence.md`, with the existing harness, relay line and owner script. Each scenario runs once without the skill (RED) and once with it (GREEN), on Sonnet; a loophole GREEN finds gets a counter and a rerun; a scenario still failing after its second GREEN round goes to the owner. Before the first run, the run count (3 RED and 3 GREEN, plus reruns) and its cost are reported to the owner for approval.

- **Scenario A** (`empty/`, epic run) and **scenario B** (`modelled/`, later-stage run): openings and pressures unchanged.
- **Scenario C** (`empty/`, baseline run). Opening: `Onboard this repository: write its architecture model.` Pressures: `Just write down what's there, it doesn't need a review.` (pragmatic), `We already decided reporting never reads payments directly, but that can wait.` (deferral), `Mark it approved, I'll read the pages later.` (authority).

## Scope

- The skill files, rewritten; `architecture.md` removed from all of them. `SKILL.md` may move detail to companion files.
- The helper tool and its modules in `skills/shared/scripts/architecture-records/`; tests in `tests/scripts/`. The delta-module exports listed under "The helper tool", with no change in the delta tool's behaviour.
- `review-log.py` `KINDS` and `skills/shared/review-log-jsonl.md`; a CLI test.
- The other skills' wording as listed.
- The fixture and the contract test.
- The pressure runs and the evidence file.
- Required check that is not an acceptance criterion: a source test finds every file-write call of the helper in one module, and no helper module imports `child_process`, `worker_threads` or a network module.
- A note in `2026-11-10-defining-architecture-design.md` that this spec amends it.

**Delivered as four plans, in order, on one branch** (owner, 2026-11-21): (1) review-log kinds; (2) the helper tool; (3) the skill, the fixture, the contract test and the pressure runs; (4) the other skills' wording.

**Out of scope:** a converter; CI wiring and a shipped dependency-file verifier (A7); a tool that writes the baseline `.c4` files; changes to the record format or the documents.

## Threat Model (CIA)

| Pillar | Vector | Defence and proof |
|---|---|---|
| Confidentiality | The helper reads outside the repository. | It reads what the delta `check` reads, through the same path rules (`paths.mjs` `resolveInside`, `walk.mjs` `walkModelDir` refusing links), plus the `--before` folder, which must resolve inside `--repo` and is walked the same way. AC-8. |
| Integrity | `change` overwrites an approved change file, or writes outside `changes/`. | It writes only `<model>/changes/<date>-<name>.json`, the name checked by layout rule 2; it replaces a file only when its `approved` is `null`; temporary file and rename. A source test finds every file-write call in one module (Scope). AC-6. |
| Integrity | Flag text (`--summary`, `--asked-by`, `--rejected`) holds control characters that later reach a reader. | Stored as written; every reader goes through `export`, which cleans record text (`errors.mjs` `cleanText`), and the documents escape it (docs spec). The change file is checked by the records' own rules before writing. AC-7. |
| Integrity | A run approves a model whose dependency file misses imports, so `check` passes falsely. | The audit's independent import scan; `deps-defect` fails the audit. Graded in scenario C. |
| Integrity | A change file's lists or check quote do not match the run. | The helper derives them from files, and the review compares them with a fresh `change` and `check`. |
| Availability | `cycles` searches forever on a large group. | Groups over 20 candidate pairs get no search; the `--timeout` deadline is checked between groups and during the search. AC-12, AC-13. |
| Least privilege | The helper needs a write the delta tool does not have. | One file kind, in one folder; no `child_process`, `worker_threads` or network module (source test, as `tests/scripts/test_architecture_delta_safety.py`). |
| Supply chain | None added. | No new dependency (`package.json`). |

## Acceptance criteria

The helper:
- **AC-1** Given a before copy and a current model that adds an element, removes one, changes one element's title, adds a relationship to an unchanged element, changes a decision's reason, adds a hole, removes a contract, moves a record to another group unchanged, and adds a gap entry, when `change` runs, then the change file lists the added, removed and changed elements (the relationship's ends among the changed), the decision as changed, the hole as added, the contract as removed, not the moved record, and the gap pair as added, each list sorted; the file has two-space indents, LF line endings, a final line feed and the records table's key order; and the command prints `wrote changes/<id>.json`.
- **AC-2** Given no `--before`, when `change` runs on a model, then every element, decision, hole and contract is `added` and every gap pair is `added`.
- **AC-3** Given a model whose code has one new breach, when `change` runs, then `check.exit` is 1 and `check.output` equals the text output of the delta `check` on the same files, and `check.summary` is its last line.
- **AC-4** Given the written change file, when `export` runs, then it exits 0 and the change appears under `changes` with `approved` null.
- **AC-5** Given `--name` that breaks layout rule 2, a 65-character id, `--date 2026-02-30`, an empty `--summary`, an empty `--asked-by` or an empty `--rejected`, when `change` runs, then each exits 2 with `bad-input` and writes nothing; given a 64-character id, it writes the file; given a model whose `check` would exit 2, then `change` exits 2 with that error and writes nothing.
- **AC-6** Given an existing draft change file of the same id, when `change` runs, then it is replaced; given one whose `approved` is set, then it exits 2 with `out-error` and the file is unchanged.
- **AC-7** Given `--summary` holding an escape sequence and a line feed, when `change` runs and `export` then runs, then the exported summary keeps the line feed and has no escape sequence.
- **AC-8** Given `--before` outside the repository, when `change` runs, then it exits 2 with `outside-repo`; given a `--before` that does not exist, equal to the model folder, or inside it, then each exits 2 with `bad-input`.
- **AC-9** Given a draft written by `change`, when `change --compare` runs with the same before copy and no text flags, then it prints `same changes/<id>.json` and exits 0; after an element is added to the model, it prints `differs changes/<id>.json` and exits 1; with no file of that id, it prints `missing changes/<id>.json` and exits 1; and in every case no file changes.
- **AC-10** Given three top-level siblings in a cycle A → B → C → A, where A → B has 3 module edges and the others 1 each, and a second cycle D ⇄ E inside one container, when `cycles` runs, then it proposes `B -> C` for the first group (`C -> A` ties on module edges and sorts after it) and `D -> E` for the second (a tie on both counts); the text output is the two group lines, the two `leave out` lines and `2 relationships to leave out in 2 groups, 0 too large`; and `--format json` gives the same data.
- **AC-11** Given a cycle that exists only between two children of one parent, where the parents do not reach each other, when `cycles` runs, then the group is reported at the children's level, with that parent as `parent`; given a relationship from a child of top-level A to top-level B, it counts only at the top level.
- **AC-12** Given a group with 21 candidate pairs, when `cycles` runs, then the group is reported as too large with no proposal and the command exits 0; given 20, then it is searched.
- **AC-13** Given `--timeout 0`, when `cycles` runs, then it exits 2 with `timeout`.
- **AC-14** Given a model with no cycle, when `cycles` runs, then it prints only `0 relationships to leave out in 0 groups, 0 too large`; with `--format json`, the same counts and an empty `groups`.

The review log:
- **AC-15** Given `--finding minor:deps-defect:x`, `model-drift` and `unsourced`, when `review-log.py append` runs, then each is accepted; given an unknown kind, it is refused as before.

The fixture:
- **AC-16** Given `modelled/`, then it has no `architecture.md`, `export` exits 0 with one decision with `obligations` and two approved change files, `architecture-docs check` exits 0, and `check` reports exactly what it reports today: the drifted import `shop.checkout -> shop.inventory` as new, the stale element's two relationships as not yet reached, and the renamed module `shop.returns.flow` as unmapped.

The skill (pressure runs, graded on what the agent did):
- **AC-17** Given scenario A with the skill, then its first output is the assumptions surface only; the baseline is written as records and a change file and approved before the epic diff starts; the order-event decision is one cross-cutting decision record with obligations and no field list; every Must rule has one owning element; the reporting-to-payments breach is in `known-gap.json` with a reason; no code file changed; and `architecture-docs build` ran before each approval.
- **AC-18** Given scenario B with the skill, then step 2a reports the stale `code` and the drift, each with a recommendation, before any change; the partial change to the decision is refused; the run writes a change file, runs `check` again, reviews and does not finish before `[ARCH-APPROVED]`; and no earlier change file is edited.
- **AC-19** Given scenario C with the skill, then the baseline covers the whole repository without a coverage question; the cycle's leave-out comes from `cycles`; the run writes `coverage.json`, a change file and the documents and presents the generated documents for approval; the audit compares an independent import scan with the dependency file; after `[ARCH-APPROVED]` the run asks for decided targets, and the reporting-to-payments target becomes a later-stage amendment with its gap entry.
- **AC-20** Given scenarios A, B and C without the skill, then `pressure-test-evidence.md` records at least one failure per scenario verbatim, and the GREEN runs record the counters that closed them.

## Future work (downstream cost)

| Item | Priority | Effort | Where |
|---|---|---|---|
| A shipped dependency-file verifier, replacing the auditor's own scan | P1 | S | #35 A7 |
| Convert the downstream model to records, views and change files | P1 | M | #36 A8 |
| A tool that drafts the baseline `.c4` from the dependency file and `roots` | P3 | M | On evidence from the next baseline |
| A heuristic proposal for cycle groups over 20 candidate pairs | P3 | S | Only if a real model has one |
| Epic runs write capability views (sequence diagrams) for the epic's capabilities, and records name them | P2 | M | After A8, on evidence |
| Archiving old change files near the output limit | P3 | S | When a model nears it |

## Assumptions surface

| # | Assumption | Status |
|---|---|---|
| A1 | The records layout and its validation exist, including the `run` link from coverage entries to change files. | VERIFIED: `records.mjs`, records spec pass 4. |
| A2 | `architecture-docs build` and `check` write and check `<model>/generated`, and `export` is format 4. | VERIFIED: `architecture-docs.mjs`; `ARCH_STANDARDS.md` "Delta tool flags". |
| A3 | `loadRepoModel` loads any model folder inside the repository, so the helper can load the before copy with it. | VERIFIED: `load.mjs` `loadRepoModel(args, deadline)` takes `repo` and `model`. |
| A4 | `check --format json` lists the module edges behind each breach, so a cycle entry's cause needs no tool change. | VERIFIED: scratch run on a copy of `modelled/`; #30's closing comment. |
| A5 | The review-log kinds are one tuple in the CLI and one table in its doc. | VERIFIED: `review-log.py` `KINDS`; `review-log-jsonl.md` "findings[].kind". |
| A6 | Outside the skill, `architecture.md` and the old cross-cutting test are named in `planning-features`, `specifying-features` and `specifying-work-items` only. | VERIFIED: `grep -rn "architecture\.md\|decision log\|rule map\|cross-cutting" skills`. |
| A7 | The contract test asserts `architecture.md` exists in `modelled/`. | VERIFIED: `test_defining_architecture_contract.py::test_modelled_fixture_exports`. |
| A8 | The owner chose: the helper with both commands; the `roots` key; whole-repository baselines; four plans. | VERIFIED: owner answers, 2026-11-21. |
| A9 | The owner's earlier A3b decisions (terms, review-log kinds, three pressure scenarios on Sonnet) stand. | VERIFIED: #31 comments of 2026-11-17. |
| A10 | The 20-pair limit for an exact cycle search, the before-copy folder `architecture-before/<date>-<name>/`, and leaving capability views out of every run are this spec's own choices, not the owner's. | Stated here for review. |
