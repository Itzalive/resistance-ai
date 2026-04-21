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

- After implementation and review are complete
- Before `finishing-a-development-branch`
- When AGENTS Phase 4 applies and the change touched executable logic

## Steady-State Preflight

Before any experiment:

1. name one explicit steady-state verification command
2. name the expected healthy signal for that command
3. name one focused test command for the changed logic

If any item is missing, stop. No experiment runs without a measurable baseline.

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

Append a bounded experiment summary to `.review_log.jsonl` using the generic append template from `skills/review-log-jsonl.md`.

Do not copy full stdout/stderr, full diffs, or secret-bearing output into the log.

Record the survivability score as:

- `mutation_killed=<killed>/<total>`
- `chaos_passed=<passed>/<total>`
- overall result: `PASS` or `FAIL`

If any mutant survives, log it as CRITICAL FRICTION for retrospective ingestion.

## Quick Reference

1. establish steady state
2. run the bounded mutation slate
3. run the bounded chaos slate
4. append the bounded experiment summary
5. proceed to finish only on PASS

## Red Flags

- single mutation probe offered as “enough”
- undefined “meaningful decision point”
- undefined “dependency-touching” scope
- chaos experiments with no restore path
- logging raw command output into `.review_log.jsonl`

## Integration

- called after implementation/review
- runs before `finishing-a-development-branch`
- hands the survivability score forward to retrospective work
