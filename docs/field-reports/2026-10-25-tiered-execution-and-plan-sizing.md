# Field report: tiered execution, checkpoint reviews and plan sizing (writing-plans, subagent-driven-development)

Source: five implementation plans run in one downstream project (a Python service with an LLM front end, three entry paths that show stored records to models, and an eval suite), October 2026. Project specifics are left out; numbers are the project's own tallies. Draft — to be finished after one more data point (an architecture spike), then turned into skill changes in a separate session.

## 1. What was tried

A trial format layered on writing-plans and subagent-driven-development:

- **Model tag per task.** The plan writer (Opus) tags each task: haiku for mechanical work with complete code and exact commands, sonnet by default, opus where a mistake is costly (concurrency, conditional writes, idempotency, trust boundaries).
- **Checkpoints.** Every 3–5 tasks (after cross-cutting changes, around opus tasks, at subsystem ends) an Opus reviewer reads the code and test diffs against the plan and spec, runs one quiet test command, and runs the full suite only when the group was cross-cutting. Weak tests are the main thing it looks for.
- **Escalation.** Two failures move a task one model up. Checkpoint fixes are commits on top; holes in the plan go back to the plan.
- **Plan end.** Full suites, survivability, code review.
- **Tallies.** Executor model, escalations and tokens per task, recorded on the work item.

## 2. Results

| Plan | Tasks | Lines | Plan changes during execution | Escalations | Total tokens |
|---|---|---|---|---|---|
| A (library contract) | 11 | 2,036 | 0 | 0 | ~1.9M (plan 735k) |
| B (format change across four entry paths) | 16 | 2,761 | 6, then resharded | 0 | ~1.32M for the first shard and planning |
| B2 (one entry path, after reshard) | 7 | 1,535 | 0 | 0 | ~1.6M |
| B3 (the other paths and evals) | 7 | 1,361 | 0 | 0 | ~1.2M before plan end |

- **No escalations in about 25 executor runs.** Haiku handled mechanical tasks; sonnet handled breadth tasks once every edit was written out in full; opus tasks were the trust-boundary and conditional-write work. The tiers look right as specified.
- **Cost shape** (per plan, roughly): planning plus alignment review ~40%, checkpoint reviews and their fixes ~25%, executors ~25%, plan-end code review ~10%. Planning is the largest single cost; the split does not pay for itself unless plans are small enough to be planned once.

### Zero escalations is a calibration signal, not success

- Escalation only fires on a loud failure (two failed attempts). No opus-tagged task was ever tried on sonnet, so "no escalations" shows no task was under-tiered, not that any was correctly tiered.
- The plans gave complete code and every edit in full, so executors mostly transcribed and tested; that is exactly the work cheaper tiers do well.
- Executor slips (stash, heredocs, RED written with the code, a test inserted inside another) happened at every tier, opus included: they are process slips, not capability limits, and a higher tier did not prevent them.
- Almost every checkpoint finding was a plan or spec defect, not an executor one.
- **Target:** a low escalation rate (~5–15%) shows tasks are tiered at the edge of each model's ability. A failed cheap attempt plus a redo is cheap and loud; that is the insurance being paid for.
- **The real risk is silent quality loss** (tests that pass but prove nothing, subtle security slips), which escalations do not measure. Lower executor tiers only where an Opus checkpoint review with mutations checks the result, and measure **executor-attributable checkpoint findings** alongside the escalation rate and tokens per task. If lower tiers raise executor-attributable findings, raise them back.
- **Expected saving is modest:** executors are ~25% of a plan's cost, so tier drops save perhaps 10–15%; planning plus alignment (~40%) is the bigger lever.
- **Proposed next experiment:** where the plan gives complete code, drop one tier (opus→sonnet except for genuine trust-boundary or conditional-write judgement; sonnet→haiku where every edit is listed in full); keep opus for checkpoint reviews.

## 3. What each review layer caught

| Layer | What it found | Verdict |
|---|---|---|
| Alignment review (plan vs spec vs code, read-only) | Almost entirely **missed callers**: a consumer committed before its dependency (A); five tests/fakes/asserts of changed signatures and two eval readers (B); a caller in `scripts/`, outside the directories grepped (B2); none (B3) | Worth it, but its findings are mechanical — the plan writer should have found them |
| Checkpoint review (Opus, mutation-checked) | **Weak tests** at almost every checkpoint (an assert that only checks non-null; a boundary not tested; a mutation that survives); twice a **plan hole** (code contradicting its own test; a test named as proof that never reaches the code); once a **spec-level trust-boundary hole** the alignment review missed (untrusted text reachable by a parser through a block the spec never mentioned) | The most valuable layer. It earns its cost when it runs real mutations on a scratch copy, not just reads |
| Plan-end code review | Real fixes every time (4, 4): one security gap (unfiltered names reaching the model), behaviour gaps, cross-item hand-offs | Keep. It sees across tasks, which checkpoint reviews don't |
| Plan-end survivability | 5/5 mutants killed both times | Mostly redundant after mutation-checked checkpoints; chaos probes still useful |

## 4. Lessons for the skills

### writing-plans
1. **Cap plan size by tasks and entry paths, not lines** (see 18). Split above ~8 tasks or when a plan touches more than two entry paths. The 16-task plan needed six changes mid-execution and a reshard; the 7-task shards needed none.
2. **Caller sweep is the writer's job, not the reviewer's.** For every changed signature, grep every caller *and* every test, fake, mock and assert across all source directories — including scripts and evals, not only the main package — and write each edit out in full. "Replacement rules" instead of literal edits failed review every time.
3. **Every commit green.** State, per task, which callers move with it; check no task consumes something a later task adds.
4. **Trust-boundary section (required when anything untrusted reaches a model or a parser):** a table of every reader of model-facing text and every producer into a model-facing block, what text each receives, and the task and test that prove it. Introduced after the hole above; the next two plans had clean first checkpoints and a first-round alignment pass.
5. **Boundary tests at every threshold** (at, below, above), and composed behaviour tested through the real entry point, not only unit-tested helpers.
6. **Docs present tense** in plans' docstrings and comments (no history narration).
7. **Open decisions up front**: anything the spec doesn't settle goes to the owner with a recommendation before execution; decisions found mid-execution were the costliest changes.

### specifying-work-items (or the spec template)
8. **An injection or trust rule must name every place it is applied.** "Only cells we write are read for handles" was true but incomplete: the spec never said which readers exist or what text reaches them, so the plan built the parser and its consumers in different tasks without the check.

### subagent-driven-development
9. **Checkpoint reviewer brief:** list the checkpoint's "reviewer looks at" items, require a mutation per item on a scratch copy (`git archive HEAD | tar -x`), report killed/survived with the test that kills it, and give verified test code for survivors. Ask it to judge executor deviations (which of code vs test is the truth).
10. **Executor hygiene rules** (each came from a real slip): never `git stash` in a shared checkout (worktrees share the stash); never write code through shell heredocs (they mangled backslash escapes three times on Windows Git Bash — use the edit tools); write RED tests and run them before the implementation (two executors wrote both together); insert new tests between functions, never inside one; run tests that check repository state only after committing.
11. **Continue the same reviewer for later rounds** (send it the fix commit): round 2 cost 4k–36k tokens against 250k+ for a fresh reviewer, and it verifies its own findings.
12. **Coordinator applies small verified fixes itself**; spawning a fix agent for two pre-verified tests cost more than the fix.
13. **Resume, don't restart, after a rate limit**: a stopped agent's work is saved; messaging it to continue lost nothing.

## 5. How the skills were checked in use (method worth keeping)

- **Trial defined on the work item**, not in memory: what changes, how it's judged ("judged against cost at the end"), and that it becomes a rule only if it works.
- **Per-run tallies** (model, escalations, tokens per task and per review) on each work item, so plans can be compared.
- **A/B by accident, then on purpose:** the over-large plan vs its reshards gave a clean comparison (same spec, same writer, same reviewers; plan size and the trust-boundary section changed).
- **Count findings by layer and by kind** (missed caller, weak test, plan hole, spec hole, real bug) — that is what showed the alignment review's findings were mechanical and the checkpoint review's were not.
- **Review log** (`.review_log.jsonl`) entries per phase with the raw reasons, so outcomes are machine-readable later.
- **Owner pauses to ask "what did we do wrong?"** produced the two biggest changes (resharding; the trust-boundary section). A planned retrospective prompt at each plan end would make that routine.

## 6. Ideas for letting the skills improve from use

- **A run record per plan**, written by the coordinator at plan end in a fixed shape: tasks, tiers, escalations, tokens per phase, findings per layer and kind, plan changes during execution, slips. A later skill session can aggregate many.
- **A retrospective step in finishing-a-development-branch** that asks: which layer found what; what the writer should have caught; which executor slips recurred; and files skill feedback where the skills live (not in the project).
- **Track coordinator overhead** — not measured in this trial; it is probably large in long sessions.
- **Watch for repeated reshards** as a signal of coupling in the codebase rather than a planning failure (section 7).

## 7. Repeated resharding is a coupling signal (architecture spike)

A read-only spike (~180k tokens) costed the release's remaining items before planning them.

- **Finding:** the resharding came from coupling, not only plan size. Every feature item in the release changes "the same thing on each of N entry paths", and each path has its own reader, validator and write call for it, so every new rule costs N tasks, N test sets and N alignment arguments. **The number of entry paths an item touches, not its line count, is what crosses the reshard threshold.**
- **Cost model fitted from the tallies:** about 0.42M tokens fixed per plan (planning base plus code review) plus about 0.15M per task, within ~±10% across three plans. Splitting a plan by path multiplies the fixed cost and duplicates the rule work.
- **Result:** a behaviour-preserving consolidation item first (one shared reader for model actions, one shared writer returning a structured outcome, one shared builder for what the model was shown), then the three feature items, is estimated at ~6.0M against ~8.4M as they stand (saving range 1.0–3.5M; break-even sits well inside the duplicated work of the first feature item alone).
- **What did not pay back** within the release: moving evals onto production seams (the next items don't change those shapes), splitting a large file (the consolidation moves its relevant parts out anyway), a full shared context builder (rendering was already shared).

### Lessons for the skills

14. **Before planning an item, count its entry paths and how many places implement each of its rules today.** If several upcoming items each restate rules across the same three or more implementations, plan a behaviour-preserving consolidation item first; it is usually cheaper than resharding every feature item by path.
15. **Cut the consolidation to what the upcoming items change** (shared reader, writer, outcome types). Leave tidy-ups that only reduce reading cost — file splits, evals onto seams the next items don't touch — until an item needs them.
16. **A costing spike before a run of items is cheap** (~3% of the work it costs out) and is the right place to ask "should we consolidate first?"; fit the cost model from the project's own tallies rather than guessing.
17. **Treat a second reshard request as a trigger** for that spike rather than just splitting again.
18. **A size number given to the plan writer becomes a target.** With a ~1,500 / ~1,300-line cap, first drafts landed just over it twice (1,535 and 1,313), the signature of writing to the number. No missing code was traced to it (alignment found missed callers only from too-narrow grep scope), but a line target competes with "write every edit in full", and compression is the easy way to meet it. Size the plan by **tasks and entry paths** (≈7–8 tasks, ≤2 entry paths; over that, propose a split before writing tasks); report line count but never target it; tell the writer never to shorten or omit an edit to save space; have the alignment reviewer check completeness, not length.
23. **The same happens with a task count.** Replacing the line target with "about 7–8 tasks" moved the pressure: the next plan landed on exactly 8 tasks at ~377 lines per task, against ~200 in the two plans before — tasks packed to stay under the count. Give the writer no target numbers at all. Give it the per-task rule the skill already has (one behaviour per task, at most two core files plus tests unless it is a true atomic change across all callers) and let the task count fall out; a plan whose count then runs well past ~8, or touches more than two entry paths, is split. The reviewer checks each task against the per-task rule, not the plan against a total.
24. **Evidence for 23:** the alignment reviewer re-tasked that 8-task plan by the two-core-files rule and got **15 tasks** — five of the eight held two or three tasks each — and a clean split into two plans along the spec's own seam (one plan with no trust-boundary change, one carrying all of it, the latter with opus checkpoint reviews). The owner chose the split. The same review also found a trust-boundary race that a packed task had hidden: one live seen-set shared across a round of parallel tool calls let a sibling search validate a handle the model had only guessed (fix: snapshot per round). Packed tasks hide cross-task interactions; small tasks surface them.
25. **State decision consequences against the real gates.** The plan said a missing confidence would make an action "wait for approval"; checked against the actual floors, it would have been silently dropped. The reviewer caught it; the owner then chose a per-type default that does wait for approval. Every open decision should name the concrete thresholds it crosses and what happens at each.
26. **Decisions surfacing during planning are spec gaps — go back to the spec.** Across four consecutive items, plan writers and alignment reviewers kept raising behaviour rules the approved release spec had left open (defaults that decide whether an action waits for approval, whether an edit may change what a record is about, what an empty list means, id composition, a concurrency rule). Each was settled in chat and recorded in plans, beads and review logs — scattered, not in the spec — and each find cost a plan rewrite and another review round (~300k tokens). Fix: (a) amend the spec with every decision already made, so it is the single source of truth again; (b) before planning each remaining item, run a short read-only **spec-gap pass** (one agent, ~100–150k: the item's spec sections against the code as built, every open behaviour question with a recommendation), have the owner decide, amend, then plan. A release-wide spec written before its enabling refactor existed should expect this.
27. **A spec-gap pass works, but present its output in tiers.** The first pass (~135k tokens) found 21 open questions for one item — 2 that blocked planning, 19 with safe recommended defaults — and two of them also invalidated a plan already written for the previous item. The owner accepted all of it but found the volume heavy to decide at once. Present only the blocking questions and any default a user would notice as decisions; record the rest as "defaults applied unless you object" in one list. Run the gap pass before planning *any* item whose rules touch the same behaviour, not just the next one — here a gap pass run one item earlier would have saved a plan rewrite.

## 8. Final tallies

- B3 (the last shard): ~1.54M, 7 tasks, first-round alignment pass, no plan changes during execution, no escalations; code review found 6 fixes, one a real correctness slip.

## 9. Tier-drop experiment (consolidation item, behaviour-preserving)

Every task tagged one tier lower than the writer otherwise would (4 haiku, 3 sonnet, no opus executors); opus kept for checkpoint reviews.

- **Result:** 0 escalations, one attempt per step on every task; **0 executor-attributable correctness issues** across three mutation-checked checkpoints (2 cosmetic slips, one per tier).
- **Test gaps were found at every checkpoint, all plan-attributable** — worst at the writer checkpoint, where 20 of 43 mutants survived because the plan said "no new tests" for moved write paths and relied on existing tests that did not pin retry counts, refusal logs or kept-value rules.
- **Reviewer's verdict on the tasks dropped from opus:** safe *because the plan wrote the code and had settled the hard choices* (retry boundary, outcome mapping, kept-value rules). What the higher tier would have added is noticing that the given tests don't pin those behaviours — the lower tier transcribed faithfully and did not raise it.
- **Cost:** ~1.78M for 7 tasks, ~20% over the spike's estimate; executors ~27%, planning plus alignment ~38%, checkpoint reviews and their fixes ~23%, code review and fixes ~12%. Haiku used ~70–80k tokens per task against ~55–60k for sonnet on similar tasks, so judge tier savings on price, not token counts.

### Lessons for the skills

19. **Drop executor tiers when the plan gives complete code**, keeping opus on checkpoint reviews: it held with zero escalations and zero executor-attributable defects.
20. **When tiers drop, the checkpoint review owns test sufficiency.** Brief it to mutate every "reviewer looks at" item; expect it to find the plan's missing tests, not executor errors.
21. **"No new tests: existing tests pin it" is a plan claim to verify, not assume** — the writer should name, per moved behaviour, the test and assert that pins it; behaviour-preserving refactors were where pinning was weakest.
22. **Measure tier choices on price, not tokens**, and record attempts per step alongside escalations — one-attempt-everywhere is the healthy signal, a rising attempt count the early warning before escalations appear.
