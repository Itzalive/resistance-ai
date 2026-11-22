---
name: defining-architecture
description: "Use when an approved epic needs its architecture decided before features are planned, when a later stage asks for the architecture model to be changed, or when a repository with no architecture model is onboarded. Also use when someone asks to just draw the boxes, skip the architecture checks, treat a model change as a one-line edit, or stop a run early because its request will be refused."
---

# Defining Architecture

## Overview

This skill keeps a target C4 model of the repository in the model folder and amends it. The model folder holds the LikeC4 `.c4` files, `known-gap.json`, the records (`decisions/`, `contracts/`, `changes/`, `coverage.json`) and the generated documents (`generated/`). There is no `architecture.md`.

**Core principle:** every run is a reviewed amendment to a model that is checked against the code. Every judgement goes into a validated record, every run that is not waived leaves one change file, and the owner approves from the generated documents. Nothing is decided in prose alone, nothing is approved in one step, and no breach is accepted without `check` reporting it and the owner accepting it.

**Announce at start:** "I'm using the defining-architecture skill."

## When to Use

| Trigger | Entry gate |
|---|---|
| An epic needs its architecture (epic run) | The epic has `[EPIC-APPROVED]` |
| A later stage (`planning-features`, `specifying-features`, `specifying-work-items`, `writing-plans`, the code review before a merge, or `finishing-a-development-branch`) needs the model changed (later-stage run) | The model is approved: every file in `changes/` has a non-null `approved`, and the asking stage has written a diff request |
| A repository is onboarded with no model (baseline run) | None |

## When NOT to Use

- The epic is not `[EPIC-APPROVED]`: finish `specifying-epics` first.
- To skip a run because the request looks wrong. A request that changes a product rule, or changes a cross-cutting decision in part, is refused inside the run at step 2c, after the baseline check.
- Designing a feature's internals (functions, schemas, field lists, algorithms): that belongs to the feature and its work items.

## Ownership

This skill owns the model folder's content and changes no code. Outside the model folder it writes only a waiver entry in the epic's decision log (when an epic run is waived), the append-only work-item notes, and its before copies, which are never committed. Filling `close_by` on gap entries belongs to `planning-features`; removing a stale gap entry belongs to the branch that fixed the breach, or to `specifying-features` at a feature's close. Merging, branching and feature planning belong to later stages.

## Steps

One step at a time: each step is its own reply, ending in that step's approval question, and nothing from the next step is sent with it. A step with nothing to decide (no cross-cutting decision, no new gap entry) is still presented on its own. An approval covers the step it answers, nothing more. Load each file at its step.

1. **Assumptions surface** (load `ARCH_STANDARDS.md`). Your first output is this and nothing else: the trigger and its gate; required or waived (epic run); the overlay's values or defaults, `roots` included; the `deps-command`; for an epic run, the capabilities. No options and no design. Before writing it, run the `deps-command` and read the repository modules from the dependency file, so `roots` (or the shared prefix) can be checked; an overlay error stops the run here. Anything missing stops the run.
2. **Baseline check** (load `tools.md` and `amendment.md`): `check`, then 2a (is the model current?), 2c (does a later-stage request stand?), 2b (how much to baseline? load `baseline-run.md`; a baseline run asks nothing and loads it here).
3. **Write the draft amendment** (load `records.md`): the files first, then `change`, coverage, `export`, `check`, `architecture-docs build`. Nothing is presented before this step has run.
4. **Cross-cutting decisions,** presented from the written records.
5. **The diff,** presented from the generated change document and area documents.
6. **The known gap,** from the written `check`.
7. **Review and approval** (load `review-workflow.md`, `ARCH_REVIEW_MANIFEST.md`, `ARCH_RUBRIC.md`).

## Rules

**Every run is an amendment** to whatever is in the model folder. The first run amends an empty model. The model folder is empty when it is absent or holds no `.c4` file other than `c4.c4`.

**When an epic run is required.** Always, unless the owner agrees from the epic's capabilities both that the epic ships as one feature and that no module is expected to be reached from two or more entry paths. A waiver is written in the epic's decision log and the work-item note, and the run stops: no change file, no review-log entry.

**Baseline before target.** A run whose touched groups are not modelled first records what the code *is* (`baseline-run.md`), as its own diff with its own change file and `[ARCH-APPROVED]`. Only then does the outer diff turn it into what the code should be.

**Drift is a finding, never a quiet edit.** For each step 2a finding, recommend one allowed outcome and let the owner decide:
- a `code` value that matches no module: update it to describe what is;
- a breach not in the gap file: a gap entry with a reason, so the target stands (the default), or a target change in this run's diff with its own reason;
- a gap entry that no longer matches: remove it.

Adding a relationship because the code now has the import makes the drift legal without a decision. Don't.

**Judgement goes into records.** A decision is a record in `decisions/`, a cross-cutting decision is a decision with `obligations`, an open question or an improvement you see and do not make is a hole or a proposed decision, binding the elements it concerns, so it appears in the improvement list. Never leave one in a reply, a note or prose only.

**Cross-cutting decisions are taken whole.** A decision with `obligations` is decided once for every part it binds; a principle binds the whole system. A request to change part of one, or to change it for one bound element, is refused.

**A decided target is recorded.** A target the owner states during a run is never deferred unrecorded: in an epic or later-stage run it is part of the diff; after a baseline it becomes the first amendment (`baseline-run.md`).

**`check` runs every time.** Every run quotes a fresh `check` in its change file, even when the model did not change and even when the request is refused. No run ends before step 2 has run `check` on a non-empty model.

**The tools are the source.** `check` finds breaches, `cycles` chooses what a cycle leaves out, `change` writes the change file, `architecture-docs build` writes the documents (`tools.md`). Comparing imports with the model by hand, or hand-writing a change file, is never a substitute.

**What the owner approves from:** the generated documents (`amendment.md`), never the record files or your own summary.

**A change file is never edited after its run is approved** (`records.md`).

**Approval.** `[ARCH-APPROVED]` comes only after self-review and the independent audit have passed, and only from the owner. A run is not finished until the owner has given it.

## Hard rules

- No new product rules: a rule gap goes back to the epic.
- Every Must rule has exactly one owning element, in an epic run and in any run on a model that already assigns `rules`.
- Every breach `check` reports is in `known-gap.json` with a reason; none is allowed silently and none is fixed by changing code.
- Inside the coverage, every module `check` lists as unmapped is mapped or listed in `coverage.json` `unmapped` with a reason.
- No mechanism detail: no functions, schemas, field lists or algorithms.
- The model loads with no errors and uses the shipped `c4.c4` unchanged.
- No code file is changed.

## Review log

Each review round is logged with the append CLI, to the repository's review log unless told otherwise (`review-workflow.md` gives the loop):

```bash
python <skills-dir>/shared/scripts/review-log.py append --item-id <id> --skill defining-architecture --phase ARCH_REVIEW --round <n> --verdict APPROVED|REJECTED --orchestrator <model> --reviewer-model <model> --independence self --reason "<reason>" [--finding <severity>:<kind>:<text> ...]
```

The audit uses `--phase INDEPENDENT_AUDIT`. `<reason>` starts `epic`, `later-stage: <stage>` or `baseline`. Severities are `critical`, `important`, `minor`; kinds include `model-drift`, `deps-defect` and `unsourced` beside the shared ones.

## Handoff

An epic run hands off to `planning-features`, or straight to `specifying-features` for an epic the owner agrees ships as one feature. A later-stage run hands back to the stage that asked. A standalone baseline run (a repository with no model) ends after its decided-targets question and any first amendment. A nested baseline asks nothing: after its `[ARCH-APPROVED]` it hands back to the outer run at step 3, and the targets the epic or the request states go in the outer run's diff.

## Red Flags — stop

- Your first reply contains options or a design.
- You are presenting a decision or a diff that is not yet in the files.
- You are about to write `architecture.md`, or the architecture anywhere outside the model folder.
- You are writing a change file by hand, or choosing a cycle's leave-out without `cycles`.
- You are showing the owner your own summary instead of the generated documents.
- You found a cycle, a breach or an open question and it is in no record.
- The owner stated a target and it is neither in this run's diff nor, in a baseline run, carried as the recommended answer to the decided-targets question.
- You are looking for `[ARCH-APPROVED]` in a file instead of in the change files' `approved` fields.
- You are skipping `check` because the model didn't change or the request will be refused.
- You are marking something approved after a single step approval.
- You are editing a record an approved run wrote, other than through a new diff.
- You are adding a relationship because the code has the import.
- You are presenting two steps' material in one reply.
- A nested baseline is approved and you are about to ask for decided targets, or to run the epic's targets as a separate later-stage run.
- A field list, function name or algorithm is in a decision.
- The run is ending with no review and no `[ARCH-APPROVED]`.

## Rationalisations

| Excuse | Reality |
|---|---|
| "The model has no `[ARCH-APPROVED]` record and no `architecture.md`." | Approval is each change file's `approved` field. Read `changes/`. |
| "A one-line change doesn't change the steps, so I did not run `check`." | Holding the steps means running them: step 2 runs `check` before any request is judged. |
| "The epic run will turn your decision into the target." | A target the owner states is never left to another stage: it goes in this diff or, in a baseline run, is the recommended answer to the decided-targets question and becomes the first amendment. |
| "A baseline adds no containers or systems." | A baseline records what is, including a system, containers and outside systems (`baseline-run.md`). |
| "Each has one module edge, so it's a tie." | `cycles` breaks ties by a fixed order. Run it. |
| "`architecture.md` and `known-gap.json` come in step 6." | Files come first. Step 3 writes them; steps 4 to 6 present what is written. |
| "I recorded it in the decision log." | An open question is a hole record; it then appears in the improvement list. |
| "The design adds no new dependencies, so the cycle can be left alone." | Today's cycle goes in `known-gap.json` as `cycle in current code`. |
| "The team already spent weeks on the epic; don't make them redo it." | The epic isn't redone. The architecture is new work on top of it, and its steps still apply. |
| "The request is refused, so there's nothing to check." | The model can still have drifted. Refuse at 2c, after `check`, and finish the run. |
| "There's nothing to decide in step 4, so it can go with steps 5 and 6." | Each step is its own reply and its own approval, even when it holds nothing. |
| "The baseline is approved, so ask for decided targets." | Only a standalone baseline asks. A nested baseline hands back to the outer run at step 3; the epic's targets are its diff. |
| "The deadline is tight, so approve now and overlap the rest." | A deadline doesn't merge steps. |
| "The owner said Approved, so the architecture is approved." | That approves the step presented. `[ARCH-APPROVED]` comes after review and audit. |
| "Just draw the boxes." / "Mark it approved, I'll read the pages later." | The boxes are step 5's diff, reached through steps 1 to 4; approval comes after review, from the generated pages. |
| "The model should reflect the code as it is." | The baseline does. After that the model is the target, and drift is a decision. |
| "It's a one-line change." / "The tech lead signed it off." / "The model was approved last week." | Size and sign-off don't change the steps: `check`, review and `[ARCH-APPROVED]`. |

## Common Mistakes

- **Designing in the first reply.** Step 1 is the assumptions surface only.
- **Presenting before writing.** Step 3 writes and runs the tools; only then are decisions and the diff shown.
- **Treating the target as the baseline.** Record what is first, then amend it.
- **A field list in a cross-cutting decision.** Name the obligations; leave the fields to the first feature that builds it.
- **Asking "should I fix this?" without a recommendation.** Every finding and every question carries one.
