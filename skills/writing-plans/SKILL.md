---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code; especially when sequencing, failure paths, and execution risk must be made explicit before coding
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

This skill is the shipped default plan-writing rulebook. Repo-root `PLAN_WRITING.md`
is an optional overlay only. Strictly apply repo-root overlays; if they contradict this file, the overlay wins.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by specifying-work-items).

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<work-item-id>-<work-item-name>.md`
- (User preferences for plan location override this default)

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
3. If scope or architecture proof is missing, ask one targeted question or reject the work as spec-incomplete.
4. Push back on unnecessary complexity instead of silently absorbing it into the plan.
5. Split work by dependency order and chunk size, not by convenience.
6. Use RED → GREEN → REFACTOR for every task; for docs-only or config-only work, use exact verification checks instead of invented tests.
7. Run self-review, then the Unified Coherence Check, before offering execution handoff.

---

## Scope Check: Spec simplification and pushback

Before writing tasks, decide whether the approved spec should stay in one plan or be
split into independent plans. Keep related changes in one plan only when they share
the same acceptance surface, verification path, and dependency chain; otherwise shard
them into separate plans before task writing begins.

Resist the urge to solve complexity by writing an increasingly complex plan. If
execution requires edge-case workarounds, non-trivial data-model hacks, or
complex mock setups not defined in the spec, stop and push back on the spec:

> *"The spec requires X, which adds [N tests / a new field / a workaround] to the
> plan. Would it be simpler to [alternative]? That would remove [complexity] from
> the execution."*

Do not silently absorb spec complexity into the plan.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

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

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

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

## Task Structure

For each task, use one execution goal, a concrete file list, and ordered RED → GREEN
→ REFACTOR steps that point back to the hard gates below.

````markdown
### Task N: [single execution goal]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`
- Regenerate: `[checked-in generated artifact if required]`

- Satisfies Spec AC: [List specific Given/When/Then criteria covered]
- **Test retention:** [**Permanent** | **Temporary** — remove before final commit]

- [ ] **Step 1: write RED tests for the happy path AND at least two failure modes.**

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

- [ ] **Step 4: run test to verify it's GREEN**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS


- [ ] **Step 5: regenerate artifacts, rerun exact verification commands, and refactor duplicated wording or structure without weakening gates**

```python
def function(input):
    return expected
```

- [ ] **Step 6: commit the finished slice**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task
- Do not write "preserve existing gates" without naming `### Risk & Confidence Assessment`, `Strict RED / GREEN / REFACTOR`, `Dependency ordering`, `Fail-closed planning contract`, `Unhappy-path-first planning`, and `Unified Coherence Check`.
- Do not write "restore vendor sections" without naming the exact headings.
- Do not write "run the tests" without the exact `pytest` command.

## Remember
- Exact file paths always
- Complete code in every step — if a step changes code, show the code
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits

## Process Flow

```dot
digraph writing-plans {
    "Read spec" -> "Explore context";
    "Explore context" -> "Spec simplification check";
    "Spec simplification check" -> "Write plan";
    "Write plan" -> "Pre-plan verification";
    "Pre-plan verification" -> "Self-Review";
    "Self-Review" -> "Unified Coherence Check" [label="approved"];
    "Unified Coherence Check" -> "Execution Handoff" [label="approved"];
    "Unified Coherence Check" -> "Fix plan" [label="rejected"];
    "Fix plan" -> "Pre-plan verification";
}
```

---

## Tabula Rasa Mandate

Assume your memory of the specification is flawed, hallucinated, or incomplete.
Your first action must be to shell-read the approved spec (for example,
`ls docs/superpowers/specs/` then `cat <file>`). Do not outline execution steps
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
- *Isolated state:* every test must use a unique UUID or fresh transaction to
  prevent state pollution between runs.

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

## Chunking and context protection

No single planned step may touch more than two core files plus their
corresponding tests, unless it is a true atomic refactor that must update all
consumers together to keep the build passing. Break larger features into
verifiable RED / GREEN chunks, and do not advance until the current GREEN step
yields a passing test suite.

---

## Pre-plan verification

Before review, physically execute shell commands to verify:

1. **Existing implementation / state** — verify whether the target file, section,
   feature, or prior plan already exists so the plan refines reality instead of
   blindly recreating it.
2. **Target directories** — `ls` or `tree` planned write paths; add a creation step if missing.
3. **Test runners** — confirm the test commands against `package.json`, `pyproject.toml`, or equivalent.
4. **Method / class / return shapes** — `grep` the names and signatures the plan depends on.
5. **Config templates** — if new env/config values appear, update the relevant example/template file.
6. **MCP inputSchema args** — verify tool argument names against the real schema.
7. **Naming collisions** — confirm no existing file already serves the planned purpose.

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
the Unified Coherence Check:

1. **Placeholder scan** — verify no `TODO`, `TBD`, or hand-wavy instructions.
2. **RED / GREEN integrity** — confirm test-writing steps and implementation steps
   are separate and in the correct order.
3. **Dependency order** — verify the plan flows bottom-up from data to consumers.
4. **Chunking check** — confirm no step exceeds the chunking rule.
5. **Reality check** — re-run the `Pre-plan verification` shell verifications for any steps you
   changed during self-review.
6. **Unhappy-path coverage** — confirm at least two failure-mode tests per task.
7. **Runbook completeness** — every manual infrastructure step has an explicit runbook entry.
8. **Test retention audit** — confirm every new test is marked Permanent or Temporary, and no Temporary test survives the final REFACTOR step unless it protects a deliberate contract.
9. **Convention sync**: if planned work changes a repository-wide convention, include updates to contributor instruction files (for example 
`.github/copilot-instructions.md`, `AGENTS.md`, and `CLAUDE.md`) in the same plan.


Fix issues inline. No need to re-review after fixing — just correct and move on.
If a spec requirement has no corresponding task, add the task.

After applying self-review fixes, re-run any affected verification from `Pre-plan verification` before dispatching the audit. If a fix changes command changes, file paths, or artifact names, the relevant shell checks must be refreshed first.

---

## Unified Coherence Check

**CRITICAL:** Before marking work as approved, and only after the Plan self-review
plus any resulting fixes are complete, perform a double-blind alignment check using
a cross-model sub-agent (Rubber Duck).

**Model selection rule:**
- Orchestrator is **claude-\*** → sub-agent must be **gpt-5.4**.
- Orchestrator is **gpt-\*** → sub-agent must be **claude-sonnet-4.6**.

Build the reviewer input bundle using `unified-coherence-check-evidence.md` in this
directory. That support file defines the exact evidence to provide, including the
existing-state check, shell verification output, Tabula Rasa proof, review-log chain,
and opposite-model proof.

The sub-agent must validate:
- **Alignment A (Spec vs. Work Item):** Does the spec satisfy every functional
  requirement, security guardrail, and constraint in the original work item?
- **Alignment B (Plan vs. Spec):** Does the plan faithfully implement the spec
  without omitting edge cases or simplifying complex logic?
- **Alignment C (Context vs. Reality):** Do all file paths, method signatures,
  and class names in the plan match the physical repository state (verified by
  `grep` / `ls` commands and the provided shell evidence)?

**Decision logic:** Do not proceed to execution until `[APPROVED]` is reached.
- `[APPROVED - READY FOR EXECUTION]` — full alignment across all vectors.
- `[REJECTED - PLAN DRIFT]` — plan deviates from the spec's logic or skips
  complex requirements.
- `[REJECTED - SPEC INCOMPLETE]` — spec fails to deliver the original work item's
  requirements.

Record the result and raw reasons in `.review_log.jsonl` at the repo root using
`../review-log-jsonl.md`. If rejected, fix discrepancies, re-run verifications
and the Plan self-review, then restart the Unified Coherence Check.



---

## Execution Handoff

After the plan passes self-review and the final approval gate, offer:

1. **Subagent-Driven (recommended)** — use `subagent-driven-development`
2. **Inline Execution** — use `executing-plans`

Neither path may skip Tabula Rasa, RED/GREEN/REFACTOR, or the final approval gate.

---

## Common rationalizations

The following are recognised failure modes. Encountering them in your own reasoning
is a **red flag** that you are rationalising toward a shortcut.

| Rationalisation | Red flag | Correct action |
|---|---|---|
| "The spec is obviously simple, I don't need to ingest it" | Tabula Rasa skipped | Shell-read the spec first, always |
| "This is a small change, chunking doesn't apply" | Chunking rule bypassed | Still apply the two-file limit; atomic refactors are the only exception |
| "The reviewer says don't overcomplicate failure cases" | Unhappy-path pressure | Reject; failure cases are real engineering, not complexity |
| "I'll add error handling later" | Fail-closed planning violated | Every external-dependency step must have a failure branch now |
| "I remember the method signature from earlier in the session" | Pre-plan verification skipped | Shell-verify the signature before committing it to the plan |
| "The spec covers it implicitly" | Invisible runbook step | Every manual step must be made explicit in the runbook |
| "I'll just guess the unknown variable and note it" | Unknown variable unresolved | Name it in the Risk Assessment and ask targeted questions before planning |
| "This temporary test is still useful, so I'll keep it" | REFACTOR stage bypassed | Delete or replace implementation-shape tests before completion unless they protect a deliberate contract |

**Red flags in your own output:**
- You started writing tasks before running `cat` on the spec file.
- The plan has no `### Risk & Confidence Assessment` block.
- Every task step describes the happy path only.
- You wrote "handle errors appropriately" without specifying what that means.
- A new test asserts inheritance, helper existence, or call ordering without a `Test retention` note explaining why it survives REFACTOR.
