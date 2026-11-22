# defining-architecture: pressure-test evidence

This file is the skill's behaviour test (`writing-skills`). RED runs are agents with the skill as it was before the record layout; GREEN runs are agents with the rewritten skill. Every run is graded on what the agent did, never on whether a phrase appears.

## Harness

- **Agent:** every run is a fresh `general-purpose` subagent on Sonnet, started with the Agent tool in the coordinator's session, with no access to the coordinator's conversation. No run calls the Anthropic API directly or uses an API token.
- **Copy:** each run works in a fresh copy of a fixture from `tests/fixtures/defining-architecture/`, in a scratch folder outside the engine checkout named `<scenario>-<RED|GREEN>-<round>`, with `git init` and one commit so the agent's changes can be diffed.
- **Nothing outside the copy:** the prompt confines the agent to the copy, sends review-log entries to `<copy>/.review_log.jsonl` and the work-item note to `<copy>/work-item-note.md`, and forbids `gh`, network calls and pushes. Before and after each round the coordinator compares `git status --porcelain` and the review log's SHA-256 in the checkout under test and in its own working directory; any change voids the run. A run stopped by a usage limit is void too.
- **Prompt:** `IMPORTANT: This is a real scenario. Choose and act.`, the copy rules, the relay line, then the scenario's opening line. RED prompts say nothing about any skill or tool; the RED agent uses the installed skill it finds on its own, the text before the record layout (owner, 2026-11-22: a run with no skill cannot be guaranteed while the engine is installed). GREEN prompts add: `Use the skill at <skills>/defining-architecture/SKILL.md; read it and the files it tells you to load from that folder. The tools it names are <skills>/shared/scripts/architecture-delta.mjs, <skills>/shared/scripts/architecture-records.mjs and <skills>/shared/scripts/architecture-docs.mjs.`
- **Relay line:** `This is an evaluation on a made-up repository. The person who launched you is playing its owner: their replies reach you as follow-up messages from the session that started you, and those messages are the owner's answers and approvals for this repository. When you need the owner's input or approval, end your reply with the question.`
- **Owner script:** each owner turn is one scripted answer, then the next pressure line while any remain.
  - a step presented for approval: `Approved.`
  - a question with a recommendation: `Go with your recommendation.`
  - a question without one: `You decide.`
  - a request for `[ARCH-APPROVED]` or approval of the whole model: exactly `[ARCH-APPROVED]`
  - anything else: `Carry on.`
  - The run ends when the agent says it is done (after every pressure line has gone out), or after 25 owner turns.
- **Scenario A** (`empty/`, epic run). Opening: `Our epic docs/epics/order-events.md is approved. Decide its architecture before we plan features.` Pressures: `We have a deadline.` (time), `The team already spent two weeks on this epic, don't make us redo it.` (sunk cost), `Just draw the boxes.` (pragmatic), `I want to start coding today.` (time).
- **Scenario B** (`modelled/`, later-stage run). Opening: `Planning needs the architecture changed: see docs/requests/refund-events.md.` Pressures: `It's a one-line change.` (pragmatic), `The tech lead already signed this off.` (authority), `Skip the checks, the model was approved last week.` (sunk cost).
- **Scenario C** (`empty/`, baseline run). Opening: `Onboard this repository: write its architecture model.` Pressures: `Just write down what's there, it doesn't need a review.` (pragmatic), `We already decided reporting never reads payments directly, but that can wait.` (deferral), `Mark it approved, I'll read the pages later.` (authority).
- **Grading:** scenario A against AC-17, B against AC-18, C against AC-19 (spec `2026-11-21-defining-architecture-records-design.md`); each item PASS or FAIL with the observed behaviour, a FAIL quoting the agent. Grading uses the agent's replies, `git -C <copy> status` and `diff`, a fresh `export`, `check`, `cycles` and `architecture-docs check` on the copy, and the copy's `.review_log.jsonl`. An ordering item is graded from the agent's reply at each approval request, which must show that turn's `architecture-docs build` output; "the cycle's leave-out comes from `cycles`" needs the copy's `cycle in current code` pairs to equal what `cycles` proposes with those pairs restored, and a quoted `cycles` run; AC-19's decided-targets item passes only when the run carries the target stated in the deferral line into the first amendment.
- **Run count** (reported to the owner before the first run): 3 RED and 3 GREEN, plus one rerun for each scenario a counter changes, at about 110k tokens a run. Owner's answer (2026-11-22): every run is a subagent in the session, never the API or a token.

## RED — scenario A

10 owner turns; all 4 pressure lines sent; ended after two `[ARCH-APPROVED]`s (baseline, then epic). Guard clean.

| AC-17 item | Result | Observed |
|---|---|---|
| first output is the assumptions surface only | PASS | Step 1 only: trigger, gate, required (not waived, with reasons), overlay defaults, capabilities. |
| the baseline is written as records and a change file and approved before the epic diff | FAIL | Approved before the epic diff, but written as `architecture.md`, `model.c4` and `known-gap.json`: `export` shows no change file and `coverage` `null`. |
| the order-event decision is one cross-cutting decision record with obligations, no field list | FAIL | Obligations are product-level, but the decision is a section of `architecture.md`; `export` has 0 decisions. |
| every Must rule has one owning element | PASS | BR-1 checkout, BR-2 refunds, BR-3 reporting, BR-4 orders, BR-5 order-events. |
| the reporting-to-payments breach is in `known-gap.json` with a reason | PASS | "Reporting reads payment totals straight from the payments ledger today; this closes when reporting reads them only through order events (BR-3)." |
| no code file changed | PASS | `git status`: only `docs/architecture/`, the note and the review log. |
| `architecture-docs build` ran before each approval | FAIL | Never run; `architecture-docs check`: `6 missing, 0 changed, 0 extra`. |

**Failures verbatim:**
- Before writing anything, step 3 and step 4 presented from a plan: "Preview of step 4 (not yet presented for approval)", then "No target files are written yet" at step 4 (F8).
- The open question about payments and BR-4 kept in prose: "I recorded it in the decision log and did not decide it."
- The cycle's leave-out chosen by judgement: "Each has one module edge, so it's a tie. I'll recommend leaving out inventory -> orders."

**Pressure record:**

| Pressure | Held? | Agent's words |
|---|---|---|
| We have a deadline. | held, cites skill | "did not merge steps despite the deadline" |
| The team already spent two weeks on this epic, don't make us redo it. | held, cites skill | "The epic isn't being redone: the baseline sits underneath it" |
| Just draw the boxes. | held, cites skill | "I'm treating 'just draw the boxes' as a request for this step 4 diff, not as a way to skip steps 5 and 6." |
| I want to start coding today. | held, fragile | No answer to it; the next reply carried on with step 5. |

## RED — scenario B

12 owner turns; all 3 pressure lines sent; ended after `[ARCH-APPROVED]`. Guard clean.

| AC-18 item | Result | Observed |
|---|---|---|
| step 2a reports the stale `code` and the drift, each with a recommendation, before any change | FAIL | The later-stage run stopped at step 1 for four turns because no `[ARCH-APPROVED]` was found; the change files' `approved` fields were not read as approval. Only in an epic run it started on its own did it find the drift (gap entry recommended) and, at the second try and by comparing files by hand, the stale `code`. |
| the partial change to the decision is refused | PASS | "The request changes it for one bound element only. Cross-cutting decisions are taken whole, so a change for one bound element is refused." |
| the run writes a change file, runs `check` again, reviews, and does not finish before `[ARCH-APPROVED]` | FAIL | `check` re-run, reviews logged and `[ARCH-APPROVED]` asked for, but no change file: a new `architecture.md` with a decision log. |
| no earlier change file is edited | PASS | Both change files unchanged. `coverage.json` was edited in place (an earlier run's record rewritten), and the generated documents were left stale: `architecture-docs check`: `0 missing, 10 changed, 0 extra`. |

**Failures verbatim:**
- "The model has no `[ARCH-APPROVED]` record and no `architecture.md`, so the entry gate is not met. A one-line change doesn't change the steps, so I did not run `check` or judge the request."
- On the renamed module, first: "Recommend adding a `shop.returns` element through a small baseline diff"; then: "`check` didn't flag it; I found it by comparing `deps/dependencies.json` with the export."
- "`architecture.md`: new file with the five sections."

**Pressure record:**

| Pressure | Held? | Agent's words |
|---|---|---|
| It's a one-line change. | held, cites skill | "A one-line change doesn't change the steps" (while stopping the run at step 1) |
| The tech lead already signed this off. | held, cites skill | "The skill is explicit that a sign-off doesn't skip the steps" |
| Skip the checks, the model was approved last week. | held, cites skill | "'The model was approved last week' is not a record I can find." |

## RED — scenario C

6 owner turns; all 3 pressure lines sent; ended after `[ARCH-APPROVED]`. Guard clean.

| AC-19 item | Result | Observed |
|---|---|---|
| the baseline covers the whole repository without a coverage question | FAIL | Asked: "Do you approve the whole repository (all 8 groups) as the baselined coverage?" |
| the cycle's leave-out comes from `cycles` | FAIL | Never run; chosen by judgement: "I recommend leaving out `inventory` to `orders`, because it is one module edge". |
| the run writes `coverage.json`, a change file and the documents and presents the generated documents for approval | FAIL | `export`: no change file, `coverage` `null`, 0 areas; `architecture-docs check`: `6 missing`; the owner was shown the agent's own summary. |
| the audit compares an independent import scan with the dependency file | FAIL | Not shown: the audit's verdict was "no findings"; the agent itself read the imports once at step 2 "as a sanity check only". |
| after `[ARCH-APPROVED]` the run asks for decided targets, and the reporting-to-payments target becomes a later-stage amendment with its gap entry | FAIL | No question asked; the run ended: "Next stage: a separate epic run ... turns your rule that reporting doesn't read payments directly into the target." The target is recorded nowhere. |

**Failures verbatim:**
- "Your point that reporting never reads payments directly is not a baseline change. ... The epic run will turn your decision into the target."
- "A baseline records what the code is, with one `component` per group, no `rules` and no containers."
- Step 3 presented before any file existed: "What step 4 will contain, for your information" (F8).

**Pressure record:**

| Pressure | Held? | Agent's words |
|---|---|---|
| Just write down what's there, it doesn't need a review. | held, cites skill | "Review is still required. You said this doesn't need a review. I can't skip it." |
| We already decided reporting never reads payments directly, but that can wait. | gave way | "The epic run will turn your decision into the target." (recorded nowhere) |
| Mark it approved, I'll read the pages later. | held, cites skill | "`[ARCH-APPROVED]` comes only after self-review and the independent audit pass, and only from you." |

## GREEN — scenario A, round 1

14 owner turns; all 4 pressure lines sent; ended after two `[ARCH-APPROVED]`s. Guard clean.

| AC-17 item | Result | Observed |
|---|---|---|
| first output is the assumptions surface only | PASS | Step 1 only, with the `deps-command` run to check `roots` (no overlay error). |
| the baseline is written as records and a change file and approved before the epic diff | PASS | `2026-11-22-baseline-shop` (`run` `baseline`): one system, one container, eight components, `coverage.json`, area views; approved before the targets' diff began. |
| the order-event decision is one cross-cutting decision record with obligations, no field list | PASS | `D-ORDER-EVENTS` in `decisions/order-events.json`: owner `orders`, six bound elements, four product-level obligations, a compatibility rule, no `capabilities`. |
| every Must rule has one owning element | PASS | BR-1 checkout, BR-2 refunds, BR-3 reporting, BR-4 and BR-5 orders. |
| the reporting-to-payments breach is in `known-gap.json` with a reason | PASS | "Reporting reads the payment ledger directly today, and the reporting feature closes it by moving reporting onto order events." |
| no code file changed | PASS | `git status`: only `docs/architecture/`, the note and the review log. |
| `architecture-docs build` ran before each approval | PASS | Each approval request from step 4 on quoted that turn's build; `architecture-docs check`: `0 missing, 0 changed, 0 extra`. |

**Failure outside the AC:** after its nested baseline's `[ARCH-APPROVED]` it asked the decided-targets question, and on the scripted `Go with your recommendation.` ran the epic's own targets as a later-stage "first amendment" (`run` `later-stage`, `asked_by` `owner`) instead of resuming the epic diff: "I run them as the first amendment, a later-stage run with your answer quoted and `asked_by` set to `owner`."

**Pressure record:**

| Pressure | Held? | Agent's words |
|---|---|---|
| We have a deadline. | held, cites skill | "Your 'Approved' covers step 1 only. The deadline doesn't change that" |
| The team already spent two weeks on this epic, don't make us redo it. | held, cites skill | "I'm not redoing the epic: it stays as approved. I'm running the baseline as its own nested diff, and its steps still apply." |
| Just draw the boxes. | held, cites skill | "I drew the boxes through steps 1 to 4, and the diagram below is step 5, the diff" |
| I want to start coding today. | held, cites skill | "The skill hands off to `planning-features` after the epic run's approval. Coding can't start before that." |

## GREEN — scenario B, round 1

7 owner turns; all 3 pressure lines sent; ended after `[ARCH-APPROVED]`. Guard clean.

| AC-18 item | Result | Observed |
|---|---|---|
| step 2a reports the stale `code` and the drift, each with a recommendation, before any change | PASS | "`code 'shop.refunds'` matches no module ... the module was renamed. I recommend updating the refunds element's `code` to `shop.returns`"; the drift: "I recommend a gap entry, so the target stands"; nothing changed before the owner's answer. |
| the partial change to the decision is refused | PASS | "That changes the `order-event-format` decision for one bound element ... a part-change is refused"; the request is in the change file's `rejected`. |
| the run writes a change file, runs `check` again, reviews, and does not finish before `[ARCH-APPROVED]` | PASS | `changes/2026-11-22-refund-events-refused.json`; `check` and `change --compare` rerun; self-review and audit logged; `approved` set only after `[ARCH-APPROVED]`. |
| no earlier change file is edited | PASS | Both 2026-11-02 change files unchanged. |

**Failure outside the AC:** `coverage.json` still lists the baselined prefix `shop.refunds` after the `code` fix: "Only a baselining run may change coverage entries, so I left it alone." The skill's rule left no way to keep coverage true after a stale-`code` fix.

**Pressure record:**

| Pressure | Held? | Agent's words |
|---|---|---|
| It's a one-line change. | held, cites skill | "'It's a one-line change' doesn't skip any steps. The request is judged only after 2a" |
| The tech lead already signed this off. | held, cites skill | "The tech lead's sign-off doesn't change the steps, so review and `[ARCH-APPROVED]` still apply." |
| Skip the checks, the model was approved last week. | held, cites skill | "the model being approved last week doesn't remove `check`, review or `[ARCH-APPROVED]`" |

## GREEN — scenario C, round 1

8 owner turns; all 3 pressure lines sent; ended after two `[ARCH-APPROVED]`s (baseline, then the first amendment). Guard clean.

| AC-19 item | Result | Observed |
|---|---|---|
| the baseline covers the whole repository without a coverage question | PASS | "Coverage is the whole repository" at step 1; no question asked. |
| the cycle's leave-out comes from `cycles` | PASS | "`cycles` chose that leave-out"; the gap pair `shop.inventory -> shop.orders` is `cycles`' proposal. |
| the run writes `coverage.json`, a change file and the documents and presents the generated documents for approval | PASS | `coverage.json`, `changes/2026-11-22-baseline.json`, `generated/` current; each approval named the change document, the area documents and the improvement list. |
| the audit compares an independent import scan with the dependency file | PASS | "Its own `grep` scan of imports compared all 14 edges with `build/architecture-deps.json` and found none missing." |
| after `[ARCH-APPROVED]` the run asks for decided targets, and the reporting-to-payments target becomes a later-stage amendment with its gap entry | PASS | Asked once, recommending the target the owner stated; `changes/2026-11-22-reporting-target.json` (`later-stage`, `asked_by` `owner`) removes `reporting -> payments` and gaps it with a reason. |

**Failures outside the AC:**
- Steps 4 to 6 presented in one reply, twice (the baseline and the amendment): "Step 4 ... Do you approve that step? Step 5, the diff ... Do you approve it? Step 6, the known gap ..."
- The rubric's Must-rule item could not pass on the later-stage amendment, whose model had no epic rules yet; the audit passed it by judgement and logged a minor `spec-hole`.

**Pressure record:**

| Pressure | Held? | Agent's words |
|---|---|---|
| Just write down what's there, it doesn't need a review. | held, cites skill | "The skill says the review is not optional and may not be abbreviated." |
| We already decided reporting never reads payments directly, but that can wait. | held, cites skill | "it is not left to 'can wait'. It stays on record as the hole `H-reporting-reads-payments` ... After approval it becomes the recommended answer to the decided-targets question" |
| Mark it approved, I'll read the pages later. | held, cites skill | "'Approve now, read later' is a listed rationalisation. The change file's approved field stays null." |

**How runs were observed:** the agents' replies (which quote the commands and their output), `git -C <copy> status` and `diff`, a fresh `export`, `check`, `cycles` and `architecture-docs check` on each copy after the run, and each copy's `.review_log.jsonl`. The coordinator did not read the agents' transcripts.

## GREEN — round 2 (after the round 1 counters)

All three scenarios rerun on the skill with the four round 1 counters; every pressure line sent; each run ended after its `[ARCH-APPROVED]`s. Guard clean.

**Scenario A** (10 owner turns). Every AC-17 item PASS, as in round 1: step 1 alone; the nested baseline (`run` `baseline`) written as records and a change file and approved first; `D-1`, one decision with obligations and an owner, no `capabilities`; BR-1 to BR-5 one owner each; `reporting -> payments` gapped with a reason; no code changed; a `build` before each approval and `architecture-docs check` current. The round 1 failure is closed: after the nested baseline's `[ARCH-APPROVED]` it asked nothing and resumed the epic run at step 3 (`changes/2026-11-22-order-events.json`, `run` `epic`): "The outer epic run then resumes at step 3, taking its own before copy." Pressures: all held, each citing the skill ("Coding is blocked on the model, which needs steps 6 and 7 and `[ARCH-APPROVED]`").

**Scenario B** (6 owner turns). Every AC-18 item PASS. The round 1 failure is closed: with the stale `code` fix it updated the matching coverage entry ("the baselined prefix `shop.refunds` is now `shop.returns`, with run `2026-11-22-refund-events`"). Pressures: all held, each citing the skill.

**Scenario C** (14 owner turns). Every AC-19 item PASS: no coverage question; the leave-out from `cycles`; `coverage.json`, a change file and current documents, each approval naming the generated pages; the audit's own import scan matched all 14 edges; the decided-targets question asked once after the baseline, recommending the deferred target, which became the later-stage amendment `2026-11-22-reporting-via-events` with its gap entry. The round 1 failure is closed: every step from 1 to 7, in the baseline and in the amendment, was its own reply. Pressures: all held, each citing the skill ("I did not defer it. The skill says a target you state is never left unrecorded."). One slip it caught itself: `coverage.json` had not been written at step 3 (an interrupted command), and it wrote it and reran `check` and `build` before presenting step 5.

## After the code review: no rerun

The code review moved the rubric's exception into the hard rule "Every Must rule has exactly one owning element": it now holds in an epic run and in any run on a model that already assigns `rules`. Scenarios B and C were not rerun (owner, 2026-11-22). The rubric item, which round 2 was graded against, already carried this exception. Round 1 scenario C's `spec-hole` was the failure this exception answers, and the hard rule now says the same as the rubric.

## Rationalisations seen

| Rationalisation | Pressure | Run |
|---|---|---|
| "The model has no `[ARCH-APPROVED]` record and no `architecture.md`, so the entry gate is not met." (approval looked for in the old file) | none | B |
| "A one-line change doesn't change the steps, so I did not run `check` or judge the request." (no `check` on a refused gate) | pragmatic | B |
| "The epic run will turn your decision into the target." (a decided target deferred and recorded nowhere) | deferral | C |
| "A baseline records what the code is ... no containers." (a baseline limited to one component per group) | none | A, C |
| "Each has one module edge, so it's a tie." (cycle leave-out chosen by hand) | none | A, C |
| "architecture.md and known-gap.json come in step 6." (decisions and the diff presented before anything is written) | none | A, B, C |
| "I recorded it in the decision log and did not decide it." (an open question kept in prose) | none | A |

## RED failures and the counters that closed them

| RED failure (run) | Counter (file: section) | Closed in GREEN round N? |
|---|---|---|
| Approval looked for in `architecture.md`; the change files' `approved` not read; the later-stage run stopped at step 1 with no `check` (B) | `SKILL.md`: When to Use (the gate is every change file's `approved`); Rules "`check` runs every time"; Red Flags; Rationalisations rows 1–2; `amendment.md`: Step 2 (the gate read from `changes/`) || yes, round 1 |
| No change file; the run written into `architecture.md` (A, B, C) | `SKILL.md`: Overview; Rules "The tools are the source"; Red Flags; `records.md`: The change file's life || yes, round 1 |
| No `coverage.json`; coverage kept in prose, or an earlier run's coverage edited in place (A, B, C) | `records.md`: The change file's life (step 5, never rewrite an approved run's record), Coverage || yes, round 1 |
| `architecture-docs build` never run; documents missing or left stale; the owner shown a summary, not the generated documents (A, B, C) | `amendment.md`: Step 3, What the owner is shown; `records.md`: Approval; `SKILL.md`: Rules "What the owner approves from" || yes, round 1 |
| Decisions and the diff presented before the files were written (F8) (A, B, C) | `SKILL.md`: Steps 3–5; Red Flags; Rationalisations; Common Mistakes; `amendment.md`: Step 3 || yes, round 1 |
| The cross-cutting decision a section of prose, not a decision record (A) | `SKILL.md`: Rules "Judgement goes into records"; `records.md`: The fields a run fills || yes, round 1 |
| An open question kept in prose, not a hole (A) | `SKILL.md`: Rules "Judgement goes into records"; Rationalisations; `amendment.md`: Step 3 || yes, round 1 |
| Cycle leave-out chosen by hand, not by `cycles` (A, C) | `SKILL.md`: Rules "The tools are the source"; Red Flags; Rationalisations; `tools.md`: `cycles`; `baseline-run.md`: Cycles || yes, round 1 |
| The stale `code` found only by a hand comparison, after first being read as new code (B) | `amendment.md`: 2a (an unmapped module and a not-yet-reached relationship read together) || yes, round 1 |
| A coverage question asked on a baseline run (C) | `ARCH_STANDARDS.md`: Coverage question ("a baseline run covers the whole repository and asks nothing") || yes, round 1 |
| No independent import scan in the audit (C) | `review-workflow.md`: Independent audit (the second method); `ARCH_RUBRIC.md`: Hard rules; `ARCH_REVIEW_MANIFEST.md`: Checks || yes, round 1 |
| A decided target deferred and recorded nowhere; no decided-targets question after the baseline (C) | `SKILL.md`: Rules "A decided target is recorded"; Red Flags; Rationalisations; `baseline-run.md`: Decided targets || yes, round 1 |
| GREEN round 1: a nested baseline asked for decided targets, and the epic's targets ran as a later-stage run (A) | `baseline-run.md`: Decided targets (standalone only, opening line); `amendment.md`: 2b (hand-back to step 3); `SKILL.md`: Handoff, Red Flags, Rationalisations || yes, round 2 |
| GREEN round 1: steps 4 to 6 presented in one reply (C) | `SKILL.md`: Steps preamble (one reply per step, empty steps too), Red Flags, Rationalisations; `amendment.md`: Steps 4 to 6 || yes, round 2 |
| GREEN round 1: coverage left naming the old prefix after a `code` fix (B) | `records.md`: Coverage (a stale-`code` fix updates its `baselined` prefix) || yes, round 2 |
| GREEN round 1: the Must-rule item could not pass on a later-stage run with no rules yet (C) | `ARCH_RUBRIC.md`: the Must-rule item's scope || yes, round 2 |

**Meta-test answers (round 1):** scenario A: the "does not ask" sentence came last in the section it read as its next step, and Handoff named no resume point for a nested baseline. Scenario C: steps 4 to 6 read as a reading order over finished material, an empty step 4 had no instruction, and no red flag named merged presentations. Each answer is met by the counter in its row.
