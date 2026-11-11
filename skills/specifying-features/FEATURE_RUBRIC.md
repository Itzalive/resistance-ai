# Feature design rubric

Grade every item. Each item is binary. Items tagged `[whole]` are graded on the whole design in every run; the rest are graded on the run's scope, as `FEATURE_REVIEW_MANIFEST.md` describes. An item that fails names the question, AC, shard or delta item and the correction.

## What review checks

- [ ] Every question the map gives the feature is answered with evidence, in the design.
- [ ] Every epic AC the map gives the feature is served by an `AC-F`, and every `AC-F` traces to an epic AC. [whole]
- [ ] The `check` output is quoted, and was run with the feature's elements as its scope and with the shards file; or the section records `no model` with a waiver reference. [whole]
- [ ] The quoted output shows no new breach and no stale entry in scope. [whole]
- [ ] Every known breach in scope, every shared hot spot and every eval copy is a shard 0 refactor or is left alone with a reason.
- [ ] Every `AC-F` is in exactly one shard. [whole]
- [ ] No shard mixes a refactor with a behaviour change.
- [ ] Where three or more implementations of one rule would each be changed, a consolidation shard comes first.
- [ ] Every `AC-F` has a probe, and one eval run is named.
- [ ] The cost names its run records or is marked `guess`.

## Hard rules

- [ ] No shard spec exists for the feature. [whole]
- [ ] The epic, the model, the code and other features' rows are unchanged. [whole]
- [ ] No cost is stated as a target or a cap.
- [ ] The decision log only grew. [whole]
