# Resistance engine authoring scaffolding restoration

**Date:** 2026-04-16  
**Status:** Drafted for review  
**Prerequisite spec:** `docs/superpowers/specs/2026-04-15-resistance-engine-authoring-pair-rewrite-design.md`

---

## Problem

The shipped worktree rewrite for the authoring pair preserved the hardening goals of
the 2026-04-15 authoring-pair rewrite, but it also removed operator-facing workflow
scaffolding that existed in the vendor defaults.

That loss is now visible in the current worktree:

- `brainstorming` no longer exposes vendor sections such as `## Anti-Pattern`,
  `## Checklist`, `## Process Flow`, `## The Process`, and `## After the Design`
- `writing-plans` no longer exposes vendor sections such as `## Scope Check`,
  `## File Structure`, `## Bite-Sized Task Granularity`, `## Task Structure`,
  `## No Placeholders`, and `## Execution Handoff`

The prior rewrite succeeded as a self-sufficient safety rulebook, but it became harder
to operate as a guided workflow. The regression is not that the current skills are
weak; the regression is that they are harder to execute correctly under pressure.

This follow-on work must restore workflow scaffolding without weakening the current
self-sufficient defaults, fail-closed overlay model, CIA burden-of-proof, or audit
gates. The acceptance criteria from the 2026-04-15 rewrite remain authoritative and
must still pass after the restoration.

---

## Current-state evidence

The current repository state shows the operator-guidance gap directly.

```text
$ rg -n "^## " resistance-engine/skills/brainstorming/SKILL.md
8:## Overview
25:## Core Premise
56:## Mandatory outputs
78:## Drafting-time repository ingestion
120:## Fail-closed ambiguity
138:## Spec sharding and refactor isolation
167:## Source-of-truth sync
194:## Empirical verification before review
234:## Review loop discipline
272:## Cross-model audit
296:## Optional overlays
323:## Red flags — stop and question
344:## Common rationalizations

$ rg -n "^## " vendor/obra-superpowers/skills/brainstorming/SKILL.md
16:## Anti-Pattern: "This Is Too Simple To Need A Design"
20:## Checklist
34:## Process Flow
68:## The Process
107:## After the Design
138:## Key Principles
147:## Visual Companion

$ rg -n "^## " resistance-engine/skills/writing-plans/SKILL.md
8:## Overview
25:## Tabula Rasa Mandate
35:## Spec simplification and pushback
49:## Mandatory opening output
82:## Strict RED / GREEN / REFACTOR
104:## Dependency ordering
116:## Manual steps and runbooks
136:## Chunking and context protection
146:## Pre-plan verification
159:## Fail-closed planning contract
172:## Unhappy-path-first planning
189:## Plan self-review
209:## Unified Coherence Check
256:## Common rationalizations

$ rg -n "^## " vendor/obra-superpowers/skills/writing-plans/SKILL.md
8:## Overview
21:## Scope Check
25:## File Structure
36:## Bite-Sized Task Granularity
45:## Plan Document Header
63:## Task Structure
106:## No Placeholders
116:## Remember
122:## Self-Review
134:## Execution Handoff
```

The existing approved spec also remains the constraint surface for this work:

```text
$ rg -n "^## BDD acceptance criteria|^### Self-sufficient defaults|^### Brainstorming behavior|^### Writing-plans behavior|^### Overlay behavior|^### Audit gate behavior" docs/superpowers/specs/2026-04-15-resistance-engine-authoring-pair-rewrite-design.md
488:## BDD acceptance criteria
490:### Self-sufficient defaults
510:### Brainstorming behavior
540:### Writing-plans behavior
568:### Overlay behavior
594:### Audit gate behavior
```

Those existing criteria already require self-sufficient defaults, CIA threat
modeling, fail-closed overlays, and audit-gate behavior. This follow-on spec is
therefore additive: restore the workflow shell while preserving the current safety
core.

---

## Goals

- Restore explicit operator-facing workflow scaffolding to `brainstorming`
- Restore explicit executor-facing planning scaffolding to `writing-plans`
- Preserve every existing acceptance criterion from the 2026-04-15 authoring-pair
  rewrite
- Keep the current worktree’s hardening rules authoritative inside the restored flow
- Execute the work sequentially: `brainstorming` first, then `writing-plans`
- Preserve the current fail-closed overlay behavior and self-sufficient defaults

## Non-goals

- No rollback to vendor wording wholesale
- No weakening of CIA burden-of-proof, repository-proof requirements, or audit gates
- No removal of Tabula Rasa, Risk & Confidence Assessment, Unified Coherence, or
  unhappy-path-first planning
- No new generalized overlay engine
- No change to the existing requirement that the authoring pair works without repo-root
  overlays

---

## Approach

Treat the current worktree files as the **safety core** and the vendor files as the
**workflow shell**.

The restoration should reintroduce the missing headings, state-machine guidance, and
handoff scaffolding that made the vendor skills easy to operate, but it must route
those sections through the current worktree rules rather than around them.

This is a layering exercise:

1. restore operator guidance sections
2. wire those sections into the current hard gates
3. verify that the existing authoring-pair contract still passes unchanged

---

## Files and surfaces expected to change

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `resistance-engine/skills/brainstorming/SKILL.md` | Modify | Restore operator-facing workflow sections while preserving the current hardening and audit gates |
| `resistance-engine/skills/writing-plans/SKILL.md` | Modify | Restore executor-facing planning scaffolding while preserving the current fail-closed planning contract |
| `tests/scripts/test_import_superpowers_catalog.py` | Modify | Extend wording-level regression coverage for restored workflow headings and preserved hardening language if current assertions are too narrow |
| `tests/scripts/test_validate_resistance_engine_provenance.py` | Modify | Preserve authoring-default contract coverage if wording-level expectations change |
| `resistance-engine/catalog/catalog_index.json` | Regenerate if needed | Keep catalog output aligned with updated source skill content |
| `resistance-engine/provenance/provenance_manifest.json` | Regenerate if needed | Keep provenance output aligned with updated source skill content |

If implementation can preserve the current tests without changing their assertions, it
should do so. Test edits are allowed only where the restored headings materially change
the shipped wording contract.

---

## Detailed design

### 1. Restore `brainstorming` as a guided state machine

`resistance-engine/skills/brainstorming/SKILL.md` should regain explicit workflow
sections equivalent in role to:

- `## Anti-Pattern: "This Is Too Simple To Need A Design"`
- `## Checklist`
- `## Process Flow`
- `## The Process`
- `## After the Design`

But those restored sections must explicitly route through the current safety core:

- adversarial interrogation before design confidence rises
- repository-grounded verification before claims become accepted facts
- fail-closed blocking questions when ambiguity cannot be resolved by inspection
- mandatory `### Threat Model (CIA)`
- post-fix consistency checks before the next review round
- `.review_log.jsonl` recording of review outcomes
- `[SPEC-APPROVED]` as the hard prerequisite for plan writing

The restored `## Process Flow` is especially important. It should make loopbacks
explicit for:

- unanswered blocking questions
- design sections the user wants revised
- written spec changes requested by the user
- failed spec audit results

This section should restore operator readability without softening the adversarial
stance.

### 2. Restore `writing-plans` as an executor-ready scaffold

`resistance-engine/skills/writing-plans/SKILL.md` should regain explicit workflow
sections equivalent in role to:

- `## Scope Check`
- `## File Structure`
- `## Bite-Sized Task Granularity`
- `## Task Structure`
- `## No Placeholders`
- `## Execution Handoff`

Those restored sections must explicitly sit on top of the current planning laws:

- physical spec ingestion before planning
- `### Risk & Confidence Assessment`
- strict RED / GREEN / REFACTOR sequencing
- dependency ordering
- runbook treatment for manual steps
- fail-closed planning contract
- unhappy-path-first planning
- Unified Coherence as the final approval gate

`## Execution Handoff` must again make the implementation transition clear by naming
the supported execution paths (`subagent-driven-development` and `executing-plans`)
without allowing either to bypass the current fail-closed checks.

### 3. Preserve the existing authoring-pair contract unchanged

The current approved acceptance criteria from the 2026-04-15 rewrite remain in force.
This follow-on work is successful only if:

- the self-sufficient default behavior still holds without repo-root overlays
- the overlay model still rejects weakening or malformed overlays
- `brainstorming` still requires CIA proof-or-blocker outputs and audit-gate behavior
- `writing-plans` still requires Tabula Rasa, Risk & Confidence Assessment,
  unhappy-path planning, and Unified Coherence

### 4. Execute in two sequential restore tasks

The implementation plan derived from this spec should create and execute two tasks in
order:

1. restore `brainstorming` scaffolding
2. restore `writing-plans` scaffolding

The second task must depend on the first so the operator-facing recovery lands before
the planning handoff repair.

---

## BDD acceptance criteria

### Existing criteria remain mandatory

1. **Given** the 2026-04-15 authoring-pair rewrite criteria are already approved  
   **When** this restoration lands  
   **Then** every existing self-sufficient-default, overlay, CIA, writing-plans, and
   audit-gate criterion still holds without relaxation.

### Brainstorming restoration

2. **Given** a user opens the restored `brainstorming/SKILL.md`  
   **When** they inspect the workflow guidance  
   **Then** the file includes explicit operator-facing sections for anti-pattern
   framing, checklisting, process flow, live process guidance, and post-design handoff.

3. **Given** a user follows the restored `brainstorming` process flow  
   **When** a blocking ambiguity, rejected design section, requested spec change, or
   failed spec audit occurs  
   **Then** the flow shows the explicit loopback path instead of leaving the recovery
   state implicit.

4. **Given** the restored `brainstorming` workflow guidance exists  
   **When** it routes the user toward planning  
   **Then** it still requires repository grounding, `### Threat Model (CIA)`,
   `.review_log.jsonl` review recording, and `[SPEC-APPROVED]` before invoking
   `writing-plans`.

### Writing-plans restoration

5. **Given** a user opens the restored `writing-plans/SKILL.md`  
   **When** they inspect the workflow guidance  
   **Then** the file includes explicit executor-facing sections for scope check, file
   structure, task structure, no-placeholder discipline, and execution handoff.

6. **Given** the restored `writing-plans` handoff guidance exists  
   **When** planning transitions into execution  
   **Then** it explicitly names `subagent-driven-development` and
   `executing-plans` as supported paths while preserving the current fail-closed
   review and verification gates.

7. **Given** the restored `writing-plans` scaffolding is present  
   **When** an operator follows the task-writing guidance  
   **Then** the guidance still requires Tabula Rasa ingestion, `### Risk & Confidence
   Assessment`, strict RED / GREEN / REFACTOR, unhappy-path planning, and Unified
   Coherence instead of allowing a simpler but weaker workflow.

### Overlay safety

8. **Given** a repo-root overlay attempts to use the restored guidance sections to
   weaken a mandatory default gate  
   **When** the authoring pair evaluates that overlay  
   **Then** the workflow still fails closed instead of treating the restored headings as
   an escape hatch.

---

## Security & Risk Analysis

### Threat Model (CIA)

#### Confidentiality

This work edits authoring documentation, not live user-data flows, so direct data
exposure risk is low. The real confidentiality risk is indirect: if the restored
workflow shell made it easier to skip threat modeling or repo verification, a later
spec could under-model PII or access-control exposure. Mitigation: the restored
sections must route into the existing proof-or-blocker CIA requirements instead of
offering a softer parallel path.

#### Integrity

Integrity risk is medium. The main failure mode is document drift: a restored checklist
or handoff could contradict the current hard gates and teach the model the wrong
behavior. Mitigation: preserve the current safety sections as authoritative, keep the
existing 2026-04-15 acceptance criteria unchanged, and add additive acceptance checks
for the restored workflow sections.

#### Availability

Runtime availability risk is low because this is skill documentation work. The
practical availability risk is process-level: if the restored flow becomes ambiguous,
review cycles lengthen and execution stalls. Mitigation: restore explicit state-machine
loopbacks and execution handoff sections so operators can recover cleanly from blockers
and rejected reviews.

#### Least privilege and supply chain

This spec introduces no new third-party dependencies and no new runtime privilege
boundaries. The relevant safety rule remains process-level: restored guidance must not
license broader overlay behavior or a generalized rule-ingestion framework beyond this
pair of skills.

---

## Future work

- If this restoration still leaves `writing-skills` ergonomically inconsistent with the
  repaired authoring pair, create a separate follow-on shard instead of expanding this
  scope.
- If the catalog later needs a shared workflow-shell pattern across multiple skills,
  treat that as a distinct overlay/framework shard rather than broadening this restore.
