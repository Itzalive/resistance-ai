## Resistance engine survivability skill

**Date:** 2026-04-20
**Status:** Drafted for review
**Work item:** #5
**Parent work item:** #4

---

## Problem

`AGENTS.md` carried an inline survivability phase template, but the local skill
catalog did not expose a standalone `survivability` skill that could replace that
template cleanly.

Today, the local workflow jumps from completed implementation/review straight to branch
finishing:

- `skills/executing-plans/SKILL.md` hands from finished task execution to
  `finishing-a-development-branch`
- `skills/subagent-driven-development/SKILL.md` hands from final review to
  `finishing-a-development-branch`

That leaves the Phase 4 "Gauntlet" as project prose rather than a first-class local
catalog artifact. The result is an important local-only gate that is easy to skip,
hard to audit, and duplicated between project prose and workflow behavior.

---

## Goals

- Add a standalone local `survivability` skill as a first-class peer in the local
  catalog
- Preserve the survivability phase as a gate, not just advisory prose
- Preserve the existing mutation, chaos, and review-log contract in the standalone
  skill
- Insert survivability into the real execution-to-finish workflow handoff
- Keep the implementation tool-agnostic and compatible with the repo's current
  dependency set
- Feed survivability results into later retrospective work instead of treating them
  as ephemeral session observations

## Non-goals

- No retrospective skill work in this shard; that belongs to issue #6
- No bootstrap compatibility work in this shard; that belongs to issue #7
- No new mutation-testing or chaos-engineering dependency in this shard
- No production-only chaos platform requirement
- No long-term duplication of survivability guidance between `AGENTS.md` and the
  standalone skill; once the skill exists, it should own that contract

---

## Assumptions surface

| Assumption | Status | Evidence / note |
| --- | --- | --- |
| The repo had a local-only survivability phase template at design time | **VERIFIED** | `AGENTS.md:55-71` defined Phase 4, including mutation testing, chaos injection, and review-log submission, before this branch removed the inline template |
| Survivability results are expected to flow into retrospective work | **VERIFIED** | `AGENTS.md:70-71` recorded a survivability score for Phase 6 and logged survived mutations as critical friction before the inline template was replaced by the skill |
| The repo already has a structured append-only review log | **VERIFIED** | `.review_log.jsonl` exists at the repo root; `skills/review-log-jsonl.md:1-97` defines the contract |
| Local-only skills may exist as first-class peers in the local catalog | **VERIFIED** | `docs/superpowers/specs/2026-04-15-resistance-engine-catalog-retarget-design.md:140-156` allows local-only skills beside imported ones and expects them to consult local project guidance |
| No local `survivability` skill exists yet | **VERIFIED** | `skills/` currently has no `survivability/` directory |
| Older lifecycle mapping treated survivability as a gate rather than a skill | **VERIFIED** | `docs/superpowers/specs/2026-04-14-superpowers-overlay-lifecycle-design.md:143-165` models `survivability` as a gate owned by controller/project rules |
| A standalone local skill is still valid in the retargeted architecture | **VERIFIED** | User-approved design choice for issue #5: the skill is the local-catalog expression of the gate rather than a semantic change to the gate itself |
| Dedicated mutation or chaos tooling is already installed | **VERIFIED FALSE** | `pyproject.toml` only includes `pytest` in dev dependencies; `package.json` is metadata-only |

**Blocking constraints**

- No steady-state verification command means no survivability run.
- No reversible restore path means no mutation or chaos probe.
- No new mutation/chaos dependency may be required by this spec.
- No production-only chaos requirement may be introduced.
- No full stdout/stderr, full diffs, or secret-bearing output may be appended to
  `.review_log.jsonl`.

---

## Shard evaluation

This work must remain separate from:

1. the retrospective phase (`#6`)
2. the bootstrap compatibility gap (`#7`)

The three slices have different acceptance surfaces, different integration points, and
different verification paths. A combined spec would conflate a workflow gate skill, a
post-implementation learning skill, and a bootstrap naming/compatibility decision.

---

## Approach

Implement survivability as a **standalone local gate skill** that runs after
implementation/review completes and before branch-finishing begins.

This preserves the older lifecycle meaning: survivability remains a gate. The local
catalog simply gains a dedicated skill artifact that owns the gate procedure and makes
it visible, repeatable, and reviewable.

The skill will define four stages:

1. **Steady-state preflight**
2. **Mutation probe lane**
3. **Chaos probe lane**
4. **Review-log submission + handoff**

The skill remains tool-agnostic. It uses the repo's existing tests, mocks, local
code edits, and worktree isolation rather than naming PIT, Stryker, Gremlin, or any
other external dependency as mandatory.

---

## Files and surfaces expected to change

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `skills/survivability/SKILL.md` | Create | Local-only skill that owns the survivability gate procedure |
| `skills/executing-plans/SKILL.md` | Modify | Insert survivability between completed execution and branch finishing |
| `skills/subagent-driven-development/SKILL.md` | Modify | Insert survivability between final review and branch finishing |
| `skills/review-log-jsonl.md` | Modify only if required | Add named survivability logging template only if the generic append contract is insufficient |
| `AGENTS.md` | Modify only if required | Remove the temporary inline survivability template once the standalone skill owns the gate |
| `tests/` | Create / modify | Prove the local catalog includes the skill and workflow skills reference it correctly |

---

## Detailed design

### 1. Standalone skill, gate semantics preserved

The new `skills/survivability/SKILL.md` is a local-only skill that embodies the
survivability gate. It does **not** redefine survivability as a new lifecycle meaning.
Instead:

- the gate remains the lifecycle concept
- the skill is the local catalog artifact that operationalizes the gate

This resolves the tension between the older controller-oriented lifecycle mapping and
the newer retargeted catalog model that treats local-only skills as first-class peers.

### 2. Steady-state preflight

Before any mutation or chaos experiment runs, the skill must require:

- one explicit steady-state verification command
- the expected healthy signal for that command
- one focused test command for the changed logic under test

If the agent cannot name these commands and signals, the skill stops. No experiment
runs without a measurable baseline.

This follows chaos-engineering guidance to start with a steady-state hypothesis rather
than with arbitrary damage.

### 3. Mutation probe lane

The mutation lane measures test effectiveness, not line coverage.

For a small change, the skill requires a bounded mutation slate of **3 representative
probes**:

1. a boundary/condition mutation
2. a failure-path removal or happy-path bias mutation
3. a returned-value or state mutation

For broader changes, the skill adds **1 probe per additional meaningful decision
point**, capped at **5 total**.

Each probe follows the same loop:

1. apply one reversible mutation
2. run the same focused test command
3. classify the result as killed or survived
4. restore the original state before moving to the next probe

If any mutant survives, the survivability gate fails immediately. The work returns to
test strengthening before finish can proceed.

This aligns with mutation-testing guidance from Martin Fowler, PIT, and Stryker:
mutation testing is a targeted probe of whether tests detect realistic faults in
changed code, not a proxy for execution coverage.

### 4. Chaos probe lane

The chaos lane validates that the changed system degrades safely under realistic
disturbances.

For **local-only changes**, the skill requires at least **1** realistic fault probe.

For **dependency-touching changes**, the skill requires at least **2** realistic fault
probes, capped at **3 total**. The default pair should cover:

- latency/timeout-style degradation
- bad-response / null-response / dependency-unavailable degradation

Every chaos probe must include:

- the fault to inject
- the expected safe degradation behavior
- explicit abort/restore steps
- a rerun of the steady-state verification command

The skill must minimize blast radius and stay inside the existing local execution flow.
It must not require production-only experimentation infrastructure in this shard.

### 5. Review-log submission and retrospective handoff

The skill must append survivability outcomes to `.review_log.jsonl`.

At minimum, the logged summary must capture:

- work item identifier
- skill name
- phase/status vocabulary for survivability
- concise bounded reason text
- whether any mutation survived
- whether any chaos probe caused unsafe degradation

If a mutant survives, the skill must record that as **critical friction** so issue `#6`
can ingest it during retrospective analysis.

The skill may reuse the generic append contract in `skills/review-log-jsonl.md`. A
named survivability template should be added only if the spec proves the generic
template is not enough.

### 6. Workflow integration

The current local execution flows go directly to finishing:

- `executing-plans` → `finishing-a-development-branch`
- `subagent-driven-development` → final review → `finishing-a-development-branch`

This spec inserts survivability into both flows so the gate is structurally part of
the path to completion rather than an optional reminder in `AGENTS.md`.

---

## Threat Model (CIA)

### Confidentiality

**Risk:** Mutation and chaos runs can capture secrets, environment output, or large raw
test logs and accidentally persist them in `.review_log.jsonl`.

**Repository proof:** `skills/review-log-jsonl.md:8-13,28-41` defines append-only
logging and preserves raw reason text, but does not provide a redaction layer.

**Control:** The new skill must log only **bounded experiment summaries**. It must
forbid copying full stdout/stderr, full diffs, or secret-bearing environment output
into `.review_log.jsonl`.

### Integrity

**Risk:** Mutation and chaos probes intentionally distort logic or runtime conditions.
If restore steps fail, the repo can retain corrupted state, commit a mutant, or
invalidate later verification.

**Repository proof:** `skills/using-git-worktrees/SKILL.md:6-15,51-70` defines
isolated workspace setup and safety checks; execution already expects isolated
worktrees before implementation begins.

**Control:** Every probe must be reversible, restore before the next probe, and fail
closed if the workspace cannot be returned to the pre-probe state.

### Availability

**Risk:** Unbounded probe loops, hangs, or high-blast-radius fault injection can turn
survivability itself into a failure source.

**Repository proof:** `skills/survivability/SKILL.md:53-70` names realistic local
faults (500ms latency, timeout, null response, dependency unavailable). External
chaos-engineering guidance requires a steady-state hypothesis and minimal blast
radius.

**Control:** Require a steady-state command before any experiment. Cap mutation probes
at 3-5. Require 1 chaos probe minimum for local-only changes and 2 for
dependency-touching changes, capped at 3 total. Require explicit abort/restore steps.

### Least privilege

**Risk:** The skill could overreach by demanding new services, broad permissions, or
open-ended experiment scope.

**Repository proof:** The current local workflow is file-based, test-driven, and
worktree-based; no special chaos platform exists in the repo today.

**Control:** The skill must operate with the narrowest required scope: changed code,
focused tests, local mocks/stubs, and isolated worktree execution.

### Supply chain

**Risk:** Naming PIT, Stryker, Gremlin, or similar tooling as required dependencies
would invent new supply-chain scope that the repo has not approved or installed.

**Repository proof:** `pyproject.toml` only includes `pytest` in dev dependencies, and
`package.json` is metadata-only.

**Control:** No new dependency is required by this spec. Tool-backed mutation or chaos
automation belongs to a later shard if the repo explicitly adds and verifies it.

---

## Acceptance criteria

1. **Given** a completed change under test  
   **When** `survivability` starts  
   **Then** it refuses to run until the agent names one explicit steady-state
   verification command and the expected healthy signal.

2. **Given** a small logic change  
   **When** the mutation lane runs  
   **Then** the skill requires a mutation slate of 3 representative probes and reruns
   the same focused test command after each probe.

3. **Given** a change that touches additional meaningful decision points  
   **When** the mutation slate is built  
   **Then** the skill adds 1 probe per additional decision point, capped at 5 total.

4. **Given** any surviving mutant  
   **When** the focused tests still pass  
   **Then** the skill fails the survivability gate, records critical friction in
   `.review_log.jsonl`, and routes the work back to stronger tests before finish.

5. **Given** a local-only change  
   **When** the chaos lane runs  
   **Then** the skill requires at least 1 realistic fault injection with abort/restore
   steps and re-runs the steady-state command.

6. **Given** a dependency-touching change  
   **When** the chaos lane runs  
   **Then** the skill requires at least 2 realistic fault probes, capped at 3 total,
   and checks whether the system degrades safely.

7. **Given** a chaos probe causes unsafe degradation or unrecoverable state  
   **When** the steady-state check fails or restore cannot complete  
   **Then** the skill blocks finish and reports the exact failure.

8. **Given** the mutation and chaos lanes both pass  
   **When** the skill completes  
   **Then** it emits a bounded survivability summary and hands a survivability score
   forward to retrospective work.

---

## Empirical verification before review

This draft is grounded in the current repository state:

- At draft time, `AGENTS.md` contained the inline survivability template that this
  branch replaces with the standalone skill
- `skills/executing-plans/SKILL.md` and `skills/subagent-driven-development/SKILL.md`
  prove the current workflow bypasses an explicit survivability skill
- `skills/review-log-jsonl.md` and `.review_log.jsonl` prove the append-only log
  contract and the existence of the log surface
- `docs/superpowers/specs/2026-04-15-resistance-engine-catalog-retarget-design.md`
  proves local-only skills may be first-class peers
- `docs/superpowers/specs/2026-04-14-superpowers-overlay-lifecycle-design.md` proves
  survivability previously existed as a lifecycle gate
- `pyproject.toml` and `package.json` prove no dedicated mutation or chaos dependency
  is installed today

---

## Review and audit gates

This shard inherits the repo's standard spec-review discipline before it may proceed to
plan writing.

### Self-review gate

Before planning:

- run the full `brainstorming` self-review manifest and rubric
- reject the spec if any required criterion fails
- fix rejected sections inline
- run a post-fix consistency check across assumptions, detailed design, threat model,
  files/surfaces, and acceptance criteria so no stale contradictory text remains

### Cross-model audit gate

After self-review passes:

- dispatch an opposite-family audit reviewer
- provide the full spec, issue details, and empirical verification evidence
- record the result in `.review_log.jsonl`

### Fail-closed transition rule

Rejected specs may **not** proceed to `writing-plans`.

Planning may begin only after:

1. self-review returns `[SPEC-APPROVED]`
2. the opposite-family audit returns `APPROVED - CROSS-MODEL AUDIT`
3. both review outcomes are recorded in `.review_log.jsonl`

---

## Source-of-truth sync

Scope change from deferred issue `#3` was synchronized into GitHub Issues:

- `#4` — parent: remaining imported gaps and local-only additions
- `#5` — this survivability shard
- `#6` — retrospective shard
- `#7` — bootstrap compatibility shard

Issue `#3` was updated with a deferral comment before this shard was opened.

---

## Future work (downstream cost)

- **P1 / Medium** — Issue `#6` should consume survivability summaries and critical
  friction entries as a formal retrospective input rather than prose convention.
- **P1 / Medium** — Issue `#7` should decide whether bootstrap/startup guidance needs
  to advertise survivability explicitly in the lifecycle map.
- **P2 / Medium** — If the repo later installs real mutation tooling, a follow-on shard
  can upgrade the manual mutation slate to tool-backed execution.
- **P2 / Small** — If more AGENTS-only lifecycle phases are promoted, define a repeatable
  local-skill pattern for future migrations.
