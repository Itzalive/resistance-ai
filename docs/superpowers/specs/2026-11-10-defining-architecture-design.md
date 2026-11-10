# defining-architecture skill

Work item: #22. Part of #19. Depends on #20 (delta tool) and #21 (review-log phases), both merged.

## What changes and why

In a multi-feature epic, architecture decided one work item at a time shows up late as unplanned
refactors: several items restating one rule on separate entry paths, or a feature opening with a
"shard 0" of behaviour-free splits. The layering that prevents most of this is knowable when the
epic starts. This work item adds the skill that decides it: `skills/defining-architecture/`, which
keeps a target C4 model (LikeC4 `.c4` files) of the repository and amends it. It also moves the
delta tool's default model folder to `docs/architecture/`.

**Trigger.** A run starts in one of three ways, each with its own entry gate:

| Trigger | Entry gate |
|---|---|
| An epic needs its architecture (epic run) | The epic has `[EPIC-APPROVED]` |
| A later stage (`planning-features`, `specifying-features`, `specifying-work-items`) needs the model changed (later-stage run) | The model has `[ARCH-APPROVED]` and the asking stage has written a diff request (what to change and why) |
| A repository is onboarded with no model (baseline run) | None |

**Ownership.** This skill owns the model folder's content: the `.c4` files, `architecture.md` and
`known-gap.json`. It owns no code and changes none. Filling `close_by` on gap entries belongs to
`planning-features` (#23); the edits that hand off to this skill from `specifying-epics` and that
make `specifying-work-items` read the model belong to #25; the skill index and README to #25.

## Rules

**Every run is an amendment.** The current model is whatever is in the model folder. A run proposes
a diff to it: elements, relationships, tags, metadata and cross-cutting decisions added, changed or
removed, each with a reason and the stage that asked. Only the size differs: an epic run is a large
diff, a later-stage run a small one, and the first run in a repository amends an empty model.

**Empty model folder** means: the folder is absent, or holds no `.c4` file other than `c4.c4`.

**When an epic run is required.** Always, unless the owner agrees, from the epic's capabilities,
both that the epic ships as one feature and that no module is expected to be reached from two or
more entry paths. A waiver is written in the epic's decision log with both judgments and appended
as a note to the epic's work item, and the skill stops. No review-log entry is written for a
waiver.

**Overlay.** Repo-root `ARCHITECTURE_DESIGN.md` is optional. Under a heading `## Architecture`, one
`key: value` line per key:

| Key | Default | Meaning |
|---|---|---|
| `model` | `docs/architecture` | The model folder, relative to the repository root |
| `deps-command` | none | The command that writes the dependency file (`{"edges": [[from, to], ...]}`) |
| `deps-file` | `build/architecture-deps.json` | Where that command writes; inside the repository, not committed |
| `separator` | `.` | The module-name separator |
| `group-depth` | `1` | Segments below the shared prefix that make one top-level module group |
| `small-repo-modules` | `200` | Coverage question: at or under this many modules counts as small |
| `small-repo-groups` | `10` | Coverage question: at or under this many top-level groups counts as small |

The overlay may tighten this skill's rules, never weaken them. With no `deps-command`, the run stops
at step 1 and asks for one; it never guesses. Every tool call passes `--model <model>` and never
`--gap`, so the gap file is always `<model>/known-gap.json`; `check` calls also pass
`--separator <separator>` and `--deps <deps-file>` (`export` takes neither).

**Terms.**
- **Repository module:** a module that is the first item of at least one edge in the dependency
  file. A module that appears only as a target is outside the repository (a standard library or
  third-party package) and is never grouped, counted or modelled.
- **Top-level module group:** take the longest prefix, at the separator, shared by every repository
  module; a group is that prefix plus the next `group-depth` segments. A repository module equal to
  the shared prefix gets an element only when the whole repository is baselined; otherwise it is
  listed under "Unmapped modules" with the reason `shared prefix`, and it is never an edge node,
  because an element whose `code` is the shared prefix would match every uncovered module.
- **Not yet built:** an element with no `code` metadata (a conceptual element). An element with
  `code` is built: each `code` value must equal a module in the dependency file or a prefix of one
  at the separator.
- **Must rule:** every business rule owned by a Must Have capability of the epic. For an epic
  written before capabilities existed, every business rule tied to a Must Have item of its MoSCoW
  scope.
- **Edge node:** a `component` covering a neighbour group outside the baselined area, with `code`
  set to that group's prefix, no children, no `rules`, and no part in any cross-cutting decision.

**Cross-cutting decisions.** A decision that two or more capabilities depend on (a data or storage
format, a shared contract or API, an id or naming scheme, a vocabulary of kinds or types) is taken
whole: decided once, for every capability that needs it, including those built in later features.
Its section in `architecture.md` holds its name, its owning element, the elements and capabilities
it binds, the obligations it places on them at product level, and its compatibility or versioning
rule. Field lists and schemas are not in it; they belong to the first feature that builds it. The
bound-elements list is what the "changed" review scope is worked out from. A decision is used as is
or changed whole as part of a diff, never in part.

**Steps.** One at a time, each approved by the owner before the next. Each step covers only what
the diff touches, except where a check is marked "whole".
1. **Assumptions surface:** the trigger and its entry gate; required or waived (epic run); the
   overlay's values or their defaults; `deps-command` named; for an epic run, the epic's
   capabilities (or its MoSCoW scope). Anything missing stops the run.
2. **Baseline check.** Run `deps-command`, then `export` (skipped while the folder is empty) and
   `check`. A `check` exit 1 (a breach not in the gap, or a stale entry) is a finding for 2a; exit 2
   stops the run with the tool's error.
   - **2a. Is the affected model current and valid?** For every modelled element the run touches,
     its relationships and its gap entries:
     - valid: the model loads, the spec copy matches, and the relationships have no cycles;
     - a `code` value that matches no module (code moved, renamed or deleted);
     - a breach not in the gap file (code drifted from the target since its approval);
     - a gap entry that no longer matches (its breach was fixed);
     - a relationship reported "not yet reached" that code now has (noted only).
     Each finding is presented with a recommendation and the owner decides: a stale `code` value is
     updated to describe what is; a drift breach becomes a gap entry with a reason (the target
     stands) or a target change in this run's diff; a stale gap entry is removed. Nothing is resynced
     silently.
   - **2b. How much to baseline?** The agent proposes the groups the run touches, from the epic's
     capabilities or the diff request, and the owner approves the list. Only when some of them are
     outside the current coverage (all of them, when the folder is empty) is there one question,
     with a recommendation from the run's impact and the codebase's size:
     - the whole repository, when there are at most `small-repo-modules` repository modules or at
       most `small-repo-groups` top-level groups;
     - the whole affected container, when the model already has containers and the run touches more
       than half of one container's groups, or a cross-cutting decision binds that container;
     - otherwise the touched groups plus edge nodes.
     The answer and the counts behind it are recorded in `architecture.md` under "Baseline
     coverage", then `baseline-run.md` is loaded and its instructions build that coverage. The
     baseline is its own diff: it goes through steps 3 to 6 with its own review and
     `[ARCH-APPROVED]`, logged with the reason `baseline`. The outer run then resumes at step 3,
     with `check` re-run against the approved baseline.
3. **Cross-cutting decisions in scope:** every decision the diff depends on, existing or new, each
   presented with options and a recommendation and approved separately.
4. **The diff:** elements with `code` and `rules`, tags (`#protected`, `#layer`, `#generic`,
   `#eval`), relationships and invariants expressed as relationships, shown before and after with
   the rule map. If the diff needs an edge node's inside, the run goes back to 2b for that area,
   whose baseline is approved on its own as above, and then returns to step 3.
5. **The known gap:** `check` against the amended model. Breaches the diff adds get a proposed
   reason; entries it closes are removed; entries naming an element the diff renames or removes are
   re-keyed or removed; the owner accepts or rejects each.
6. **Write, review, approve:** write the files; self-review against `ARCH_REVIEW_MANIFEST.md` and
   `ARCH_RUBRIC.md` (review log `--skill defining-architecture --phase ARCH_REVIEW`); a
   fresh-context audit (`INDEPENDENT_AUDIT`); the owner's `[ARCH-APPROVED]`; an append-only note on
   the triggering work item. The `--reason` of each entry starts `epic`, `later-stage: <stage>` or
   `baseline`. Self-review stops for the owner after 5 consecutive rejections, the audit after 3.

**Baseline run** (`baseline-run.md`, loaded only by step 2b). It describes what the code is, not
what it should be, for the coverage step 2b chose:
- when the folder is empty, it creates the folder and copies the shipped `c4.c4` into it unchanged;
- one `component` per top-level module group inside the coverage, with `code` set to the group's
  prefix and no `rules`; one edge node per neighbour group outside it that has a code edge to or
  from the coverage; containers and systems are added only by an epic's diff, never by a baseline;
- one relationship per element pair with a code edge between them, edge nodes included; edges from
  an edge node into unmodelled code point at no element, so the tool ignores them;
- where the groups' code edges form a cycle of any length, one relationship of each cycle is left
  out of the model and recorded in `known-gap.json` with the reason `cycle in current code`; the
  agent recommends the relationship with the fewest module edges and the owner chooses in step 5;
- "Baseline coverage" in `architecture.md` lists the baselined groups, the edge nodes, and the run
  that added each.

It goes through steps 3 to 6 like any diff, logged with the reason `baseline`. An epic's run then
amends the baseline into the target, so its diff and its new gap entries show what the epic forbids
that the code does today. A later run that extends coverage can turn up breaches an edge node hid;
they appear as new `check` breaches and go through step 5.

**Hard rules.**
- No new product rules: a rule gap goes back to the epic.
- Every Must rule has exactly one owning element.
- Every breach `check` reports is in `known-gap.json` with a reason; none is allowed silently and
  none is fixed by changing code.
- Inside the baselined coverage, every module `check` lists as unmapped is either mapped or listed
  in `architecture.md` with a reason; unmapped modules outside the coverage are expected.
- No mechanism detail (functions, schemas, field lists, algorithms); that belongs to the feature and
  the work item.
- The model loads with no errors and uses the shipped C4 spec unchanged.

**What review checks.** Scope "changed" covers the changed elements, their relationships and every
decision whose bound-elements list includes one of them; scope "whole" covers the whole model.
- Every Must rule has exactly one owner (whole).
- Every cross-cutting decision in scope is found, taken whole, and holds only product-level content
  (changed).
- No cycles (whole): from the `export` relationships, each relationship counts for its endpoints and
  all their ancestors; two siblings that reach each other, directly or through others, form a cycle.
- Every `code` value equals a module in the dependency file or a prefix of one (changed).
- A `check` run's output is quoted in this run's decision-log entry, and every breach is in the gap
  file (whole).
- Unmapped modules inside the coverage are mapped or listed with a reason (whole).
- No element's `code` is the shared prefix unless the whole repository is baselined, so no element
  matches modules outside its own groups (whole).
- Every edge node listed under "Baseline coverage" is a `component` with `code`, no children and no
  `rules`, and is in no decision's bound-elements list (whole).
- No mechanism detail and no new product rules (changed).
- The model loads with no errors (whole).

**`architecture.md`.** Kept in the model folder, with sections: Decision log (one dated entry per
run: the diff summary, the stage that asked, the alternatives rejected, the quoted `check` output),
Rule map (rule → owning element), Cross-cutting decisions (one section each), Baseline coverage,
Unmapped modules (module → reason). The decision log only grows; the other sections are edited in
place to stay current.

**Handoff.** An epic run hands off to `planning-features`, or straight to `specifying-features` for
an epic the owner agrees ships as one feature. A later-stage run hands back to the stage that asked;
a baseline run on its own ends there.

**Delta tool default.** `--model` defaults to `docs/architecture`, so the gap file defaults to
`docs/architecture/known-gap.json`. A model only in `architecture/` is no longer found without
`--model`. The engine's own spec copy, `skills/shared/architecture/c4.c4`, does not move.

## Scope

- `skills/shared/scripts/architecture-delta/args.mjs`: the `--model` default.
- Tests moved to the new default: `tests/scripts/arch_delta_support.py` (`make_repo`), the seven
  lines that write under `repo / "architecture"` in `test_architecture_delta_check.py`,
  `test_architecture_delta_export.py` and `test_architecture_delta_safety.py`, and the expected
  default in `test_architecture_delta_args.py` (`"model": "docs/architecture"`).
- `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md` and
  `docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md`: the default path.
- `skills/defining-architecture/`: `SKILL.md` (everything above except the baseline run, which it
  loads only from step 2b), `baseline-run.md`, `ARCH_STANDARDS.md` (the overlay table, spotting a
  cross-cutting decision, what counts as mechanism detail, gap reason format, the `architecture.md`
  layout), `ARCH_REVIEW_MANIFEST.md`, `ARCH_RUBRIC.md` (each review check as a binary item with its
  scope), `review-workflow.md`, `pressure-test-evidence.md`.
- `tests/fixtures/defining-architecture/`, a made-up shop repository in two copies:
  - `empty/`: an approved epic with three capabilities (checkout, refunds, reporting) that depend on
    one order-event format, and a Must rule that reporting reads payment totals only through the
    order events, never from payments directly; an `ARCHITECTURE_DESIGN.md` whose `deps-command`
    copies a committed dependency file into `deps-file`; code and dependencies with two entry paths
    (an API and a nightly job) that both write orders, a reporting module that reads payments
    directly, and an import cycle between the `orders` and `inventory` groups; no model.
  - `modelled/`: the same repository with an approved model in `docs/architecture/` (with
    `architecture.md` and `known-gap.json`) holding one cross-cutting decision, plus one renamed
    module that is the whole `code` value of one modelled element, one drifted import in the
    affected area, and a written later-stage diff request that
    changes only part of the decision.
- `tests/scripts/test_defining_architecture_contract.py`: the package files exist; the description
  starts "Use when", names no workflow and is at most 500 characters; `SKILL.md` names
  `[ARCH-APPROVED]` and loads `baseline-run.md` only from step 2b; every review-log skill and phase
  the package names is one the CLI accepts; `export --model docs/architecture` on `modelled/` exits 0
  with `architecture.md` and `known-gap.json` in the folder.
- RED and GREEN runs per `writing-skills`, recorded in `pressure-test-evidence.md`. They verify
  AC-3 to AC-8; the skill's behaviour is an agent's, so the evidence file, not pytest, is the test.
  Fresh subagents work on a copy of a fixture, once without the skill (RED) and once with it
  (GREEN). The orchestrator plays the owner from a fixed script kept in the evidence file: it
  approves each step as presented and adds the scenario's pressure lines.
  - Scenario A, `empty/`, epic run (AC-3 to AC-5, AC-8): pressures "we have a deadline", "just draw
    the boxes" and "I want to start coding today".
  - Scenario B, `modelled/`, later-stage run (AC-6, AC-7): pressures "it's a one-line change" and
    "skip the checks, the model was approved last week".
  Each loophole GREEN finds gets an explicit counter and a fresh rerun.

**Out of scope:** a `draft` command that writes the baseline `.c4` automatically; the other shards
named under Ownership.

## Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | The delta tool's `--model` default is set in one place | VERIFIED: `args.mjs:48` `model: opts['--model'] ?? 'architecture'` |
| A2 | The gap default is derived from the model folder | VERIFIED: `architecture-delta.mjs:72` `path.join(modelDir, 'known-gap.json')` |
| A3 | The helper, seven test lines and the args test's expected default assume `architecture` | VERIFIED: `grep -rn '"architecture"' tests/` |
| A4 | The review log accepts `defining-architecture`, `ARCH_REVIEW`, `INDEPENDENT_AUDIT` and free `--reason` text | VERIFIED: `review-log.py` `SKILLS`, `SELF_PHASES`, `REVIEWER_PHASES` (#21) |
| A5 | The C4 spec ships `system`, `container`, `component`, `external`, `uses` and the four tags | VERIFIED: `skills/shared/architecture/c4.c4` |
| A6 | Existing skill packages follow the SKILL / STANDARDS / MANIFEST / RUBRIC / review-workflow shape with contract tests | VERIFIED: `skills/specifying-epics/`, `tests/scripts/test_specifying_work_items_response_contract.py` |
| A7 | No `defining-architecture` skill or `ARCHITECTURE_DESIGN.md` exists yet | VERIFIED: `ls skills/`, `ls ARCH*` |
| A8 | `architecture.md` and `known-gap.json` are safe inside the model folder | VERIFIED: likec4 loads only `.c4`, `.likec4` and `.like-c4` files (`fileExtensions` in `node_modules/likec4/dist/chunks/node.mjs`); `walk.mjs` refuses only config names and links |
| A9 | Unmapped targets are ignored and unmapped sources are listed, not checked | VERIFIED: `match.mjs` `compare` (`target === null` returns; `source === null` adds to `unmapped`) |
| A10 | The tool reads `--deps` only inside `--repo` | VERIFIED: `resolveInside` in `paths.mjs`, called for `--deps` in `runCheck` |

## Threat Model (CIA)

- **Confidentiality.** The skill reads only the repository, the epic and the tool's output. The
  delta tool makes no network call (#20, `test_no_network_check_and_export`). The fixture is made up
  and holds no real data. The `deps-command` is the repository's own, named in its overlay.
- **Integrity.** The model changes only through the steps above, each approved, then self-review,
  an independent audit and the owner's `[ARCH-APPROVED]`; drift found in step 2a is never resynced
  without the owner. The skill writes files only inside the model folder, apart from the append-only
  waiver entry in the epic's decision log and the append-only work-item notes, and never edits code.
  The tool refuses model folders holding config files or links and checks the spec copy against the
  shipped one (#20, AC-4 and AC-24).
- **Availability.** The tool's file, element and edge limits and its `--timeout` bound every run
  (#20). The review circuit breakers bound the review loop; the coverage question bounds how much
  a baseline run models.
- **Least privilege and supply chain.** No new dependency, no secrets.

## Acceptance criteria

- **AC-1** Given a repository whose model is only in `architecture/`, when `export` runs without
  `--model`, then it exits 2 with `error: bad-input:`; given the model in `docs/architecture/`,
  then it exits 0.
- **AC-2** Given a repository whose gap file is `docs/architecture/known-gap.json`, when `check` runs
  without `--gap`, then that file's entries are applied.
- **AC-3** Given scenario A with the skill, when the agent starts, then its first output is the
  assumptions surface only, naming the epic run, its entry gate and the overlay's values.
- **AC-4** Given scenario A carried through, then the coverage question recommends the whole
  repository with the module and group counts, the baseline describes the current code, the
  `orders`–`inventory` cycle has one edge in `known-gap.json` with the reason
  `cycle in current code`, and the baseline is approved before the epic diff starts.
- **AC-5** Given the epic diff in scenario A, then the order-event format is one decision whose
  section binds all three capabilities and holds no field list, every Must rule has one owning
  element, the reporting-to-payments breach is in `known-gap.json` with a reason, and no code file
  is changed.
- **AC-6** Given scenario B with the skill, then step 2a reports the renamed module's stale `code`
  and the drifted import, each with a recommendation, and changes neither before the owner decides.
- **AC-7** Given scenario B carried through, then the partial change to the decision is refused
  unless the decision is changed whole, `check` is re-run, and review applies the "changed" checks
  to the changed elements, their relationships and the decision they bind, and the "whole" checks to
  the whole model.
- **AC-8** Given scenarios A and B without the skill (RED), then `pressure-test-evidence.md` records
  at least one failure per scenario verbatim, and the GREEN runs record the counters that closed
  them.

## Future work (downstream cost)

| Item | Priority | Effort | Why |
|---|---|---|---|
| `planning-features` fills `close_by` on gap entries (#23) | P1 | in #23 | This skill leaves it empty |
| `specifying-epics` hands off here; `specifying-work-items` reads the model (#25) | P1 | in #25 | The flow is not wired until then |
| A `draft` command that writes a baseline `.c4` from the dependency file | P3 | M | Hand drafting large repos is slow |
| A cycle check in the delta tool | P3 | S | The reviewer checks cycles by hand from `export` |
| Re-run the RED/GREEN scenarios when the skill changes | P2 | S | Skill edits need a failing test first |
