---
name: defining-architecture
description: "Use when an approved epic needs its architecture decided before features are planned, when a later stage asks for the architecture model to be changed, or when a repository with no architecture model is onboarded. Also use when someone asks to just draw the boxes, skip the architecture checks, treat a model change as a one-line edit, or stop a run early because its request will be refused."
---

# Defining Architecture

## Overview

This skill keeps a target C4 model of the repository (LikeC4 `.c4` files, plus `architecture.md` and `known-gap.json`) in the model folder, and amends it.

**Core principle:** every run is a reviewed amendment to a model that is checked against the code. Nothing is decided in prose alone, nothing is approved in one step, and no breach is accepted without the delta tool reporting it and the owner accepting it.

**Announce at start:** "I'm using the defining-architecture skill."

## When to Use

| Trigger | Entry gate |
|---|---|
| An epic needs its architecture (epic run) | The epic has `[EPIC-APPROVED]` |
| A later stage (`planning-features`, `specifying-features`, `specifying-work-items`, `writing-plans`, the code review before a merge, or `finishing-a-development-branch`) needs the model changed (later-stage run) | The model has `[ARCH-APPROVED]` and the asking stage has written a diff request (what to change and why) |
| A repository is onboarded with no model (baseline run) | None |

## When NOT to Use

- The epic is not `[EPIC-APPROVED]`: finish `specifying-epics` first.
- To skip a run because the request looks wrong. A request that changes a product rule, or changes a cross-cutting decision in part, is refused inside the run at step 2c, after the baseline check; this skill adds no product rules, and the rule change goes back to the epic.
- The work is designing a feature's internals (functions, schemas, field lists, algorithms): that belongs to the feature and its work items.

## Ownership

This skill owns the model folder's content: the `.c4` files, `architecture.md` and `known-gap.json`. It owns no code and changes none. It does not write the architecture into the overlay file, the epic or any other document. Outside the model folder it writes only a waiver entry in the epic's decision log (when an epic run is waived) and the append-only work-item notes. Filling `close_by` on gap entries belongs to `planning-features`. Removing a gap entry `check` reports stale belongs to the branch that fixed the breach, at `finishing-a-development-branch`, and to `specifying-features` at a feature's close for any entry still stale. Merging, branching and feature planning belong to the stages after this one.

## Files and tools

- Load `ARCH_STANDARDS.md` at step 1: the overlay keys and defaults, the delta tool flags, the Terms, how to spot a cross-cutting decision, what counts as mechanism detail, the gap reason format and the `architecture.md` layout.
- Load `baseline-run.md` only at step 2b, when some groups the run touches are not yet modelled.
- Load `review-workflow.md`, `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md` only at step 6.
- **The delta tool ships with this skill:** `node <skills-dir>/shared/scripts/architecture-delta.mjs` (`export` and `check`). The repository does not need its own copy. Reading the code and comparing it with the model by hand is never a substitute for `check`.

## Quick Reference

One step at a time. Each step is presented, and the owner approves it before the next starts. An approval covers the step it answers, nothing more. Each step covers only what the diff touches, except the checks `ARCH_RUBRIC.md` marks `[whole]`.

1. **Assumptions surface** (load `ARCH_STANDARDS.md`). Your first output is this and nothing else: the trigger and its entry gate; required or waived (epic run); the overlay's values or their defaults; the `deps-command`; for an epic run, the epic's capabilities. No options, no design, no recommendation for the architecture yet. Anything missing stops the run.
2. **Baseline check.** Run the `deps-command`, then `export` and `check` (both skipped while the model folder is empty). A `check` exit 1 (a breach not in the gap file, or a stale entry) is a finding for 2a; exit 2 stops the run with the tool's error. Propose the groups the run touches; the owner approves the list.
   - **2a. Is the affected model current?** For every modelled element the run touches, its relationships and its gap entries, look for:
     - an invalid model: it doesn't load, `c4.c4` differs from the shipped spec, or the relationships have a cycle;
     - a `code` value that matches no module;
     - a breach not in the gap file (drift);
     - a gap entry that no longer matches (its breach was fixed);
     - a relationship reported "not yet reached" that the code now has (note it only).
     Each finding gets its own recommendation (see "Drift is a finding" below), and the owner decides each. Change nothing before that.
   - **2c. Does the request stand?** (later-stage run) Only now, after 2a, judge the diff request. Refuse a request that changes a cross-cutting decision in part or for one bound element, or that changes a product rule; recommend the whole change, or the epic, instead. A refused request ends the diff, not the run: the run carries on with the 2a outcomes, writes its decision-log entry (the refusal, the 2a outcomes, the quoted `check`), and goes through step 6 to `[ARCH-APPROVED]`.
   - **2b. How much to baseline?** Only when touched groups are not yet modelled: one question with a recommendation and the counts behind it, then load `baseline-run.md`. The baseline is its own diff through steps 3 to 6, approved with its own `[ARCH-APPROVED]`, before the run resumes.
3. **Cross-cutting decisions** in scope, each with options and a recommendation, approved separately.
4. **The diff:** elements with `code` and `rules`, tags (`#protected`, `#layer`, `#generic`, `#eval`), relationships and invariants expressed as relationships, before and after, with the rule map. If the diff needs an edge node's inside, go back to 2b for that area; its baseline is approved on its own, then the run returns to step 3.
5. **The known gap:** `check` against the amended model. Each breach the diff adds gets a proposed entry with a reason; entries the diff closes are removed; entries naming an element the diff renames or removes are re-keyed or removed. The owner accepts or rejects each one.
6. **Write, review, approve** (load `review-workflow.md`): write the files, self-review, independent audit, the owner's `[ARCH-APPROVED]`, then the work-item note.

## Rules

**Every run is an amendment.** A run proposes a diff to whatever is in the model folder: elements, relationships, tags, metadata and cross-cutting decisions added, changed or removed, each with a reason and the stage that asked. The first run in a repository amends an empty model. The **model folder is empty** when it is absent or holds no `.c4` file other than `c4.c4`.

**When an epic run is required.** Always, unless the owner agrees from the epic's capabilities both that the epic ships as one feature and that no module is expected to be reached from two or more entry paths. A waiver is written in the epic's decision log with both judgments and appended as a note to the epic's work item, and the skill stops. No review-log entry is written for a waiver.

**Baseline before target.** An epic run on a repository whose touched groups are not modelled first records what the code *is* (step 2b), with every cycle in the current code recorded in `known-gap.json` as `cycle in current code`. Only then does the epic's diff turn it into what the code *should be*. A design with no baseline under it cannot be checked.

**Drift is a finding, never a quiet edit.** For each step 2a finding, recommend one of the allowed outcomes and let the owner decide:
- a `code` value that matches no module: update it to describe what is;
- a breach not in the gap file (code drifted since approval): either a gap entry with a reason, so the target stands (the default recommendation), or a target change in this run's diff with its own reason;
- a gap entry that no longer matches: remove it.

Adding a relationship just because the code now has the import makes the drift legal without a decision. Don't.

**Cross-cutting decisions are taken whole.** A decision two or more capabilities depend on is decided once for all of them. Its section names the decision, its owning element, the elements and capabilities it binds, its product-level obligations and its compatibility rule, and nothing else. A request to change part of it, or to change it for one bound element only, is refused: the decision is used as is or changed whole, for every bound element, in this run's diff.

**`check` runs every time.** Every run quotes a fresh `check` output in its decision-log entry, even when the model didn't change and even when the request is refused: the code may have drifted, and the asking stage plans against the model. No run ends before step 2 has run `check` on a non-empty model.

**Approval.** `[ARCH-APPROVED]` comes only after self-review and the independent audit have passed, and only from the owner. One `Approved.` to a step is approval of that step. A run is not finished until the owner has given `[ARCH-APPROVED]` for it.

## Hard rules

- No new product rules: a rule gap goes back to the epic.
- Every Must rule has exactly one owning element.
- Every breach `check` reports is in `known-gap.json` with a reason; none is allowed silently and none is fixed by changing code.
- Inside the baselined coverage, every module `check` lists as unmapped is mapped or listed in `architecture.md` with a reason.
- No mechanism detail: no functions, schemas, field lists or algorithms.
- The model loads with no errors and uses the shipped C4 spec (`c4.c4`) unchanged.
- No code file is changed.

## Review log

Each review round is logged with the append CLI, to the repository's review log unless told otherwise:

```bash
python <skills-dir>/shared/scripts/review-log.py append --item-id <id> --skill defining-architecture --phase ARCH_REVIEW --round <n> --verdict APPROVED|REJECTED --orchestrator <model> --reviewer-model <model> --independence self --reason "<reason>" [--finding <severity>:<kind>:<text> ...]
```

`<reason>` starts `epic`, `later-stage: <stage>` or `baseline`. A `REJECTED` entry needs at least one `--finding`.

The audit uses `--phase INDEPENDENT_AUDIT`. `review-workflow.md` gives the full loop.

## Handoff

An epic run hands off to `planning-features`, or straight to `specifying-features` for an epic the owner agrees ships as one feature. A later-stage run hands back to the stage that asked. A baseline run on its own ends there.

## Red Flags — stop

- Your first reply contains options or a design.
- You are about to write the architecture anywhere but the model folder.
- You found a cycle or a breach and are leaving it out of `known-gap.json`.
- You are comparing imports with the model by hand.
- A field list, function name or algorithm is in a decision.
- You are marking something approved, committing it or merging it after a single step approval.
- You are adding a relationship because the code has the import.
- You are skipping `check` because the model didn't change.
- You are ending a run before step 2 has run `check`.
- You noticed a mismatch between the model and the code and are leaving it for later.
- The run is ending with no review and no `[ARCH-APPROVED]`.

## Rationalisations

| Excuse | Reality |
|---|---|
| "The design adds no new dependencies, so the existing cycle can be left alone." | Today's cycle goes in `known-gap.json` with `cycle in current code`, or the model claims something the code doesn't do. |
| "The deadline is tight, so approve now and overlap the rest." | A deadline doesn't merge steps. The next step is small; present it. |
| "The team already spent weeks on the epic; don't make them redo it." | The epic isn't redone. The architecture is new work on top of it, and its steps still apply. |
| "The owner said Approved, so the architecture is approved." | That approves the step presented. `[ARCH-APPROVED]` comes after review and audit. |
| "Just draw the boxes." | The boxes are the model's diff (step 4), reached through steps 1 to 3. A picture with no model can't be checked. |
| "The model didn't change, so there's no need to re-run the check." | The code may have changed. Every run quotes a fresh `check`. |
| "The model should reflect the code as it is." | The baseline does. After that the model is the target, and drift is a decision: a gap entry or a target change. |
| "There's no architecture check tool in the repository." | The tool ships with this skill. Use it. |
| "The request is refused, so there's nothing to check." | The model can still have drifted, and the asking stage plans against it. Refuse at 2c, after the baseline check, and finish the run. |
| "It's a one-line change." / "The tech lead signed it off." / "The model was approved last week." | The size and the sign-off don't change the steps. The change still gets `check`, review and `[ARCH-APPROVED]`. |

## Common Mistakes

- **Designing in the first reply.** Step 1 is the assumptions surface only.
- **Writing the architecture into the overlay file or the epic.** The overlay holds settings; the model folder holds the architecture.
- **Treating the target as the baseline.** Record what is first, then amend it.
- **Putting a field list into a cross-cutting decision.** Name the obligations; leave the fields to the first feature that builds it.
- **Asking "should I fix this?" without a recommendation.** Every finding and every question carries one.
