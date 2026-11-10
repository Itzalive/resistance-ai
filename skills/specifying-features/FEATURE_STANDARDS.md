# Feature design standards

Load this file at step 1.

## The feature design

One file per feature, beside the feature map: `docs/features/<epic>/<id>-<slug>.md`. Sections, in this order:

1. **Questions answered:** each question, its answer and its evidence.
2. **Behaviour:** by section.
3. **Feature ACs:** `AC-F1`, `AC-F2`, …, each with the epic ACs it serves.
4. **Architecture delta:** the feature's elements, the quoted `check` output, and the decision on each item.
5. **Shard map:** the shards, the feature ACs each owns, the order and why.
6. **Eval plan:** the probes per feature AC, and the one eval run.
7. **Costing:** the counts and the estimate.
8. **Decision log:** one dated entry per run or reshard. It only grows.
9. **Close record:** written by the close run.

## Answering questions

- Evidence is a measurement, a reading of the code, or a short spike inside this feature. An answer with none is still open.
- Look for behaviour questions the map does not list: read the feature's epic ACs and rules against the code as built, and note every place the behaviour is undecided.
- Present the answers in tiers. Questions that block the design, and any default a user would notice, are decisions for the owner. The rest are listed once as defaults applied unless the owner objects.
- Every answer is written in the design. An answer settled only in conversation is lost to the shards.
- An answer that changes another feature or the epic is not applied here. Stop, and hand it to a `planning-features` re-plan.

## The feature's elements

The scope of the delta is these model elements:
- the elements that own, in the model's rule map, the rules behind the feature's epic ACs;
- the elements bound by the cross-cutting decisions the feature builds on;
- every element a proposed shard touches.

## The shards file

Kept beside the design:

```json
{"shards": {"<shard name>": ["<element id>", "..."]}}
```

Every id must be a model element; the tool exits 2 otherwise.

## Running the delta

Run the overlay's `deps-command`, then:

```bash
node <skills-dir>/shared/scripts/architecture-delta.mjs check --repo . --model <model> --deps <deps-file> --separator <separator> --scope <element,element,...> --shards <shards file>
```

Quote the whole text output in the design, with the exit code.

| Result | What to do |
|---|---|
| Exit 2 | Stop the run with the tool's error |
| A new breach in scope | Stop. Write a diff request and hand to `defining-architecture`; resume after `[ARCH-APPROVED]` |
| A stale gap entry in scope | The same |
| Known breaches | Decide each one, below |
| Shared hot spots | Decide each one, below |
| Not yet reached | Note which shard is expected to build the relationship |

## Eval copies

The tool does not report these. For each element tagged `#eval` in scope, read its code: does it call the production element for what it evaluates, or does it hold its own copy (its own builder, parser or prompt)? Record each copy, and say in the design that this is a reading, not tool output.

## Deciding each item

Every known breach in scope, every shared hot spot and every eval copy gets one of two outcomes:

- **Shard 0 refactor:** a behaviour-free shard that comes before the behaviour shards that need it. Cut it to what this feature's shards change (a shared reader, writer or type they would otherwise each restate).
- **Left alone, with the reason.** A tidy-up that only makes code easier to read, or a seam the feature's shards do not touch, is left alone until a feature needs it.

A hot spot means two or more shards change the same element. Either one shard 0 gives them a single place to change, or the shards are ordered so each builds on the last, and the reason says which.

## Shard-map rules

- Every `AC-F` is in exactly one shard.
- A refactor shard changes no behaviour. A behaviour shard carries no refactor.
- The order is given with its reason: what each shard needs from the ones before it.
- Shards are specified just in time, one at a time, by `specifying-work-items`. This skill writes no shard spec.

## Costing

- **Entry paths per shard:** the distinct ways into the code the shard changes.
- **Implementations per rule:** the places that implement each rule the feature changes. When three or more implementations of one rule would each be changed, a consolidation shard comes first, and the behaviour shards change the one place it leaves.
- **Estimate:** fit a fixed cost per plan and a cost per task from the project's `.run_records.jsonl`, apply it to the shard map, and name the records used. With no records, mark the figure `guess`.
- The estimate is reported. It is never given to a writer as a target or a cap.

## One-feature epic

For an epic that skipped `planning-features`:
- the feature's ACs and questions come from the epic;
- there is no map, so nothing is written to one;
- the close run ends with a note on the epic's work item and hands to no re-plan.

Where the architecture was also waived and the model folder is empty:
- `deps-command` is not required at step 1, and `check` is not run;
- the Architecture delta section records `no model` with the waiver's reference;
- entry paths and implementations per rule are still counted by reading the code, and shard 0 is decided from that count;
- the close run runs no `check` and removes no entries; its Close record holds the actual cost only.

This is the only case where the delta section holds no tool output.
