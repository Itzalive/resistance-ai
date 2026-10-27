# Long-term retrospective: spec, planning and implementation skills (March–October 2026)

Source: one downstream project (claude-assistant) — the full `.review_log.jsonl`, the beads database and git history — read together with the field report `2026-10-25-tiered-execution-and-plan-sizing.md`. That report covers five plans in detail; this one covers the whole history and checks where the report's conclusions hold more widely.

## 1. Data

| Source | Volume |
|---|---|
| Review log | 953 parseable entries (1 malformed), 160 work items, April and September–October 2026 |
| Beads | 465 issues (227 task, 118 feature, 51 epic, 44 bug); 365 closed |
| Git | 3,418 commits (Mar 385, Apr 847, Jun 12, Sep 951, Oct 1,223); since September: 332 `spec`, 134 `plan`, 566 `feat`, 236 `fix` |
| Docs | 149 specs, 155 plans |

Two eras. **April**: a GPT orchestrator with Claude Sonnet 4.6 as the cross-model reviewer. **September–October**: an Opus 5.5 orchestrator, with GPT almost never available.

## 2. Where the review effort goes

| Stage | Items | Log entries | Median per item | Max | Rejections |
|---|---|---|---|---|---|
| Epic | 3 | 17 | 4 | 9 | 10 |
| **Spec** | 74 | 374 | **5** | 15 | **143** |
| Plan | 90 | 227 | 2 | 8 | 46 |
| Code review | 105 | 191 | 1 | 11 | 52 |
| Survivability | 39 | 41 | 1 | 2 | 0 |

Rejection rate by month:

| Stage | Apr | Sep | Oct |
|---|---|---|---|
| Spec | 8/22 (36%) | 54/121 (45%) | 80/229 (35%) |
| Plan | 4/18 (22%) | 25/88 (28%) | **17/120 (14%)** |
| Code review | 15/26 (58%) | 19/73 (26%) | 17/91 (19%) |

Doc size by month:

| Month | Specs | Average lines | Plans | Average lines |
|---|---|---|---|---|
| Mar | 20 | 213 | 21 | 1,008 |
| Apr | 34 | 345 | 31 | 1,028 |
| Sep | 46 | 286 | 42 | 1,252 |
| Oct | 47 | 268 | 61 | 1,149 (largest 3,255) |

## 3. Findings

### F1. Spec review takes the most effort and finds the most valuable defects

The spec stage has more review entries than plan and code review put together. A typical spec runs: self-review r1 rejected → audit cr1 rejected → audit cr2 rejected or approved → cr3 approved → user approval. Round-one audits almost always find **design** defects, not wording:

- races and repeat-execution paths (a resend guard missing sequential repeats; a 412 conflict dropping results so an approved action ran twice; per-card clearing wiping a sibling action's in-flight state);
- silent-loss paths (failures that consume no number and stamp nothing; summariser exceptions swallowed);
- rules contradicting each other or the code (a guard contradicting the tool path; an example impossible under the exclusion rule);
- security claims that do not hold in production (a PII filter that does not strip names; the wrong `PIIStripper` flags on one path).

At least 46 of the 92 spec rejections name a contradiction, a silent path, a race, or behaviour that is unstated, undefined or unreachable. **These are the cheapest catches in the whole pipeline. Keep this stage strong.**

### F2. …but specs have taken on plan-level detail that churns

Since September, specs and their audits deal with test stubs, test counts and line citations: "44 collected tests not 41", "8 test sites not 3", "breaks the one-argument stubs at test_handler.py:531,566", "line drift", "citation 53-84". At least 19 spec rejections are about stubs, fakes, test sites, callers or citation drift. That is the plan writer's caller sweep (field report §4.2) moved into the spec, where every fix triggers another audit round and another `spec(...)` commit (332 since September — more than twice the 134 plan commits).

Specs also keep changing after approval. There are `SPEC_CORRECTION` / `SPEC_AMENDMENT` phases, "amendment" audit rounds (hux5.7 rounds 4–5, k84j.2), and decisions settled in chat and recorded in plans, beads and logs (field report §26). The skill has no amendment path, so each team improvises one.

### F3. "Cross-model" audit is nearly always same-family, and the rule is out of date

206 log entries record a same-family substitute ("GPT unavailable in this harness"). The skill hard-codes `gpt-5.4` ↔ `claude-sonnet-4.6`, which no longer matches the models in use. Same-family audits in fresh context still found blockers in round one on nearly every spec. **What the stage gets from the reviewer is independence (fresh context, no stake in the draft), not a different model family.** The current wording makes every audit look non-compliant and fills the log with excuses.

### F4. Plan review now finds mechanical defects, and in practice it has merged with execution

- Plan-stage rejections fell to 14% in October, which fits the field report's changes (resharding, the trust-boundary section, a wider caller sweep).
- What remains is mechanical: fixtures whose defaults change meaning, existing tests a task silently breaks, signatures that won't compile, and callers outside the grepped directories. The writer can find all of these with a required caller/test sweep.
- **Process drift:** 22 October `PLAN_REVIEW` / `UNIFIED_COHERENCE_CHECK` entries read "Unified Coherence Check executed Tasks 1–N on the branch …". For small plans the coordinator ran the plan inline and logged the coherence check afterwards, listing deviations. That is a sensible fast path, but no skill describes it, so it bypasses both the pre-execution gate and the subagent-driven-development review model without saying so.

### F5. Plans are about four times the size of their specs and haven't shrunk

Plans have averaged 1,000–1,250 lines since March, against specs of 210–345 lines. The writing-plans template asks for full code at every step, two failure-mode tests per task, and so on, which in effect writes the change twice. The field report puts planning plus alignment at ~40% of a plan's cost, and found that full code is what made cheaper executors safe. Both are true. The cost is worth paying only where a cheap executor will transcribe the code.

### F6. Code review at the end consistently finds real bugs

Across both eras the final review found crash paths from hostile or corrupt data (an out-of-range year → `ArithmeticException` replayed on every launch; a lone surrogate making a page unsealable), concurrency bugs (a shared `ErrorBedrock` across concurrent families; a missing `fsync` before rename), and behaviour that spec and plan both missed. The rejection rate fell from 58% to 19%, but the stage never went quiet. **Keep it as is.**

### F7. Survivability is not redundant everywhere, and its log hides what it finds

- The field report saw 5/5 kills after mutation-checked checkpoints and called the mutation lane mostly redundant.
- Across the whole history, survivability logged 41 entries and **never FAIL**, but 7 entries record CRITICAL FRICTION: the first mutation slate had survivors (e.g. k84j.8 3/5, k84j.10.2 4/6), tests were hardened, and the run was logged as PASS.
- Those survivors appeared on the **inline-execution path**, where no checkpoint reviewer ran mutations.
- Conclusion: the mutation lane is redundant only when checkpoints have already mutated the same diff. Its status should record the first-slate result, not the result after the fix.

### F8. Subagent-driven-development no longer describes how work is run

The skill still prescribes a spec reviewer and a quality reviewer after every task, tracked in TodoWrite. In practice there are three paths: (a) tiered executors with checkpoint reviews (the field report), (b) the coordinator executing a small plan inline, and (c) occasional per-task review (April). Only (c) is documented, and it is the costliest per task.

### F9. Owners are delegating approval gates

There are 10 entries such as "auto approve unless you need answers", "sections and spec auto-approved by Pete's standing rule", and "user pre-authorised proceeding to plan and implementation". Approving section by section, with a halt after each section, does not survive a long release. Owners skip it when nothing in it is a real decision. Field report §27 found the same: present only the blocking decisions, and list the rest as defaults applied.

### F10. The review log can't be used for retrospectives as written

- At least five key variants for the same fields: `timestamp`/`ts`/`date`, `item_id`/`bead_id`/`work_item`/`bead`, `status`/`verdict`/`result`, `skill`/`stage`.
- More than 50 distinct status strings, with bracketed and unbracketed copies of the same verdict.
- ~170 entries with no model.
- One malformed line (an unescaped backslash).
- Phase names made up per item (`TASK2_REFACTOR_OVERLAY_RERUN`, `SPEC2_PLAN_COHERENCE`).
- Old skill names (`brainstorming`, `using-superpowers`).

Every number in this report needed a normalising script. Field report §5–6 asked for machine-readable run records, and the current log can't give them.

### F11. Stale references in the skills

- subagent-driven-development tracks tasks in TodoWrite, which conflicts with bd.
- The writing-plans header says `superpowers:subagent-driven-development`, and plans are saved under `docs/superpowers/plans`.
- Hard-coded model IDs (F3).

All small, but agents copy them into every plan.

## 4. Recommendations

Ordered by expected value. **Replace** means rewriting the section or skill; **update** means targeted edits.

### R1. Replace the review model in subagent-driven-development (high value)

Rewrite the skill around the path that worked (field report §1, §9):

1. **Tiered executors.** The plan tags each task haiku, sonnet or opus. Drop one tier where the plan gives complete code. Keep opus for trust-boundary and conditional-write judgement.
2. **Checkpoint reviews.** Every 3–5 tasks, an opus reviewer runs a mutation for each "reviewer looks at" item on a scratch copy and reports killed/survived. For each survivor it gives verified test code, and it judges any executor deviation. Use the same reviewer for later rounds.
3. **Plan-end:** full suites, then code review (keep, F6), then survivability chaos probes (R6).
4. **Executor hygiene rules** from field report §10, in the implementer prompt: no `git stash`, no heredoc code edits, RED tests run before the implementation, tests inserted between functions, repository-state tests run after committing.
5. **Coordinator rules:** apply small verified fixes yourself; resume a stopped agent instead of restarting it.
6. **Name the inline fast path** (F4): a plan with ≤3 tasks and no trust-boundary change may run inline. One review at the end must then include mutations (R6).
7. Replace TodoWrite with the project's tracker. Delete the per-task two-stage review flow.

### R2. Split specs into behaviour and evidence, and add an amendment path (high value)

In specifying-work-items:

1. **The main body holds rules and decisions only.** Code facts (line numbers, test counts, stub names, caller lists) go in an *evidence appendix* that the plan writer re-verifies. The auditor checks that the evidence supports each rule, not that counts and line numbers are exact. This should cut the churn rounds behind F2.
2. **Decision register.** Every owner decision gets an id, the choice, the thresholds or gates it crosses, and what happens at each (field report §25). Plans and beads cite decision ids and don't restate them.
3. **Amendment path.** A post-approval change is an amendment: add it to the register, run an audit scoped to the sections it touches, and get owner sign-off. That replaces the improvised `SPEC_CORRECTION` / amendment rounds.
4. **Trust rules name every place they apply** (field report §8): readers of model-facing text, producers into model-facing blocks, and the parser for each.
5. **Spec-gap pass before planning any item of a multi-item release** (field report §26–27). Present the questions in tiers: blocking decisions, then "defaults applied unless you object".
6. **Section-by-section approval becomes a mode, not a rule** (F9). The default is to present the assumptions surface plus blocking decisions. The halt after each section applies only when the owner asks for it or the item is greenfield.

### R3. Rename "cross-model audit" to "independent audit" and remove hard-coded models (high value, low effort)

In specifying-work-items/review-workflow.md and writing-plans:

- **Required:** a fresh-context reviewer that gets only the spec, the rubric, the evidence and the work item.
- **Preferred:** a different model family when the harness has one. A repo overlay (e.g. `SPEC_DESIGN.md`) names the preferred reviewer model; the skill names none.
- Log `reviewer_model` and `independence: fresh-context | cross-family`. Stop treating same-family review as a substitute.
- The same reviewer continues into round 2 and later (field report §11). A new reviewer is used only after a rewrite.

### R4. Make writing-plans the owner of the caller sweep and of sizing (high value)

Fold in field report §4 and §7:

1. **Required caller/test sweep table:** each changed signature, every caller, test, fake, mock and assert across *all* source directories (scripts and evals included), the task that changes it, and the literal edit. This replaces most of what the alignment review finds (F4).
2. **Every commit green:** for each task, which callers move with it.
3. **Sizing by rule, never by number** (field report §18, §23–24): one behaviour per task, at most two core files plus tests, ≤2 entry paths per plan. If the task count runs well past ~8, propose a split. Report the line count but never target it.
4. **Pinning claims:** "no new tests: existing tests pin it" must name the test and the assert, for each moved behaviour (field report §21).
5. **Trust-boundary table**, required when untrusted text reaches a model or a parser.
6. **Open decisions up front.** Anything the spec doesn't settle goes back to the spec as an amendment (R2.3), not into the plan.
7. **Code detail by tier (experiment, measure it):** full code for every RED test and for haiku tasks. For sonnet and opus tasks, interfaces, tests and the caller table are enough. Judge it on executor-attributable checkpoint findings and on plan tokens (F5).
8. Rename the "Unified Coherence Check" to an **alignment check**. Point it at completeness and the per-task rule rather than at a three-vector cross-model ceremony. Remove the `superpowers:` names and paths.

### R5. Give the review log a strict schema and an append helper (medium value, unblocks every later retrospective)

- **One schema** in `skills/shared/review-log-jsonl.md`: `ts`, `item_id`, `skill`, `phase` (from an enum), `round`, `verdict` (`APPROVED | REJECTED | PASS | FAIL`), `reviewer_model`, `independence`, `findings` (list of `{severity, kind, text}`, with `kind` one of `missed-caller | weak-test | plan-hole | spec-hole | real-bug | slip | wording`), and optional `tokens`.
- **A small `scripts/review-log` append CLI** that validates the entry and escapes it correctly. Skills call the CLI instead of writing JSON by hand (that fixes the malformed line).
- **A run record per plan**, written at plan end by finishing-a-development-branch (field report §6): tasks, tiers, escalations, attempts per step, tokens per phase, findings per layer and kind, plan changes, slips.

### R6. Make survivability conditional and report it honestly (medium value)

- Skip the **mutation lane** when checkpoint reviews have already mutated every changed decision point. Run it in full on the inline path and on any plan without checkpoints (F7).
- Always run the **chaos lane**. The field report found it still useful.
- Log `first_slate: k/n` alongside the final result. A run with survivors is `FAIL → hardened`, not `PASS`.

### R7. Add a retrospective step to finishing-a-development-branch (medium value)

At plan end, ask: which layer found what, what the writer should have caught, which executor slips recurred, and whether this was a reshard. File skill feedback to resistance-engine's `docs/field-reports/`, not to the project. The field report shows that the owner asking "what did we do wrong?" produced the two biggest improvements; this step makes it routine.

### R8. Put release sequencing in specifying-epics (lower urgency)

Field report §7 and §14–17 belong before planning, at epic or release level:

- Count the entry paths each item touches, and how many places implement each rule today.
- If upcoming items repeat rules across three or more implementations, plan a behaviour-preserving consolidation item first, cut down to what those items change.
- Run a costing spike (~3% of the cost being estimated), with the cost model fitted from the project's own run records (R5). A second reshard request triggers the spike.

specifying-epics has 3 items so far (10/17 entries rejected); it's too early to judge the skill itself.

### R9. Clean up stale references (low effort)

TodoWrite → bd/the tracker; `superpowers:` → `resistance-engine:`; plan and spec paths become configurable; delete the hard-coded model IDs (R3).

## 5. What not to change

- **Spec independent audit:** it catches the most valuable defects (F1). R2 cuts the churn, not the scrutiny.
- **Final code review:** it found real bugs on every plan (F6).
- **Mutation-checking somewhere before finish:** the only open question is where it runs (R1.2 vs R6).
- **Complete RED test code in plans:** tests are the contract the cheap executors rely on.

## 6. Suggested order

1. R3 and R9: small text edits that remove the most noise.
2. R5: schema and helper, so later changes can be measured.
3. R1 and R4 together: the execution model and the plan format depend on each other.
4. R2: spec format and amendment path, trialled on the next release item, with rounds per spec compared against the current median of 5.
5. R6, R7, then R8.

Measures to watch afterwards: spec log entries per item (now 5), plan-stage rejection rate (now 14%), executor-attributable checkpoint findings, first-slate survivability kills, and tokens per task on the field report's ~0.42M fixed + ~0.15M per task model.
