# planning-features and specifying-features skills

Work items: #23 and #24. Part of #19. Depends on #20 (delta tool), #21 (review-log phases) and #22
(`defining-architecture`), all merged.

## What changes and why

Today nothing turns an approved epic into stages of value, and nothing designs one stage before its
work items are specified. On a real multi-item release this showed up as work items reshared again
and again, a consolidation item inserted late, refactors found only when a stage opened, and
behaviour questions settled in chat one item at a time (see Baseline).

This work adds two skills:

- `skills/planning-features/` forms and orders an epic's features and writes the **feature map**.
- `skills/specifying-features/` designs one feature from the map and writes the **feature design**.

They are specified together because the feature map is written by the first and read by the second.
They are built one after the other: `planning-features` is finished and committed before
`specifying-features` is started.

**Ownership.**

| Skill | Owns | Never changes |
|---|---|---|
| `planning-features` | The feature map; `close_by` on known-gap entries | The epic, the model (apart from `close_by`), code, any feature design |
| `specifying-features` | The feature design; its own feature's state, actual cost and question answers on the map; removing stale known-gap entries at close | The epic, the model (apart from stale entries), code, other features' rows, any shard spec |

The edits that wire these skills into `specifying-epics`, `specifying-work-items`, the skill index
and the README belong to #25.

## The feature map

One file per epic, `docs/features/<epic>/feature-map.md` by default; the owner may name another
folder at the first step. Feature designs sit beside it.

| Part | Holds |
|---|---|
| Header | The epic, the date of the model decision-log entry it was planned against, the approval tag |
| Features, in order | Id (`F1`…), goal, the success metric or MVP criterion it moves, the epic ACs it delivers, the cross-cutting decisions it builds on (marked "foundation" for the first feature to build on each), rough cost and what it was fitted from, the eval run that proves it, the known-gap entries it closes, entry-path and implementations-per-rule counts, state (planned, specified, shipped) and actual cost |
| Questions | Id, the question, the feature that answers it, its risk (what changes at each possible answer), split out or not, and the answer once given. A split-out question also names its kind (spike, measurement or prototype), what it runs before or alongside, the decision its answer feeds and the features it could change |
| AC coverage | Every epic AC against exactly one feature, or marked cross-cutting (checked in every feature) |
| Order reasoning | One short paragraph per ordering rule |
| Re-plan log | Append-only, one dated entry per re-plan |

## planning-features

**Triggers and entry gates.**

| Trigger | Entry gate |
|---|---|
| An epic's architecture is approved (planning run) | The epic has `[EPIC-APPROVED]`, the model has `[ARCH-APPROVED]`, and `check` on the whole model exits 0 |
| A feature shipped, a split-out question was answered, or `specifying-features` sent back an answer that changes another feature (re-plan run) | The map has `[FEATURES-APPROVED]` |

A `check` that does not exit 0 sends the run to `defining-architecture`; this skill never repairs the
model. An epic the owner agrees ships as one feature skips this skill: the agreement is appended as
a note to the epic's work item and the epic goes to `specifying-features`, which then takes the
epic as its feature.

**Ordering rules**, in priority order:

1. **Decisions first.** Cross-cutting decisions are already taken whole by `defining-architecture`.
   The first feature that builds on one lays its foundation, so later features add to it and do
   not reshape it.
2. **Direction-changing questions early, split by risk.** A question whose answer could change the
   plan (an unproven technique, a cost or quality unknown, a dependency on another party) is placed
   with the feature that needs its answer.
   - It is **split out** as its own item only when a wrong answer would waste or redo work in other
     features, or change the epic's direction (its capabilities, its value order or a cross-cutting
     decision). A split-out question is answered before every feature it could invalidate. Where it
     shares no files with the current feature and neither needs the other's result, it runs
     alongside that feature.
   - Otherwise it stays with its feature and is answered by `specifying-features` before that
     feature's shard specs.
3. **Value to cost.** Among what is left: MVP criteria first, then Musts by value per cost, then
   Shoulds and Coulds.
4. **Every feature stands alone.** It ships, it is measured by its own eval run, and it leaves the
   product better if the next feature never comes. A feature that delivers no epic AC is not a
   feature.
5. **Not by commonality.** Sharing code is never the reason two capabilities share a feature.
   Shared code is handled by cross-cutting decisions and each feature's architecture delta.

**Steps of a planning run**, one at a time, each approved by the owner before the next. Each step
presents the decisions the owner must make first and lists everything else as defaults applied
unless the owner objects.

1. **Assumptions surface:** the trigger and its gate with the `check` result; the epic's
   capabilities, ACs, success metrics and MVP criteria; the cross-cutting decisions and known-gap
   entries; whether run records exist. Anything missing stops the run.
2. **Questions:** every direction-changing question, its risk, and whether it is split out, with
   the reason against the test in rule 2.
3. **Signals:** per capability, a first count of the entry paths it touches and of the places each
   of its rules is implemented today, from the model's rule map, the dependency file and a reading
   of the code. Three or more implementations of one rule is flagged as likely consolidation.
4. **Features formed and ordered:** the proposed features and order, with the reasoning per rule
   and a rough cost per feature. The cost is fitted from the project's run records and names the
   records used; with no records it is marked as a guess. A cost is reported, never used as a
   target or a cap. The owner decides the order.
5. **Write:** the map; `close_by` on each known-gap entry (the feature that closes it, or
   `not planned: <reason>`); one work item per feature and per split-out question.
6. **Review and approve:** self-review (review log `--skill planning-features --phase
   FEATURES_PLAN_REVIEW`), a fresh-context audit (`INDEPENDENT_AUDIT`), the owner's
   `[FEATURES-APPROVED]`, and an append-only note on the epic's work item. Self-review stops for
   the owner after 5 consecutive rejections, the audit after 3.

**Re-plan run.** It records the result and the actual cost on the map, re-checks the order of the
features not yet shipped against the same rules, and adds a re-plan log entry. If the order or any
feature's content changes, the change goes through step 6 with review scoped to the changed
features. If nothing changes, the owner confirms the log entry and no review runs. Shipped features
are never reordered or rewritten.

**Hard rules.**
- The order is the owner's call; the skill proposes and gives its reasoning.
- A change to the epic's capabilities or ACs is an epic amendment, and a change to the model goes
  through `defining-architecture`. Neither is made here; the run stops and hands over.
- Every epic AC is in exactly one feature or marked cross-cutting.
- No code is written or changed.

**What review checks.**
- Every epic AC is in exactly one feature or marked cross-cutting.
- Every feature has a goal, the metric or criterion it moves, at least one epic AC, an eval run,
  and a cost that names its records or is marked a guess.
- No feature's stated reason is shared code.
- Every question has its risk and its placement. Every split-out question names its kind, the
  decision it feeds and the features it could change, and is placed before each of them.
- The first feature to build on each cross-cutting decision is marked as its foundation.
- Every known-gap entry has `close_by`.
- The signals are present for every capability.
- Order reasoning is given per rule.
- The epic, the model (apart from `close_by`) and the code are unchanged.

**Handoff.** To `specifying-features` for the first feature in the order, and to the owner for any
split-out question that runs first or alongside.

## specifying-features

**Triggers and entry gates.**

| Trigger | Entry gate |
|---|---|
| A feature starts (design run) | The map has `[FEATURES-APPROVED]`; the feature is the next in its order, or the owner names it; every split-out question that could change it is answered |
| The feature's last shard has merged (close run) | The feature design has `[FEATURE-APPROVED]` |
| The owner or a shard asks for the shard map to change (reshard) | The feature design has `[FEATURE-APPROVED]` |

For a one-feature epic that skipped `planning-features`, the gate is `[EPIC-APPROVED]` and
`[ARCH-APPROVED]` (or its logged waiver), and the feature's ACs and questions come from the epic.

**The feature design** is one file, `docs/features/<epic>/<id>-<slug>.md`, with sections: Questions
answered, Behaviour, Feature ACs, Architecture delta, Shard map, Eval plan, Costing, Decision log,
Close record.

**Steps of a design run**, one at a time, each approved before the next, with decisions and
defaults presented as in `planning-features`.

1. **Assumptions surface:** the trigger and its gate; the feature's row from the map (ACs,
   questions, decisions, gap entries); the overlay's `deps-command`; whether run records exist.
   Anything missing stops the run.
2. **Questions answered:** each open question the map gives this feature, with its evidence (a
   measurement, a reading of the code, or a short spike inside this feature), plus any behaviour
   question the epic and the code as built leave open for this feature. An answer that would
   change another feature or the epic stops the run and goes to a `planning-features` re-plan; the
   design resumes after it.
3. **Behaviour and feature ACs:** behaviour by section, and ACs numbered `AC-F…`, each tracing to
   the epic ACs it serves. Every epic AC the map gives this feature is served by at least one.
   Where the feature lays the foundation of a cross-cutting decision, its field lists and formats
   are designed here, inside the obligations the decision sets.
4. **Architecture delta and shard map.**
   - The proposed shards and the model elements each touches are written to a shards file.
   - `deps-command` runs, then `check --scope <the feature's elements> --shards <file>`. The output
     is quoted in the design.
   - For each `#eval` element in scope, the skill reads whether it uses the production element or
     holds its own copy, and says that this is a reading, not tool output.
   - Every breach in scope, every shared hot spot and every eval copy becomes a shard 0 refactor,
     or is recorded as left alone with the reason. A refactor is cut to what this feature's shards
     change; a tidy-up that only makes code easier to read is left alone.
   - The shard map gives each shard its feature ACs (every `AC-F` in exactly one shard), the order
     and why. Refactor shards change no behaviour; behaviour shards carry no refactor.
5. **Eval plan and costing.**
   - The probes each feature AC needs, and the one eval run that proves the feature.
   - Entry paths per shard and implementations per rule. When three or more implementations of one
     rule would each be changed, a consolidation shard comes first.
   - A cost estimate fitted from `.run_records.jsonl`, naming the records used, or marked as a
     guess when there are none. It is reported, never used as a target or a cap.
6. **Write, review, approve:** self-review (`--skill specifying-features --phase FEATURE_REVIEW`),
   a fresh-context audit (`INDEPENDENT_AUDIT`), the owner's `[FEATURE-APPROVED]`, the map row set
   to "specified", and an append-only note on the feature's work item. Self-review stops for the
   owner after 5 consecutive rejections, the audit after 3.

**Reshard.** A change to an approved shard map goes through step 6 with review scoped to the
changed shards. The second reshard request in one feature re-runs the costing in step 5 before the
shard map changes.

**Close run.** It re-runs `deps-command` and `check` on the whole model, removes the known-gap
entries the tool reports stale, writes the Close record (the gap entries closed and the actual cost
from the run records), sets the map row to "shipped", and hands to a `planning-features` re-plan.
A gap entry the map says this feature closes but the tool still reports is recorded as not closed.
A new breach is not added to the gap here; it goes to `defining-architecture`. The owner confirms
the Close record; no review runs.

**Hard rules.**
- No shard spec before `[FEATURE-APPROVED]`.
- The Architecture delta section is never empty without the tool's output showing the scope clean.
- A change to the model goes through `defining-architecture`, and a change to another feature or to
  the epic goes through `planning-features`. Neither is made here; the run stops and hands over.
- A shard never mixes a refactor with a behaviour change.
- No code is written or changed.

**What review checks.**
- Every question the map gives the feature is answered with evidence.
- Every epic AC the map gives the feature is served by an `AC-F`, and every `AC-F` traces to one.
- The `check` output is quoted and was run with the feature's scope and the shards file.
- Every breach in scope, hot spot and eval copy is a shard 0 refactor or left alone with a reason.
- Every `AC-F` is in exactly one shard, and no shard mixes a refactor with behaviour.
- Consolidation comes first where three or more implementations of one rule change.
- Every `AC-F` has a probe, and one eval run is named.
- The cost names its records or is marked a guess.
- No shard spec exists, and the epic, the model, the code and other features' rows are unchanged.

**Handoff.** A design run hands to `specifying-work-items` for the first shard. A close run hands
to `planning-features`.

## Baseline

These skills are written from what happened on a real multi-item release without them, not from
synthetic scenarios (owner decision, 2026-11-10). Each skill's evidence file records the failures
it answers, in generic terms, with their source.

| # | What happened | Source | Answered by |
|---|---|---|---|
| B1 | Several items each restated one rule on separate entry paths; a consolidation item was inserted late | Field report 2026-10-25 §7, lesson 14; change plan "Why" | planning step 3; design step 5 |
| B2 | Entry paths, not size, drove the cost, and this was found only by a spike in the middle of the release | Field report 2026-10-25 §7, lesson 16 | planning steps 3 and 4; design step 5 |
| B3 | Parts of a proposed consolidation did not pay back within the release | Field report 2026-10-25 §7, lesson 15 | design step 4, "cut to what this feature's shards change" |
| B4 | A feature opened with unplanned behaviour-free refactors | Change plan "Why" | design step 4, shard 0 decided before any shard spec |
| B5 | An eval used its own copy of a builder instead of production's | Change plan "Why" | design step 4, eval copies |
| B6 | Work was reshared repeatedly with no re-costing | Field report 2026-10-25 §7, lesson 17 | Reshard |
| B7 | Behaviour questions surfaced item by item, were settled in chat, and one invalidated a plan already written | Field report 2026-10-25, lessons 26 and 27 | planning step 2; design step 2 |
| B8 | A long list of questions was heavy for the owner to decide at once | Field report 2026-10-25, lesson 27; retrospective 2026-10-27, F9 | decisions first, defaults listed, in every step |
| B9 | A size number given to a writer became a target | Field report 2026-10-25, lessons 18 and 23 | cost reported, never a target |
| B10 | A decision's consequence was stated wrongly because it was not checked against the real thresholds | Field report 2026-10-25, lesson 25 | a question's risk states what changes at each answer |

Ordering rules 1, 4 and 5 and the approval tags come from the approved change plan, not from a
recorded failure; each evidence file says so.

**Tuning.** Each evidence file ends with a field log, empty at first. A real use that goes wrong
adds a dated entry: what the agent did, in its own words where possible, and the wording changed in
response. Red flags and rationalization tables start with only what the baseline supports and grow
from the field log. The skills are changed from a field-log entry or a filed issue, never from a
guess.

## Scope

- `skills/planning-features/`: `SKILL.md` (gates, ordering rules, steps, hard rules, handoff),
  `replan-run.md` (loaded only by a re-plan run), `FEATURES_STANDARDS.md` (the map's format, the
  split-out test, the signals, cost fitting), `FEATURES_REVIEW_MANIFEST.md`, `FEATURES_RUBRIC.md`
  (each review check as a binary item), `review-workflow.md`, `field-evidence.md`.
- `skills/specifying-features/`: `SKILL.md` (gates, steps, reshard, hard rules, handoff),
  `close-run.md` (loaded only by a close run), `FEATURE_STANDARDS.md` (the design's format, the
  delta and its dispositions, shard-map rules, cost fitting), `FEATURE_REVIEW_MANIFEST.md`,
  `FEATURE_RUBRIC.md`, `review-workflow.md`, `field-evidence.md`.
- Each `SKILL.md` is at most 1,000 words. Its description says only when to use the skill.
- `tests/scripts/test_feature_skills_contract.py`, one file for both packages, checking structure
  and machine interfaces only: the package files exist; the frontmatter name matches the folder;
  the description starts "Use when" and is at most 500 characters; every review-log skill and
  phase a package names is one the CLI accepts; each `SKILL.md` has at most 1,000 words. No test
  asserts a phrase, sentence or heading of
  the skill text.
- A note appended to #23 and #24: their "RED baseline first" is met by the Baseline above.

**Out of scope:** subagent pressure runs and fixtures for these skills; a tool check for eval
copies; the wiring edits in #25; any change to `writing-skills`.

## Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | The review log accepts `planning-features`, `specifying-features`, `FEATURES_PLAN_REVIEW`, `FEATURE_REVIEW` and `INDEPENDENT_AUDIT` | VERIFIED: `review-log.py` `SKILLS`, `SELF_PHASES`, `REVIEWER_PHASES` |
| A2 | The run record has an optional `feature` field | VERIFIED: `review-log.py` `OPTIONAL_RUN_RECORD_FIELDS` |
| A3 | Known-gap entries accept an optional free-text `close_by` | VERIFIED: `architecture-delta/inputs.mjs` `parseGap` |
| A4 | `check` takes `--scope <elements>` and `--shards <file>` and reports shared hot spots | VERIFIED: `architecture-delta/args.mjs`, `match.mjs` |
| A5 | `check` reports stale gap entries, and decides staleness against the whole repository | VERIFIED: delta tool spec, "Scope" and "Known gap" |
| A6 | The tool does not report eval copies | VERIFIED: `report.mjs` sections (breaches, not yet reached, unmapped, hot spots) |
| A7 | `defining-architecture` leaves `close_by` to `planning-features` and hands off to both skills by name | VERIFIED: `skills/defining-architecture/SKILL.md` |
| A8 | Neither skill folder exists yet | VERIFIED: `ls skills/` |
| A9 | The overlay keys `model`, `deps-command`, `deps-file` and `separator` are defined by `defining-architecture` | VERIFIED: `skills/defining-architecture/ARCH_STANDARDS.md` |

## Threat Model (CIA)

- **Confidentiality.** The skills read only the repository, the epic, the model, the run records
  and the delta tool's output. The delta tool makes no network call (#20,
  `test_no_network_check_and_export`). The `deps-command` is the repository's own, named in its
  overlay. Evidence files describe failures generically and name no project.
- **Integrity.** The map and the design change only through the gated steps, then self-review, an
  independent audit and the owner's tag. Each skill's writes are limited by the Ownership table,
  and the review checks confirm the epic, the model and the code are unchanged. The gap file only
  shrinks at close: entries are removed only when the tool reports them stale, and a new breach
  goes to `defining-architecture`. Text from run records and tool output is quoted as data and
  never followed as instruction.
- **Availability.** The delta tool's file, element and edge limits and its `--timeout` bound every
  run (#20). The review circuit breakers bound the review loops.
- **Least privilege and supply chain.** No new dependency, no secrets, no network use.

## Acceptance criteria

- **AC-1** Given the repository after this work, when `uv run pytest` runs, then the contract test
  passes: both packages have their seven files, each description starts "Use when" and fits 500
  characters, every review-log skill and phase they name is accepted by the CLI, and each
  `SKILL.md` has at most 1,000 words.
- **AC-2** Given each `field-evidence.md`, when it is read against the Baseline table, then every
  baseline row assigned to that skill is recorded with its source and mapped to a rule in the
  skill, and every rule of the skill maps to a baseline row or to the change plan.
- **AC-3** Given each skill package, when it is read against this spec, then every gate, step,
  rule and review check in the skill's section is present in the package, and nothing in the
  package contradicts this spec or the change plan.

AC-2 and AC-3 are about an agent-facing text, so no automated test can verify them. They are
checked by the final code review reading the packages, and from then on by the field log.

## Future work (downstream cost)

| Item | Priority | Effort | Why |
|---|---|---|---|
| Wire the flow: `specifying-epics` capabilities and handoff, `specifying-work-items` reading the feature design (#25) | P1 | in #25 | The skills are not reachable from the flow until then |
| First real use of each skill, with its field-log entries | P1 | S | It is the skills' first behaviour test |
| A tool check for eval copies | P3 | M | The skill finds them by reading |
| Decide whether "baseline from field evidence" becomes a standing rule in `writing-skills` | P2 | S | This work departs from that skill's subagent baseline run |
