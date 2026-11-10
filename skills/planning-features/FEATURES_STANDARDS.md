# Feature planning standards

Load this file at step 1.

## Running the gate check

The overlay (`ARCHITECTURE_DESIGN.md`) and its keys are defined in `defining-architecture`'s `ARCH_STANDARDS.md`. Run the overlay's `deps-command`, then:

```bash
node <skills-dir>/shared/scripts/architecture-delta.mjs check --repo . --model <model> --deps <deps-file> --separator <separator>
```

Exit 0 passes the gate. Exit 1 (a new breach or a stale gap entry) or exit 2 sends the run to `defining-architecture`.

## Where the map lives

One file per epic: `docs/features/<epic>/feature-map.md`. The owner may name another folder at step 1. Feature designs from `specifying-features` sit beside it.

## The map's parts

| Part | Holds |
|---|---|
| Header | The epic; the date of the model decision-log entry the map was planned against; the approval tag |
| Features | One row per feature, in order (columns below) |
| Questions | One row per direction-changing question (columns below) |
| AC coverage | Every epic AC against exactly one feature, or marked cross-cutting (checked in every feature) |
| Order reasoning | One short paragraph per ordering rule |
| Re-plan log | Append-only, one dated entry per re-plan |

**Feature columns:**
- id (`F1`, `F2`, …) and goal;
- the success metric or MVP criterion it moves;
- the epic ACs it delivers;
- the cross-cutting decisions it builds on, marked `foundation` on the first feature to build on each;
- rough cost and the run records it was fitted from, or `guess`;
- the eval run that proves it;
- the known-gap entries it closes;
- entry paths, and implementations per rule;
- state (`planned`, `specified`, `shipped`) and actual cost.

**Question columns:**
- id (`Q1`, …) and the question;
- the feature that answers it;
- risk: what changes at each possible answer;
- split out: yes or no, with the reason;
- the answer, once given.

A split-out question also names its kind (spike, measurement or prototype), what it runs before or alongside, the decision its answer feeds and the features it could change.

## The split-out test

A direction-changing question is one whose answer could change the plan: an unproven technique, a cost or quality unknown, a dependency on another party. The epic's direction is its capabilities, its value order and its cross-cutting decisions.

Ask of each question: if the answer goes the other way, what has to be redone?

- **Only this feature's own design:** it stays with the feature.
- **Work in another feature, or the epic's capabilities, value order or a cross-cutting decision:** split it out, and place it before every feature it could invalidate.

State the risk against the real thresholds it crosses. "Might be slow" is not a risk; "over the response-time limit the epic sets, the capability moves from Must to Could" is.

A split-out question runs alongside the current feature only when the two share no files and neither needs the other's result. Otherwise it runs first.

## Signals

Counted per capability at step 3, from the model's rule map, the dependency file and a reading of the code:

- **Entry paths:** the distinct ways into the code the capability changes (an API route, a job, a message handler, a command).
- **Implementations per rule:** the number of places that implement each of the capability's rules today.

Three or more implementations of one rule that the epic would change is flagged as likely consolidation. This is a first count to make heavy consolidation visible before any feature is designed; `specifying-features` counts again per shard.

At step 4, each feature's counts are derived from the capabilities whose ACs it takes.

## Cost

- With run records (`.run_records.jsonl`): fit a fixed cost per plan and a cost per task from the project's own records, apply it to the feature's likely plans and tasks, and name the records used.
- With none: mark the figure `guess`.
- A cost is reported for ordering. It is never given to a writer as a target or a cap; a number handed over as a limit becomes what the work is sized to.

## Work items

One work item per feature and per split-out question, in the project's tracker or the place the caller names. Each carries its row from the map. Notes on existing work items are append-only.

## `close_by`

Each entry in `<model>/known-gap.json` gets `close_by`: the id of the feature expected to close it, or `not planned: <reason>`. Change nothing else in the model folder.
