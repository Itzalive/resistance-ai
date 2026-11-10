# Feature design review manifest

Used by the self-review and by the independent auditor. Gather the inputs, work out the scope, then grade every item in `FEATURE_RUBRIC.md`.

## Inputs

- The feature design and its shards file.
- The feature's row and questions from the feature map (for a one-feature epic, the epic).
- The approved epic's ACs and rules that the feature serves.
- The model folder's `architecture.md` (rule map, cross-cutting decisions) and `known-gap.json`.
- A `check` run now, with the feature's elements as `--scope` and the shards file as `--shards` (not for a one-feature epic with a waived, empty model; confirm the waiver reference instead).
- The run's diff: `git diff` of the design and the map, and `git status` for anything else changed.
- The run records, when the costing names any.

## Scope

- **Design run:** the whole design.
- **Reshard:** the changed shards and the feature ACs they own, plus the items marked `[whole]` in the rubric.

## Checks to run

- **The feature's elements:** work them out as `FEATURE_STANDARDS.md` defines them, and confirm the design's `--scope` lists them all.
- **Quoted output:** the `check` output quoted in the design matches the run you make now. If they differ, the design is stale. Skipped where the section records `no model`.
- **AC tracing:** list every epic AC the map gives the feature and find an `AC-F` that serves it. List every `AC-F` and find its shard; each is in exactly one.
- **Unchanged:** the diff touches only the design, the shards file, and this feature's state, actual cost and question answers on the map. No shard spec exists for the feature; no model file, epic text, code or other feature's row changed.

## Grading

Grade against every `FEATURE_RUBRIC.md` checkbox. Report:
- each failed item, with the question, AC, shard or delta item it names and the exact correction;
- the verdict: `[FEATURE-REVIEW-PASSED]` only when every item passes, otherwise `[FEATURE-REVIEW-FAILED]`.
