# Aligning existing skills with architecture and features

Work item: #25. Part of #19. Depends on #20, #22, #23 and #24, all merged.

## What changes and why

`defining-architecture`, `planning-features` and `specifying-features` exist, but nothing reaches
them: `specifying-epics` still breaks an epic into work items and hands each straight to
`specifying-work-items`, and no later stage reads the model or runs the delta tool. This work
edits the existing skills so the flow in the change plan is the flow an agent follows:

```
specifying-epics -> defining-architecture -> planning-features -> specifying-features
  -> specifying-work-items (per shard) -> writing-plans -> execution -> code review -> finishing
```

Each edit takes effect when its skill is next used. Every rule below that mentions the model or the
delta tool applies **only where the repository has a model** (a model folder holding a `.c4` file
other than `c4.c4`). Where it has none, the step is skipped without comment and the skill behaves
as it does today.

**Ownership.** This work edits skill text and one line of ownership. It adds no skill and no tool
behaviour. The step-file restructure of `specifying-epics` stays on #16.

## specifying-epics: capabilities, not work items

**Deliverable item 13 becomes "Capabilities".** The epic breaks down into capabilities, units of
meaning and not of delivery. Each capability has:
- a name;
- the business rules and acceptance criteria it owns, with every epic AC in exactly one capability;
- the value it brings: the success metric or MVP criterion it moves;
- its MoSCoW;
- its known product risks;
- its product dependencies on other capabilities.

A capability list holds no technical tasks, no delivery order and no sizing to one
`specifying-work-items` session. The epic may state a **product value order**; `planning-features`
treats it as the value input, not as the feature order.

**Handoff.** After `[EPIC-APPROVED]` and source-of-truth sync, the epic goes to
`defining-architecture`, then `planning-features`. Two short paths stay:
- an epic the owner agrees ships as one feature goes from `defining-architecture` (or its logged
  waiver) to `specifying-features`;
- work that is one work item with clear scope never needed an epic and goes to
  `specifying-work-items`, as today.

The epic no longer decomposes itself into work items and never hands a capability straight to
`specifying-work-items` or `writing-plans`.

**Where architecture belongs.** The epic stays product-only. Architecture decisions belong to
`defining-architecture` (across the epic) or `specifying-work-items` (inside one item).

**Every mention follows.** The Overview, When to Use, Quick Reference, Initial Gate, hard rule 7,
the hard gate, the Checklist, the Process Flow (its last two steps become the handoff above), the
Deliverable intro and must-not list, the sharding trigger (it fires when the capabilities exceed
what one team can own), Source-of-Truth Sync, the Review and Audit Gate, the Handoff section, the
red flags, common mistakes and rationalizations, `review-workflow.md`, and the manifest and rubric
checks all speak of capabilities and the handoff, not a work item breakdown. Red flags and
rationalizations about the breakdown are reworded for capabilities: the capability list is a
product decision, it is not a technical task list, and it is not a delivery plan.

**Review.** The manifest check and rubric section on the breakdown become checks on capabilities:
- each capability names its rules and ACs, its value, its MoSCoW, its risks and its dependencies;
- every epic AC is in exactly one capability;
- no capability is a technical task or a stage of delivery;
- each capability is understandable without reading the others.

**Older epics.** An approved epic that has a work item breakdown and no capabilities is not
rewritten. `defining-architecture` already reads such an epic through its MoSCoW scope.

## specifying-work-items: a shard reads the feature design and the model

**When the work item is a shard of a feature:**
- **Gate:** the feature design has `[FEATURE-APPROVED]`. With none, the run stops and goes to
  `specifying-features`.
- **Reads:** the shard's entry in the feature design's shard map (its `AC-F`s, its place in the
  order, any shard 0 decision that applies to it), the feature's answered questions, and the
  model: the elements the shard touches, their allowed relationships, and the cross-cutting
  decisions that bind them.
- **Assumptions surface** names those elements and says, for each new dependency the shard needs,
  whether the model allows it.
- **Does not re-decide** architecture, the shard's scope or an answered question. The spec stays
  inside the shard's `AC-F`s.
- **A needed model change** (a dependency the model does not allow, a changed decision) stops the
  spec. The run writes a diff request (what to change and why) and hands it to
  `defining-architecture`; the spec resumes after `[ARCH-APPROVED]`.
- **A needed change to the shard map or to another shard** goes to `specifying-features` as a
  reshard.

**When the work item is not a shard** but the repository has a model, the Assumptions surface
still names the elements it touches, and a dependency the model does not allow goes to
`defining-architecture` the same way.

**New red flag:** "add a dependency the model doesn't allow" (in any wording: "just import it",
"we'll update the diagram later").

**New rubric item**, mirrored in the manifest: every term that a rule, gate or acceptance criterion
depends on is defined once, in terms an agent can apply to the repository (a path, a prefix, a
count, a state), including its edge cases: empty, overlapping, and outside the scope.

The refactor-isolation rule and everything else in the skill are unchanged.

## writing-plans: model elements and planned dependencies

- **Header.** The plan's Architecture line names the model elements the plan touches, then the
  approach.
- **Planned dependencies.** After the caller and test sweep, the plan lists every new
  module-to-module dependency its tasks add: from, to, and the task that adds it; or `none`.
  Module names are written as the repository's dependency file writes them.
- **The delta check on the plan.** Pre-plan verification runs the overlay's `deps-command`, writes a
  copy of the dependency file with the planned dependencies added as edges (beside the dependency
  file, not committed), and runs `check` with `--deps` set to the copy. The output goes in the
  alignment check's evidence.
  - A breach that is not in the known gap rejects the plan. The plan is changed to respect the
    model, or the work stops and a diff request goes to `defining-architecture`. A plan never adds
    a known-gap entry and never edits the model.
  - Exit 2 stops with the tool's error.
  - A stale entry in this output is expected when the branch will fix a breach; it is noted and
    handled at finishing.
- **Self-review and alignment check** each gain one item: the planned dependencies list matches the
  tasks, and the `check` output shows no new breach.

## requesting-code-review and finishing-a-development-branch: the delta before merge

**requesting-code-review.** Before a review that precedes a merge, the requester runs
`deps-command` and `check` on the branch and gives the reviewer the output. A breach not in the
known gap is a Critical issue: it is fixed in code, or the merge waits for a diff request to
`defining-architecture`. It is never resolved by adding a gap entry in the branch.

**finishing-a-development-branch** gains an architecture check after the tests pass and before
the options are presented:
- `deps-command`, then `check` on the whole model.
- **A new breach blocks finishing.** The options are not presented until it is fixed in code or
  the model is amended through `defining-architecture`.
- **A stale gap entry is removed in this branch.** A stale entry means this branch fixed the
  breach. The entry is removed from `known-gap.json`, committed, and listed in the summary (and the
  PR body when one is made). `check` is re-run and must exit 0.
- Exit 2 blocks finishing with the tool's error.

**Ownership of stale entries** changes to match. The branch that fixes a breach removes its entry
at finishing. `specifying-features`' close run still runs `check` on the whole model and removes
any entry still stale, as a safety net, and its Close record lists the entries removed during the
feature, by shards and by the close. One sentence changes in each of
`skills/defining-architecture/SKILL.md` (Ownership), `skills/specifying-features/SKILL.md`
(Ownership) and `skills/specifying-features/close-run.md`. A stale entry found in scope by a
feature design run still stops that run and goes to `defining-architecture`, since it means a
branch finished without the check.

## using-resistance-engine and README

- `using-resistance-engine` gains a short section giving the flow above, the two short paths, and
  which skill to start from: epic-sized or unclear scope starts at `specifying-epics`; one clear
  work item starts at `specifying-work-items`. It stays short, since it loads in every
  conversation.
- The README gains a "Workflow" section with the flow, one line per stage and its approval tag,
  and a note that the delta tool needs Node.

## Baseline

As for #23 and #24, the baseline is the real-world record, not synthetic runs (owner decision,
2026-11-10).

| # | What happened | Source | Answered by |
|---|---|---|---|
| B1 | Architecture was decided one work item at a time, and layering knowable at the epic's start showed up late as unplanned refactors | Change plan "Why" | the `specifying-epics` handoff; a shard reading the model |
| B2 | Work items sized to one spec session each restated a rule on separate entry paths | Change plan "Why"; field report 2026-10-25 §7 | capabilities, with no sizing to a spec session |
| B3 | Callers and dependencies outside the searched directories were found only at plan review | Retrospective 2026-10-27 F4 | planned dependencies checked against the model before execution |
| B4 | An independent audit found 15 spec holes after self-review had passed twice; most were a term the rules depended on that was never pinned down, or was pinned down without its edge cases | #25 comment (checklist retrospective of #22's spec) | the new rubric item |
| B5 | The audit of the #23 and #24 spec found another such term ("the feature's elements") | Review log, item 23-24, audit round 1 | the new rubric item |

The delta checks in code review and finishing, and the stale-entry rule, come from the change plan
and the owner's decision of 2026-11-11, with no recorded failure behind them yet.

## Scope

- `skills/specifying-epics/`: `SKILL.md`, `EPIC_REVIEW_MANIFEST.md`, `EPIC_RUBRIC.md`,
  `review-workflow.md`. `EPIC_STANDARDS.md` changes only where it names the handoff.
- `skills/specifying-work-items/`: `SKILL.md` (a "Shard of a feature" section, the pointer in When
  to Use, the red flag), `SPEC_RUBRIC.md` and `SPEC_REVIEW_MANIFEST.md` (the terms item).
- `skills/writing-plans/`: `SKILL.md` (header, Planned dependencies, pre-plan verification,
  self-review and alignment-check items), `plan-document-reviewer-prompt.md`,
  `alignment-check-evidence.md`.
- `skills/requesting-code-review/`: `SKILL.md`, `code-reviewer.md` (a place for the `check`
  output).
- `skills/finishing-a-development-branch/SKILL.md`.
- `skills/defining-architecture/SKILL.md`, `skills/specifying-features/SKILL.md` and
  `skills/specifying-features/close-run.md`: the stale-entry ownership sentences.
  `skills/specifying-features/SKILL.md` stays within its 1,000-word cap.
- `skills/using-resistance-engine/SKILL.md` and `README.md`.
- No new test. The existing suite must pass unchanged; two existing contract tests assert exact
  phrases of `specifying-work-items` and `writing-plans`, and no edit removes or rewords a phrase
  they assert.

**Out of scope:** the step-file restructure of `specifying-epics` (#16); rewriting older epics; a
tool option that takes planned edges directly; evidence files for the edited skills; subagent
pressure runs.

## Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | `check` takes any dependency file inside the repository through `--deps` | VERIFIED: delta tool spec, "Inputs"; `paths.mjs` `resolveInside` |
| A2 | The dependency file's shape is `{"edges": [[from, to], ...]}`, so planned edges can be appended to a copy | VERIFIED: `inputs.mjs` `parseDeps` |
| A3 | `check` exits 1 for a new breach or a stale entry and reports each under its own heading | VERIFIED: `report.mjs` `checkText` |
| A4 | The overlay keys and the meaning of an empty model folder are defined by `defining-architecture` | VERIFIED: `skills/defining-architecture/ARCH_STANDARDS.md`; #22 spec |
| A5 | `specifying-epics` names the work item breakdown in its `SKILL.md`, manifest, rubric and review workflow | VERIFIED: `grep -n -i "work item\|breakdown\|decompos" skills/specifying-epics/*.md` |
| A6 | `defining-architecture` reads an older epic through its MoSCoW scope | VERIFIED: `ARCH_STANDARDS.md`, "Must rule" |
| A7 | Existing contract tests assert phrases only in `specifying-work-items` and `writing-plans`, plus one line of `finishing-a-development-branch` about the run record | VERIFIED: `tests/scripts/test_specifying_work_items_response_contract.py`, `test_writing_plans_contract.py`, `test_run_record_contract.py` |
| A8 | `using-resistance-engine` and the README have no flow or skill list today | VERIFIED: read of both files |
| A9 | The word cap on the two feature skills is enforced by a test | VERIFIED: `tests/scripts/test_feature_skills_contract.py` |

## Threat Model (CIA)

- **Confidentiality.** The new steps read the repository, the model and the delta tool's output.
  The tool makes no network call (#20, `test_no_network_check_and_export`). The `deps-command` is
  the repository's own, named in its overlay.
- **Integrity.** No later stage may make a breach legal: a plan, a review and a finishing branch
  can only fix code or hand a diff request to `defining-architecture`, whose changes need a review
  and `[ARCH-APPROVED]`. The only write to the model folder outside that skill is removing an entry
  the tool itself reports stale, so the gap can shrink and never grow. The planned-dependency copy
  is written beside the dependency file, inside the repository and uncommitted, and the tool
  refuses a `--deps` path outside the repository (#20). Tool output is quoted as data.
- **Availability.** The tool's limits and `--timeout` bound every run (#20). Every new step is
  skipped where there is no model, so a repository without one is not slowed or blocked.
- **Least privilege and supply chain.** No new dependency, no secrets, no network use.

## Acceptance criteria

- **AC-1** Given the repository after this work, when `uv run pytest` runs, then the whole suite
  passes with no test changed.
- **AC-2** Given the `specifying-epics` package, when it is read, then deliverable item 13 is
  Capabilities with the six parts above, the handoff goes to `defining-architecture`, and no file
  in the package tells the agent to break the epic into work items or hand a capability to
  `specifying-work-items` or `writing-plans`.
- **AC-3** Given each other edited skill, when it is read against its section of this spec, then
  every rule in that section is present, each model or delta rule says it applies only where the
  repository has a model, and nothing contradicts `defining-architecture`, `planning-features` or
  `specifying-features`.
- **AC-4** Given the three stale-entry sentences, when they are read together with
  `finishing-a-development-branch`, then they agree on who removes a stale entry and when.

AC-2 to AC-4 are about agent-facing text, so no automated test can verify them. They are checked
by the final code review reading the files.

## Future work (downstream cost)

| Item | Priority | Effort | Why |
|---|---|---|---|
| Version bump and release (#26) | P1 | S | The flow ships with it |
| First real epic through the whole flow, with field-log entries | P1 | M | It is the first behaviour test of every edit here |
| A `check` option that takes planned edges, replacing the hand-made copy | P3 | S | The copy is a manual step |
| Step-file restructure of `specifying-epics` (#16) | P2 | M | Deferred by the change plan |
