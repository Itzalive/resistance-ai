# defining-architecture skill

Work item: #22. Part of #19. Depends on #20 (delta tool) and #21 (review-log phases), both merged.

## What changes and why

In a multi-feature epic, architecture decided one work item at a time shows up late as unplanned
refactors: several items restating one rule on separate entry paths, or a feature opening with a
"shard 0" of behaviour-free splits. The layering that prevents most of this is knowable when the
epic starts. This work item adds the skill that decides it: `skills/defining-architecture/`, which
keeps a target C4 model (LikeC4 `.c4` files) of the repository and amends it. It also moves the
delta tool's default model folder to `docs/architecture/`.

**Trigger.** A run starts in one of three ways:
- an epic reaches `[EPIC-APPROVED]` and architecture is next;
- a later stage (`planning-features`, `specifying-features` or `specifying-work-items`) needs the
  approved model changed;
- a repository with no model is onboarded (the baseline run).

**Ownership.** This skill owns the model folder's content: the `.c4` files, `architecture.md` and
`known-gap.json`. It owns no code and changes none. Filling `close_by` on gap entries belongs to
`planning-features` (#23); the edits that hand off to this skill from `specifying-epics` and that
make `specifying-work-items` read the model belong to #25; the skill index and README to #25.

## Rules

**Every run is an amendment.** The current model is whatever is in the model folder. A run proposes
a diff to it: elements, relationships, tags, metadata and cross-cutting decisions added, changed or
removed, each with a reason and the stage that asked. Only the size differs: an epic run is a large
diff, a later-stage run a small one, and the first run in a repository amends an empty model.

**When it is required.** For an epic with more than one feature, or with two or more entry paths
expected into the same module. Otherwise the owner may waive it; the waiver is written in the epic's
decision log and appended as a note to the epic's work item, and the skill stops. No review-log
entry is written for a waiver.

**Overlay.** Repo-root `ARCHITECTURE_DESIGN.md` is optional and names:
- the model folder (default `docs/architecture/`);
- the command that writes the dependency file (`{"edges": [[from, to], ...]}`);
- the module-name separator (default `.`).

It may tighten this skill's rules, never weaken them. When no dependency command is named, the run
stops and asks for one; it never guesses.

**Baseline run.** When the model folder has no `.c4` file other than the shipped spec copy, the run
first builds a baseline. Its instructions live in `baseline-run.md`, which `SKILL.md` loads only in
that case. The baseline describes what the code is, not what it should be:
- one element per top-level module group, with `code` set to its module prefix, and no `rules`;
- one relationship per element pair that has a code edge;
- where code has a dependency cycle, one edge of each cycle is left out of the model and recorded in
  `known-gap.json` with the reason `cycle in current code`, so the no-cycles check is the same for
  every run.

It goes through the same steps, review and approval as any run, logged with the reason `baseline`.
An epic's run then amends the baseline into the target, so its diff and its new gap entries show
what the epic forbids that the code does today.

**Steps.** One at a time, each approved by the owner before the next. Each step covers only what
the diff touches.
1. **Assumptions surface:** required or waived; overlay present; triggering artifact approved;
   dependency command named. Anything missing stops the run.
2. **Current state:** `export` the current model (or note it is empty), run the dependency command
   and `check`, and summarise elements, open gap entries and breaches (on a baseline run, modules and
   dependencies).
3. **Cross-cutting decisions in scope:** every decision the diff depends on. A decision two or more
   capabilities depend on (a data or storage format, a shared contract or API, an id or naming
   scheme, a vocabulary of kinds or types) is taken whole: designed once, for every capability that
   needs it including those built in later features, with the elements it binds listed. An existing
   decision is used as is or changed whole as part of this diff, never in part.
4. **The diff:** elements with `code` and `rules`, tags (`#protected`, `#layer`, `#generic`,
   `#eval`), relationships and invariants expressed as relationships, shown before and after with
   the rule map.
5. **The known gap:** `check` against the amended model. Breaches the diff adds get a proposed
   reason; entries it closes are removed; the owner accepts or rejects each.
6. **Write, review, approve:** write the files; self-review against `ARCH_REVIEW_MANIFEST.md` and
   `ARCH_RUBRIC.md` (review log `--skill defining-architecture --phase ARCH_REVIEW`); a
   fresh-context audit (`INDEPENDENT_AUDIT`); the owner's `[ARCH-APPROVED]`; an append-only note on
   the triggering work item. Self-review stops for the owner after 5 consecutive rejections, the
   audit after 3.

**Hard rules.**
- No new product rules: a rule gap goes back to the epic.
- Every Must business rule has exactly one owning element.
- Every breach `check` reports is in `known-gap.json` with a reason; none is allowed silently and
  none is fixed by changing code.
- No mechanism detail (functions, schemas, field lists, algorithms): that belongs to the feature and
  the work item.
- The model loads with no errors and uses the shipped C4 spec unchanged.

**What review checks.** Scope "changed" covers the changed elements, their relationships and every
decision they bind; scope "whole" covers the whole model.
- Every Must rule has exactly one owner (whole).
- Every cross-cutting decision in scope is found and taken whole (changed).
- The relationships have no cycles (whole).
- Every `code` value names a module in the dependency file, or the element is marked not yet built
  (changed).
- A `check` run is attached and every breach is in the gap file (whole).
- No mechanism detail and no new product rules (changed).
- The model loads with no errors (whole).

**`architecture.md`.** Kept in the model folder. Each run appends a dated decision-log entry (the
diff summary, the stage that asked, the alternatives rejected). The rule map (rule → owning element)
and one section per cross-cutting decision are edited in place to stay current.

**Handoff.** An epic run hands off to `planning-features`, or straight to `specifying-features` for
an epic the owner agrees ships as one feature. A later-stage run hands back to the stage that asked;
a baseline run on its own ends there.

**Delta tool default.** `--model` defaults to `docs/architecture`, so the gap file defaults to
`docs/architecture/known-gap.json`. A model only in `architecture/` is no longer found without
`--model`. The engine's own spec copy, `skills/shared/architecture/c4.c4`, does not move.

## Scope

- `skills/shared/scripts/architecture-delta/args.mjs`: the `--model` default.
- `tests/scripts/arch_delta_support.py` (`make_repo`) and the delta tests that write under
  `repo / "architecture"`: moved to `docs/architecture`.
- `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md` and
  `docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md`: the default path.
- `skills/defining-architecture/`: `SKILL.md`, `baseline-run.md`, `ARCH_STANDARDS.md` (overlay
  keys, spotting a cross-cutting decision, what counts as mechanism detail, gap reason format,
  `architecture.md` layout), `ARCH_REVIEW_MANIFEST.md`, `ARCH_RUBRIC.md` (each check as a binary
  item with its scope), `review-workflow.md`, `pressure-test-evidence.md`.
- `tests/fixtures/defining-architecture/`: a made-up shop repository — an approved epic with three
  capabilities (checkout, refunds, reporting) depending on one order-event format, two entry paths
  (an API and a nightly job) that both write orders, a reporting module that reads payments
  directly, one import cycle, a dependency file, and a second copy with an approved model holding
  one cross-cutting decision plus a later-stage request that changes only part of it.
- `tests/scripts/test_defining_architecture_contract.py`: the package files exist; the description
  starts "Use when", names no workflow and is at most 500 characters; `SKILL.md` names
  `[ARCH-APPROVED]` and loads `baseline-run.md` only when the model folder is empty; every
  review-log skill and phase the package names is one the CLI accepts; the fixture models load
  through `export` with exit 0.
- RED and GREEN runs per `writing-skills` (they verify AC-3 to AC-7; the skill's behaviour is an agent's, so the evidence file, not pytest, is the test), recorded in `pressure-test-evidence.md`: fresh subagents
  on a copy of the fixture, without the skill and then with it, under time pressure, "just draw the
  boxes" and an owner keen to start coding. Each loophole GREEN finds gets an explicit counter and a
  fresh rerun.

**Out of scope:** a `draft` command that writes the baseline `.c4` automatically; the other shards
named under Ownership.

## Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | The delta tool's `--model` default is set in one place | VERIFIED: `args.mjs:48` `model: opts['--model'] ?? 'architecture'` |
| A2 | The gap default is derived from the model folder | VERIFIED: `architecture-delta.mjs` `readOptional(..., path.join(modelDir, 'known-gap.json'), ...)` |
| A3 | Test helpers and seven delta tests write models under `repo / "architecture"` | VERIFIED: `grep -rn '"architecture"' tests/` |
| A4 | The review log accepts `defining-architecture`, `ARCH_REVIEW` and `INDEPENDENT_AUDIT` | VERIFIED: `review-log.py` `SKILLS`, `SELF_PHASES`, `REVIEWER_PHASES` (#21) |
| A5 | The C4 spec ships `system`, `container`, `component`, `external`, `uses` and the four tags | VERIFIED: `skills/shared/architecture/c4.c4` |
| A6 | Existing skill packages follow the SKILL / STANDARDS / MANIFEST / RUBRIC / review-workflow shape with contract tests | VERIFIED: `skills/specifying-epics/`, `tests/scripts/test_specifying_work_items_response_contract.py` |
| A7 | No `defining-architecture` skill or `ARCHITECTURE_DESIGN.md` exists yet | VERIFIED: `ls skills/`, `ls ARCH*` |

## Threat Model (CIA)

- **Confidentiality.** The skill reads only the repository, the epic and the tool's output. The
  delta tool makes no network call (#20, `test_no_network_check_and_export`). The fixture is made up
  and holds no real data.
- **Integrity.** The model changes only through the steps above, each approved, then self-review,
  an independent audit and the owner's `[ARCH-APPROVED]`. The skill writes only inside the model
  folder and never edits code. The tool refuses model folders holding config files or links and
  checks the spec copy against the shipped one (#20, AC-4 and AC-24).
- **Availability.** The tool's file, element and edge limits and its `--timeout` bound every run
  (#20). The review circuit breakers bound the review loop.
- **Least privilege and supply chain.** No new dependency, no secrets; the dependency command is the
  repository's own, named by its overlay.

## Acceptance criteria

- **AC-1** Given a repository whose model is only in `architecture/`, when `export` runs without
  `--model`, then it exits 2 with `error: bad-input:`; given the model in `docs/architecture/`,
  then it exits 0.
- **AC-2** Given a repository whose gap file is `docs/architecture/known-gap.json`, when `check` runs
  without `--gap`, then that file's entries are applied.
- **AC-3** Given the shop fixture with no model and the skill, when a fresh agent runs it for the
  epic, then its first output is the assumptions surface only.
- **AC-4** Given the same run carried through, then a baseline model is built that describes the
  current code, one edge of the import cycle is in `known-gap.json` with the reason
  `cycle in current code`, and the baseline is approved before the epic diff starts.
- **AC-5** Given the epic diff in that run, then the order-event format is one decision binding all
  three capabilities, every Must rule has one owning element, the reporting-to-payments breach is in
  `known-gap.json` with a reason, and no code file is changed.
- **AC-6** Given the fixture with an approved model and a later-stage request that changes part of
  its cross-cutting decision, when a fresh agent runs the skill, then it refuses the partial change
  unless the decision is changed whole, re-runs `check`, and scopes review to the changed elements.
- **AC-7** Given the same scenarios without the skill (RED), then `pressure-test-evidence.md` records
  at least one failure per scenario verbatim, and the GREEN runs record the counters that closed
  them.

## Future work (downstream cost)

| Item | Priority | Effort | Why |
|---|---|---|---|
| `planning-features` fills `close_by` on gap entries (#23) | P1 | in #23 | This skill leaves it empty |
| `specifying-epics` hands off here; `specifying-work-items` reads the model (#25) | P1 | in #25 | The flow is not wired until then |
| A `draft` command that writes a baseline `.c4` from the dependency file | P3 | M | Hand drafting large repos is slow |
| Re-run the RED/GREEN scenarios when the skill changes | P2 | S | Skill edits need a failing test first |
