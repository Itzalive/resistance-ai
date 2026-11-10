# Feature plan review manifest

Used by the self-review and by the independent auditor. Gather the inputs, work out the scope, then grade every item in `FEATURES_RUBRIC.md`.

## Inputs

- The feature map.
- The approved epic: its capabilities, ACs, success metrics, MVP criteria and MoSCoW.
- The model folder's `architecture.md` (rule map, cross-cutting decisions) and `known-gap.json`.
- The run's diff: `git diff` of the map and of `known-gap.json`, and `git status` for anything else changed.
- The run records, when the map's costs name any.

## Scope

- **Planning run:** the whole map.
- **Re-plan run:** the changed features and questions, plus the items marked `[whole]` in the rubric.

## Checks to run

- **AC coverage:** list every epic AC and find it on the map. Each appears under exactly one feature, or is marked cross-cutting.
- **`close_by`:** every entry in `known-gap.json` has it, and each feature id it names is on the map.
- **Unchanged:** the diff touches only the map and the `close_by` values. No other key of a gap entry, no `.c4` file, no part of `architecture.md`, no epic text and no code changed.
- **Costs:** each cost names run records that exist, or is marked `guess`.

## Grading

Grade against every `FEATURES_RUBRIC.md` checkbox. Report:
- each failed item, with the feature, question or gap entry it names and the exact correction;
- the verdict: `[FEATURES-REVIEW-PASSED]` only when every item passes, otherwise `[FEATURES-REVIEW-FAILED]`.
