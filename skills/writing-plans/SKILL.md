---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code; especially when sequencing, failure paths, and execution risk must be made explicit before coding
---

# Writing Plans

## Overview

Write implementation plans that a fresh executor with no context for our codebase can carry out task by task. Document everything they need: which files to touch, which callers move with each change, the tests, the commands, and what the checkpoint reviewer must prove. DRY. YAGNI. TDD. Every commit green.

Assume the executor is a skilled developer who knows almost nothing about our toolset or problem domain, and does not know good test design very well. Cheaper executors transcribe faithfully but do not notice what the plan left out, so the plan writer owns completeness: the caller sweep, the tests that pin each behaviour, and every decision.

The plan format is what `subagent-driven-development` reads: per-task tier tags pick the executor, the caller table and per-task callers keep each commit green, and the "Reviewer looks at" items brief the checkpoint reviewer's mutations.

This skill is the shipped default plan-writing rulebook. Repo-root `PLAN_WRITING.md`
is an optional overlay only. Strictly apply repo-root overlays; if they contradict this file, the overlay wins.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by specifying-work-items).

**Save plans to:** `<plans-dir>/YYYY-MM-DD-<work-item-id>-<work-item-name>.md`
- `<plans-dir>` defaults to `docs/plans`. A plan directory named in repo-root `PLAN_WRITING.md`, or a user preference, overrides it.
- Specs live in `<specs-dir>`, which defaults to `docs/specs`. A spec directory named in a repo-root overlay, or a user preference, overrides it.

---

## When to Use

Use this skill when:

- you have an approved spec or requirements for a multi-step task
- sequencing, dependency ordering, failure paths, or execution risk must be explicit before coding
- the work spans multiple files, layers, or manual steps and a fresh execution agent could guess wrong
- you need a plan that can be handed to another agent with minimal repository context

## When NOT to Use

Do not use this skill when:

- the task is a trivial one-file wording or typo fix that only needs a lightweight inline outline
- the request still needs design, scope, or architecture approval first (use `specifying-work-items`)
- there is no meaningful sequencing, dependency, or failure-path risk to make explicit
- the user wants direct implementation rather than a stored plan document

## Checklist

1. Ingest the approved spec before writing tasks.
2. Verify current repository reality, including whether the target section, file, feature, or prior plan already exists.
3. List open decisions. Anything the spec does not settle goes back to the spec before tasks are written.
4. Count entry paths and apply the sizing rule; propose a split before writing tasks if it fails.
5. Run the caller and test sweep and fill in its table.
6. Write tasks in dependency order, each with its tier, the callers that move with it, its "Reviewer looks at" items and, where it adds no tests, what pins it.
7. Use RED → GREEN → REFACTOR for every task; for docs-only or config-only work, use exact verification checks instead of invented tests.
8. Place checkpoints, add the trust-boundary table when it applies, then run self-review and the alignment check before offering execution handoff.

---

## Scope Check: Spec simplification and pushback

Before writing tasks, decide whether the approved spec should stay in one plan or be
split into independent plans. Keep related changes in one plan only when they share
the same acceptance surface, verification path, and dependency chain; otherwise shard
them into separate plans before task writing begins. The sizing rule below decides
when a plan is too large.

Resist the urge to solve complexity by writing an increasingly complex plan. If
execution requires edge-case workarounds, non-trivial data-model hacks, or
complex mock setups not defined in the spec, stop and push back on the spec:

> *"The spec requires X, which adds [N tests / a new field / a workaround] to the
> plan. Would it be simpler to [alternative]? That would remove [complexity] from
> the execution."*

Do not silently absorb spec complexity into the plan.

## Open decisions go back to the spec

A plan translates decisions; it does not make them. Before writing tasks, list every
behaviour question the spec leaves open: defaults, what an empty value means, id
composition, ordering and concurrency rules, what happens at each threshold. For each
one, name the concrete gates or thresholds it crosses and what happens at each.

- If the list is empty, say so in the plan header (`**Open decisions:** none`).
- If it is not empty, stop. Take the questions to the owner with a recommendation,
  then amend the spec (see `specifying-work-items`) so the spec stays the single
  source of truth. Write tasks only after the amendment is approved.
- Where the spec has a decision register, cite decision ids in the tasks that apply
  them instead of restating the decision.
- A decision that surfaces during execution is a spec gap too: the executor stops,
  and the coordinator takes it back to the spec.

Decisions settled in chat and recorded only in the plan get lost, and each one found
late costs a plan rewrite and another review round.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Sizing by rule

Size the plan by rule, never by a number. A size number becomes a target: writers
compress edits to fit a line count and pack tasks to fit a task count, and packed
tasks hide the cross-task interactions that small tasks surface.

**The per-task rule:**
- one behaviour per task;
- at most two core files plus their tests, unless the task is a true atomic change
  that must update every caller together to keep the build green (say so in the task).

**The per-plan rule:**
- at most two entry paths per plan. An entry path is a distinct way the behaviour is
  reached (a request handler, a CLI command, a scheduled job, a tool call). Count the
  entry paths the spec touches before writing any task.

Let the task count fall out of the per-task rule. If the plan then touches more than
two entry paths, or the task count runs well past about eight, propose a split along
the spec's own seams before writing tasks (for example one plan with no
trust-boundary change and one carrying all of it).

Report the plan's line count and task count in the header. The line count is reported,
never a target: never shorten, summarise or omit an edit to save space.

## Caller and test sweep

The plan writer owns the caller sweep; the alignment reviewer only checks it. For
every changed signature, return shape, default, fixture or behaviour, search for
every caller, test, fake, mock and assert across **all** source directories, not only
the main package: `scripts`, `evals`, `tools`, `migrations`, test fixtures and
conftest files, docs that embed runnable examples, and any other directory with code
in it. List the directories you searched and the commands you ran in the
verification evidence.

Record the result in the plan's **Caller and test sweep** table:

```markdown
## Caller and test sweep

Searched: `src/`, `tests/`, `scripts/`, `evals/` with `rg -n "load_record\(" ...`

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `load_record(path)` → `load_record(path, *, strict)` | `src/app/reader.py:88` | caller | 2 | `load_record(path, strict=True)` |
| same | `tests/fakes.py:41` `FakeStore.load_record` | fake | 2 | `def load_record(self, path, *, strict=False):` |
| same | `scripts/backfill.py:17` | caller | 2 | `load_record(p, strict=False)` |
| `Record.default_ttl` 0 → None | `tests/conftest.py:12` fixture `record` | fixture default | 3 | `Record(ttl=0)` to keep the old meaning |
```

Rules:
- One row per site. "Replacement rules" ("update every caller to pass `strict`")
  are not edits; write the literal edit for each row.
- A fixture or default whose meaning changes is a row, even if no call changes.
- Every row names the task that makes its edit, and that task's
  **Callers that move with this task** lists it.
- If the sweep finds nothing, keep the table with one line saying what was searched
  and that nothing was found.

## Every commit green

Each task ends in a commit with the full affected suite passing. For that:

- each task lists the callers that move with it (rows from the sweep table), and its
  verification step runs those callers' tests, not only its own;
- no task consumes something a later task adds; reorder or merge tasks instead;
- a task that changes a shared signature moves every caller in the same commit.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test(s)" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test(s) pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Spec:** [path] — decisions applied: [decision ids, or "none"]

**Open decisions:** none

**Size:** [N] tasks, [M] entry paths ([names]), [L] lines (reported, not a target)

**Trust boundary:** [changed — see Trust-boundary table | unchanged]

### Risk & Confidence Assessment

**Confidence:** [N]% — [one-line rationale]

**Complexity Risk:** [Low | Medium | High] — [driving variable, e.g. "three Cosmos
partition-key changes must land atomically"]

**Environmental Risk:** [Low | Medium | High] — [driving variable, e.g. "AWS
STS token exchange untested in this tenant"]

**Main failure modes:** [briefly name the execution-breaking failures]

**Unknown variables** (only when confidence < 95%):
- [explicit list of what is unverified or ambiguous]

---
```

Rules:
- Name the main failure modes that are most likely to break execution.
- Confidence below 95 % **must** name every unknown variable explicitly.
- Medium or High risk ratings **must** name the single driving variable.
- If both risk ratings are Low, justify why the work is mechanically
  straightforward (for example, a single-file local edit with no branching or
  external calls), not merely "simple".
- A plan with unresolved unknowns is a guess. Ask targeted questions or state the
  assumption explicitly before proceeding.

After the header come, in order: the **Caller and test sweep** table, the
**Trust-boundary table** (when required), the **Checkpoints** table, then the tasks.

## Task Structure

For each task, use one execution goal, a concrete file list, its tier, the callers
that move with it, its "Reviewer looks at" items, and ordered RED → GREEN → REFACTOR
steps that point back to the hard gates below.

````markdown
### Task N: [single execution goal]

**Tier:** fast | standard | strong — [one-line reason]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`
- Regenerate: `[checked-in generated artifact if required]`

**Callers that move with this task:** [sweep-table rows, e.g. `scripts/backfill.py:17`, `tests/fakes.py:41`; or "none"]

**Reviewer looks at:**
- [decision point] — mutation: [the fault to inject] — killed by: `tests/path/test.py::test_name`
- [decision point] — mutation: [...] — killed by: [...]

**Pinned by:** [only when this task adds no new test for a moved or changed behaviour: per behaviour, the existing test and the assert that pins it, e.g. `tests/test_writer.py::test_retry_stops_at_three` asserts `attempts == 3`]

- Satisfies Spec AC: [List specific Given/When/Then criteria covered]
- Decisions applied: [decision ids from the spec, or "none"]
- **Test retention:** [**Permanent** | **Temporary** — remove before final commit]

- [ ] **Step 1: write RED tests for the happy path, the failure modes and each threshold.**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: run focused RED verification command**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: write minimal implementation for GREEN**

```python
def function(input):
    return expected
```

- [ ] **Step 4: run the task's tests and the tests of every caller that moved with it**

Run: `pytest tests/path/test.py tests/path/test_caller.py -v`
Expected: PASS

- [ ] **Step 5: regenerate artifacts, rerun exact verification commands, and refactor duplicated wording or structure without weakening gates**

- [ ] **Step 6: commit the finished slice**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

### Tier tags

Each task names the cheapest executor tier that can do it safely. Tiers are
model-neutral; a repo-root overlay maps them to models (on Claude: fast = Haiku,
standard = Sonnet, strong = Opus).

- **fast** — mechanical work where the plan gives complete code and exact commands.
- **standard** — the default; breadth work and integration across a few files.
- **strong** — work where a mistake is costly and needs judgement: trust boundaries,
  conditional writes, idempotency, concurrency.

Drop one tier where the plan gives complete code for the task (strong → standard,
except for genuine trust-boundary or conditional-write judgement; standard → fast
where every edit is written out in full). The checkpoint reviewer, not the executor
tier, owns test sufficiency.

### Reviewer looks at

List the decision points in the task that a weak test would let slip: each boundary,
branch, conditional write, default, ordering or trust check. For each, name a
mutation (the fault to inject, such as `>=` to `>`, a dropped filter, a skipped
write) and the test that should kill it. The checkpoint reviewer runs one mutation per
item on a scratch copy, so an item without a killing test is a plan hole: add the
test now.

### Pinned by

"No new tests: existing tests pin it" is a claim to verify, not to assume. When a
task adds no new test for a behaviour it moves or changes, name, per behaviour, the
test and the assert that pins it, and confirm the assert would fail if the behaviour
changed. Behaviour-preserving refactors are where pinning is weakest; if no assert
pins a behaviour, write one in the RED step.

### Code detail by tier (experiment)

- **Always in full:** every RED test, every literal edit in the caller table, and
  every exact command.
- **fast tasks:** complete code for every step.
- **standard and strong tasks:** interfaces (signatures, types, return shapes), the
  RED tests and the caller-table rows are enough; the GREEN implementation may be
  described against those interfaces.

This is an experiment. Record which tasks got interface-only detail, and judge it at
plan end on executor-attributable checkpoint findings and on plan tokens. If
executor-attributable findings rise, give those tiers full code again.

## Checkpoints

Place a checkpoint review every three to five tasks: after cross-cutting changes,
around strong-tier tasks, and at the end of each subsystem. The coordinator runs
them as described in `subagent-driven-development`.

```markdown
## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | Task 1 items 1–2, Task 3 item 1; full suite (Task 2 is cross-cutting) |
| C2 | 6 | 4–6 | Task 5 items 1–3 (strong); trust-boundary rows 1–2 |
```

Every "Reviewer looks at" item belongs to exactly one checkpoint. Say whether the
checkpoint runs the full suite (only when its tasks were cross-cutting) or the tasks'
focused tests.

## Trust-boundary table

**Required when untrusted text can reach a model or a parser**, including text that
was stored earlier and is read back later. List every reader of model-facing text and
every producer into a model-facing block or parser input, what text each one
receives, and the task and test that prove the trust rule holds there.

```markdown
## Trust-boundary table

| Reader or producer | Model-facing block or parser | Text it receives | Untrusted source | Task | Proving test |
|---|---|---|---|---|---|
| `render_history()` | system prompt "history" block | stored message bodies | end users | 4 | `tests/test_render.py::test_history_escapes_tags` |
| `parse_handles()` | handle parser | model output | model, after reading user text | 5 | `tests/test_handles.py::test_unknown_handle_rejected` |
```

If the spec names a trust rule but not every place it applies, that is a spec gap:
take it back to the spec. When the plan changes no trust boundary, say so in the
header and omit the table.

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- "Update all callers" without a row per caller in the sweep table
- "Existing tests cover it" without naming the test and the assert
- Steps that describe what to do without showing how (code blocks required for RED tests, literal edits and fast-tier code)
- References to types, functions, or methods not defined in any task
- Do not write "preserve existing gates" without naming `### Risk & Confidence Assessment`, `Strict RED / GREEN / REFACTOR`, `Dependency ordering`, `Fail-closed planning contract`, `Unhappy-path-first planning`, and `Alignment check`.
- Do not write "restore vendor sections" without naming the exact headings.
- Do not write "run the tests" without the exact `pytest` command.

## Remember
- Exact file paths always
- Every RED test, literal edit and command in full
- A row for every caller, test, fake, mock and assert of a changed thing
- Exact commands with expected output
- DRY, YAGNI, TDD, every commit green

## Process Flow

```dot
digraph writing-plans {
    "Read spec" -> "Explore context";
    "Explore context" -> "Open decisions?";
    "Open decisions?" -> "Amend spec with owner" [label="yes"];
    "Amend spec with owner" -> "Read spec";
    "Open decisions?" -> "Size by rule" [label="none"];
    "Size by rule" -> "Propose split" [label="fails"];
    "Size by rule" -> "Caller and test sweep" [label="passes"];
    "Caller and test sweep" -> "Write tasks and checkpoints";
    "Write tasks and checkpoints" -> "Pre-plan verification";
    "Pre-plan verification" -> "Self-Review";
    "Self-Review" -> "Alignment check" [label="approved"];
    "Alignment check" -> "Execution Handoff" [label="approved"];
    "Alignment check" -> "Fix plan" [label="rejected"];
    "Fix plan" -> "Pre-plan verification";
}
```

---

## Tabula Rasa Mandate

Assume your memory of the specification is flawed, hallucinated, or incomplete.
Your first action must be to shell-read the approved spec (for example,
`ls <specs-dir>/` then `cat <file>`). Do not outline execution steps
until the spec is physically ingested. A plan translates a spec mechanically; it
is not a second brainstorming phase.

---


## Strict RED / GREEN / REFACTOR

Resistance Engine relies on Test-Driven Development. Your plan must structurally enforce
this. Never bundle test creation and implementation into the same step.

- **Step A (RED):** A discrete, standalone step that writes *failing* unit and
  integration tests based on the spec's Acceptance Criteria. For refactors,
  explicitly classify each new test as either **Permanent** (behaviour-facing,
  must remain) or **Temporary** (implementation-shape guard used only to drive
  the change).
- **Step B (GREEN):** Only after the RED step is defined, a step implementing the
  minimum code to make those tests pass.
- **Step C (REFACTOR):** Steps to clean up the code and update any legacy tests
  broken by the new implementation. Delete temporary tests, or replace them with
  permanent behaviour-facing tests, and keep only behaviour-facing tests unless
  an implementation detail is itself a deliberate long-term contract.

**Docs-only / config-only branch:**
- For documentation-only or config-only plans, RED and GREEN may be exact verification
  checks rather than new automated product tests.
- **RED:** prove the current state is absent, incorrect, or misleading with exact
  commands such as `grep`, `sed -n`, config readback, or `--help`.
- **GREEN:** make the smallest edit, then rerun the same checks against the real
  metadata, config surface, or rendered file.
- **REFACTOR:** tighten wording or structure and rerun the same checks. Do not invent
  permanent regression tests unless that docs/config surface is already tested in-repo
  or the spec explicitly requires it.

**Test rigour rules:**
- *No smoke tests:* assertions must check specific data values, not merely
  "is not null" or "status 200".
- *Boundary verification:* every plan must include at least one negative test
  (expected failure) to prove the logic catches errors.
- *Thresholds:* test every threshold at, below and above it.
- *Real entry points:* test composed behaviour through the real entry point, not
  only through unit-tested helpers.
- *Isolated state:* every test must use a unique UUID or fresh transaction to
  prevent state pollution between runs.

**Docs in code:** docstrings and comments written by the plan describe the code in
the present tense; they do not narrate the change history.

---

## Dependency ordering

1. **Data layer first** — migrations, schema changes, raw data models.
2. **Logic layer second** — internal services, utilities, core business logic.
3. **Transport / API / tool layer third** — controllers, routes, MCP tool definitions.
4. **UI / consumer layer last** — if applicable.

Dependencies come before consumers. If Step 4 needs a database field, create it
in Step 1. Never plan a consumer before its dependency exists.

---

## Manual steps and runbooks

LLMs cannot execute manual web-UI tasks (clicking through a console, generating an
API key, configuring a webhook).

**The Runbook Rule:** If the spec requires *any* manual configuration, infrastructure
provisioning, or third-party credential generation, the plan must include a dedicated
step to document those instructions in the repository runbook
(e.g., `runbooks/infrastructure-setup.md`).

If the runbook step requires CLI commands (e.g., `aws s3 mb` or `terraform apply`),
the plan must instruct the agent to verify the syntax via `--help` or a dry-run
before committing those commands to the runbook.

**Zero invisible steps:** Never leave manual human steps implied. The plan must
instruct the execution agent to write out the exact, step-by-step instructions the
human must follow before the code can be safely deployed or tested.

---

## Pre-plan verification

Before review, physically execute shell commands to verify:

1. **Existing implementation / state** — verify whether the target file, section,
   feature, or prior plan already exists so the plan refines reality instead of
   blindly recreating it.
2. **Target directories** — `ls` or `tree` planned write paths; add a creation step if missing.
3. **Test runners** — confirm the test commands against `package.json`, `pyproject.toml`, or equivalent.
4. **Method / class / return shapes** — `grep` the names and signatures the plan depends on.
5. **Caller sweep** — the search commands and directory list behind the sweep table,
   covering every source directory.
6. **Pinning claims** — for each **Pinned by** entry, show the named assert exists.
7. **Config templates** — if new env/config values appear, update the relevant example/template file.
8. **MCP inputSchema args** — verify tool argument names against the real schema.
9. **Naming collisions** — confirm no existing file already serves the planned purpose.

---

## Fail-closed planning contract

If the plan cannot prove user intent or scope, ask one specific clarifying question
before writing steps.

If architecture proof is missing from the spec or verified repository context,
reject the work as `[REJECTED - SPEC INCOMPLETE]` instead of guessing.

Do not invent timeouts, retries, contracts, or fallback behavior unless they are
traceable to the approved spec or the verified repository context.

---

## Unhappy-path-first planning

**Happy-path-only planning is a failure mode.**

For every significant task in the plan, enumerate the failure modes *before*
writing the happy-path implementation steps:

- What happens if the input is malformed?
- What happens if the network call times out or returns 5xx?
- What happens if a required config value is missing?
- What happens if the operation partially succeeds?

Write tests for at least two of these failure modes per task. Then write the
happy-path implementation.


---

## Self-Review

After pre-plan verification, run this checklist yourself before dispatching
the alignment check:

1. **Placeholder scan** — verify no `TODO`, `TBD`, or hand-wavy instructions.
2. **RED / GREEN integrity** — confirm test-writing steps and implementation steps
   are separate and in the correct order.
3. **Dependency order** — verify the plan flows bottom-up from data to consumers.
4. **Per-task rule** — each task is one behaviour and touches at most two core files
   plus tests (or says why it is an atomic change); the plan touches at most two
   entry paths.
5. **Caller sweep** — every changed thing has a row per site, every row names a task,
   and every task lists the rows that move with it.
6. **Every commit green** — no task consumes something a later task adds.
7. **Tier, reviewer items and pinning** — every task has a tier, at least one
   "Reviewer looks at" item with a killing test, and a **Pinned by** entry wherever it
   adds no test for a moved behaviour; every item is in a checkpoint.
8. **Open decisions** — none left in the plan; decisions cite the spec.
9. **Trust boundary** — the table is present whenever untrusted text reaches a model or parser.
10. **Reality check** — re-run the `Pre-plan verification` shell verifications for any steps you
    changed during self-review.
11. **Unhappy-path coverage** — confirm at least two failure-mode tests per task.
12. **Runbook completeness** — every manual infrastructure step has an explicit runbook entry.
13. **Test retention audit** — confirm every new test is marked Permanent or Temporary, and no Temporary test survives the final REFACTOR step unless it protects a deliberate contract.
14. **Convention sync** — if planned work changes a repository-wide convention, include updates to contributor instruction files (for example
`.github/copilot-instructions.md`, `AGENTS.md`, and `CLAUDE.md`) in the same plan.

Record the result with the append CLI (`--phase PLAN_SELF_REVIEW`, `--independence self`).

Fix issues inline. No need to re-review after fixing — just correct and move on.
If a spec requirement has no corresponding task, add the task.

After applying self-review fixes, re-run any affected verification from `Pre-plan verification` before dispatching the alignment check. If a fix changes commands, file paths, or artifact names, the relevant shell checks must be refreshed first.

---

## Alignment check

**CRITICAL:** Before marking the plan approved, and only after self-review and its
fixes are complete, have an independent reviewer check the plan against the spec and
the repository. The reviewer checks **completeness and the per-task rule**: that
nothing the spec requires is missing, that every caller is in the sweep, and that
each task holds one behaviour. It does not judge length.

**Reviewer independence rule:**
- **Required:** a fresh-context sub-agent that did not write or fix the plan. It gets
  only the evidence bundle below, never this conversation.
- **Preferred:** a different model family, when the harness offers one. If a repo-root
  overlay names the reviewer model, use that model. This skill names none.
- Log `reviewer_model` and `independence` (`fresh-context` or `cross-family`). A
  same-family fresh-context review is compliant, not a substitute.
- Round 2 and later go back to the same reviewer with the plan diff. Start a new
  reviewer only after a rewrite of the plan.

Build the reviewer input bundle using `alignment-check-evidence.md` in this
directory, and dispatch the reviewer with `plan-document-reviewer-prompt.md`.

The reviewer must confirm:
- **Completeness:** every spec requirement and acceptance criterion maps to a task;
  the spec still meets the work item.
- **Callers:** the sweep table covers every caller, test, fake, mock and assert of
  each changed thing across all source directories, with literal edits; every commit
  stays green.
- **Per-task rule:** each task holds one behaviour and at most two core files plus
  tests (or is a stated atomic change); the plan touches at most two entry paths.
- **Execution-model fields:** tiers fit the tier rules; every "Reviewer looks at"
  item has a mutation and a killing test and sits in a checkpoint; every **Pinned by**
  names a real assert.
- **Reality:** file paths, signatures and commands match the repository evidence.
- **Decisions and trust:** no decision is made in the plan; the trust-boundary table
  is present and complete when it applies.

**Decision logic:** Do not proceed to execution until `[APPROVED]` is reached.
- `[APPROVED - READY FOR EXECUTION]` — complete, and every task meets the per-task rule.
- `[REJECTED - PLAN DRIFT]` — the plan misses or contradicts something the spec
  requires, misses callers, or breaks the per-task rule.
- `[REJECTED - SPEC INCOMPLETE]` — the spec fails the work item or leaves a decision open.

Record the result with the append CLI described in `../shared/review-log-jsonl.md`:
`--skill writing-plans --phase PLAN_REVIEW`, verdict `APPROVED` or `REJECTED`, the round
number, the reviewer model and its `--independence`. Put the reviewer's status line in
`--reason` and log each gate failure as a `--finding` (usually `plan-hole`,
`spec-hole` or `missed-caller`). If rejected, fix discrepancies, re-run verifications
and the Plan self-review, then return to the same reviewer.

---

## Execution Handoff

After the plan passes self-review and the alignment check, offer:

1. **Subagent-Driven (recommended)** — use `subagent-driven-development`: tiered
   executors per task and checkpoint reviews from the plan's **Checkpoints** table.
   That skill also defines the inline fast path for small plans.
2. **Separate session** — use `executing-plans`

Neither path may skip Tabula Rasa, RED/GREEN/REFACTOR, or the alignment check.

---

## Common rationalizations

The following are recognised failure modes. Encountering them in your own reasoning
is a **red flag** that you are rationalising toward a shortcut.

| Rationalisation | Red flag | Correct action |
|---|---|---|
| "The spec is obviously simple, I don't need to ingest it" | Tabula Rasa skipped | Shell-read the spec first, always |
| "This is a small change, the per-task rule doesn't apply" | Sizing rule bypassed | Still one behaviour and two core files per task; atomic changes are the only exception |
| "The plan is getting long, I'll summarise these edits" | Writing to a size target | Write every edit in full; report the line count, never target it |
| "I'll fit this into fewer tasks" | Packing tasks to a count | Let the count fall out of the per-task rule; propose a split if it runs long |
| "I grepped the package, that's every caller" | Sweep too narrow | Search every source directory, scripts and evals included |
| "Update every caller to pass the new argument" | Replacement rule | One sweep-table row and literal edit per site |
| "Existing tests already pin this" | Unverified pinning claim | Name the test and the assert, per behaviour, or write one |
| "The spec doesn't say, I'll pick a sensible default" | Decision made in the plan | Take it back to the spec as an amendment |
| "The reviewer says don't overcomplicate failure cases" | Unhappy-path pressure | Reject; failure cases are real engineering, not complexity |
| "I'll add error handling later" | Fail-closed planning violated | Every external-dependency step must have a failure branch now |
| "I remember the method signature from earlier in the session" | Pre-plan verification skipped | Shell-verify the signature before committing it to the plan |
| "The spec covers it implicitly" | Invisible runbook step | Every manual step must be made explicit in the runbook |
| "I'll just guess the unknown variable and note it" | Unknown variable unresolved | Name it in the Risk Assessment and ask targeted questions before planning |
| "This temporary test is still useful, so I'll keep it" | REFACTOR stage bypassed | Delete or replace implementation-shape tests before completion unless they protect a deliberate contract |

**Red flags in your own output:**
- You started writing tasks before running `cat` on the spec file.
- The plan has no `### Risk & Confidence Assessment` block.
- The plan has no **Caller and test sweep** table, or a task has no tier.
- A task has no "Reviewer looks at" item, or an item has no killing test.
- Every task step describes the happy path only.
- You wrote "handle errors appropriately" without specifying what that means.
- A new test asserts inheritance, helper existence, or call ordering without a `Test retention` note explaining why it survives REFACTOR.
