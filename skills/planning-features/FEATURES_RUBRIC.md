# Feature plan rubric

Grade every item. Each item is binary. Items tagged `[whole]` are graded on the whole map in every run; the rest are graded on the run's scope, as `FEATURES_REVIEW_MANIFEST.md` describes. An item that fails names the feature, question or gap entry and the correction.

## What review checks

- [ ] Every epic AC is in exactly one feature, or marked cross-cutting. [whole]
- [ ] Every feature has a goal, the success metric or MVP criterion it moves, at least one epic AC, an eval run, and a cost that names its run records or is marked `guess`.
- [ ] No feature's stated reason is that its parts share code.
- [ ] Every question has its risk (what changes at each answer) and the feature that answers it.
- [ ] Every split-out question names its kind, the decision it feeds and the features it could change, and is placed before each of those features.
- [ ] The first feature to build on each cross-cutting decision is marked as its foundation. [whole]
- [ ] Every known-gap entry has `close_by`. [whole]
- [ ] The entry-path and implementations-per-rule counts are present for every feature.
- [ ] Order reasoning is given for each of the five ordering rules.

## Hard rules

- [ ] The epic, the model (apart from `close_by`) and the code are unchanged. [whole]
- [ ] No shipped feature was reordered or rewritten. [whole]
- [ ] The re-plan log only grew. [whole]
- [ ] No cost is stated as a target or a cap.
