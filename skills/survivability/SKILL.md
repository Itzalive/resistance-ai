---
name: survivability
description: Use when implementation is complete and you must prove tests resist realistic faults before finishing the branch
---

# Survivability

## Overview

Survivability is the local gate between “implementation finished” and “safe to finish.”
It proves two things: the tests actually catch faults, and the system degrades safely
under realistic disruption.

## When to Use

- After implementation is complete
- After review if your workflow includes one
- Before `finishing-a-development-branch`
- When the change touched executable logic

## Steady-State Preflight

Before any experiment:

1. name one explicit steady-state verification command
2. name the expected healthy signal for that command
3. name one focused test command for the changed logic

If any item is missing, stop. No experiment runs without a measurable baseline.

## Lane Selection

The chaos lane always runs. The mutation lane runs only where no earlier mutation has
already proved the tests.

Checkpoint reviews in `subagent-driven-development` mutate each "Reviewer looks at"
item on a scratch copy and log it as `CHECKPOINT_REVIEW`. Mutating the same decision
points again is redundant; skipping the lane where no checkpoint mutated is where
survivors were missed. So:

1. List every changed decision point in the branch diff (see the definition in the
   mutation lane below).
2. Map each one to a checkpoint mutation that covered it, from the checkpoint
   reports and their `CHECKPOINT_REVIEW` entries. A decision point counts as covered
   only if that mutation was killed, and the code has not changed since. Any
   decision point changed after the last checkpoint (for example a code-review fix)
   is uncovered.
3. Choose the lane:
   - **`skipped`** — checkpoints mutated every changed decision point. Name the
     checkpoints that covered them in `--reason`.
   - **`uncovered-only`** — some were covered. Run the mutation slate on the
     uncovered decision points only, with the same bounds.
   - **`full`** — run the full slate on the inline fast path, under
     `executing-plans`, on any plan with no checkpoints, and whenever the checkpoint
     reports are missing or don't show killed/survived per item.

Never skip the lane on a claim that checkpoints ran. Skip it only on the reports.

## Mutation Probe Lane

Mutation testing measures test effectiveness, not line coverage.

For a small change, run 3 representative probes:

1. boundary/condition mutation
2. failure-path removal or happy-path bias mutation
3. returned-value or state mutation

For broader changes, add 1 probe per additional meaningful decision point, capped at 5 total.

Treat a meaningful decision point as a modified branch condition, guard clause, or early-return path that can independently change control flow.

Loop for each probe:

1. apply one reversible mutation
2. rerun the same focused test command
3. classify the result as killed or survived
4. restore the original state before the next probe

If any mutant survives, fail the gate and route the work back to implementation hardening and stronger tests.

## Chaos Probe Lane

For local-only changes, run 1 chaos probe minimum.

For dependency-touching changes, run 2 chaos probes minimum, capped at 3 total.

Treat a dependency-touching change as any change that adds, removes, or modifies a call boundary to a network service, subprocess, filesystem path outside the working tree, or other external dependency surface.

Use realistic faults such as:

- 500ms latency
- timeout
- null response
- dependency unavailable

Every chaos probe must include the fault, expected safe degradation behavior, explicit abort/restore steps, and a rerun of the steady-state command.

If a chaos probe causes unsafe degradation or restore cannot complete, fail the gate and route the work back to implementation hardening before finish.

## Review Log Submission

Append a bounded experiment summary to `.review_log.jsonl` with the append CLI described in `skills/shared/review-log-jsonl.md`, using `--skill survivability --phase SURVIVABILITY`.

Do not copy full stdout/stderr, full diffs, or secret-bearing output into the log.

Every entry records the lane and the **first slate**: the result of the first
mutation run, before any test was hardened.

- `--mutation-lane full|uncovered-only|skipped`
- `--first-slate <killed>/<total>` (omit only when the lane was skipped)
- the survivability score in `--reason`: `mutation_killed=<killed>/<total> chaos_passed=<passed>/<total>`

**Survivors mean FAIL, then hardened.** If the first slate has any survivor, log
round 1 with `--verdict FAIL` and one `critical:weak-test:<mutant and location>`
finding per survivor (CRITICAL FRICTION for retrospective ingestion). Harden the
tests, rerun the slate and the chaos lane, then log round 2 with the same
`--first-slate`, the new score, `--verdict PASS` and `--reason` starting
`FAIL -> hardened`. Never log the hardened rerun as round 1, and never log a first
slate with survivors as PASS; the CLI rejects both.

A chaos probe that degrades unsafely is logged the same way: round 1 `FAIL` with a
`real-bug` finding, then the rerun after the fix.

## Quick Reference

1. establish steady state
2. choose the mutation lane from the checkpoint reports
3. run the bounded mutation slate (full or uncovered-only), unless skipped
4. run the bounded chaos slate (always)
5. append the bounded experiment summary with the lane and first slate
6. on survivors: log FAIL, harden, rerun, log PASS as round 2
7. proceed to finish only on PASS

## Red Flags

- single mutation probe offered as “enough”
- undefined “meaningful decision point”
- undefined “dependency-touching” scope
- chaos experiments with no restore path
- logging raw command output into `.review_log.jsonl`
- skipping the mutation lane because "checkpoints ran", without per-item reports
- logging PASS after hardening as if the first slate had been clean

## Integration

- called after implementation/review
- runs before `finishing-a-development-branch`
- hands the survivability score forward to retrospective work
